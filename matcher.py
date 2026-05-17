import database
from typing import List, Dict, Tuple, Optional
from config import VIBE_CONFLICT_PAIRS, VIBE_CONFLICT_PENALTY
from utils import score_label


class MatcherService:
    """
    Multi-factor compatibility scoring engine.
    Scores are normalised to a 0–100 scale using a calibrated ceiling.

    Factor ceilings (THEORETICAL_MAX = 350, intentionally inflated so top
    real-world matches land in the 70-100 % band):

      Subjects:           min(n,3)*20  =  60
      Schedule:           min(n,5)*5   =  25
      Study Style:        min(n,4)*8   =  32
      Goals:              min(n,4)*6   =  24
      Complementary skill:min(n,3)*15  =  45  ┐ mutually exclusive per subject
      Advanced peer:      min(n,3)*10  =  30  ┘
      Same-level bonus:   min(n,3)*5   =  15  (fires when neither above applies)
      Same course:        15
      Same university:    10
      Same campus:        10
      Same zone:           8
      Environment:        min(n,3)*6   =  18
      Vibe:               min(n,3)*6   =  18
      Vibe conflict:      -8 per pair (penalty)
      Bachelor–Master:    20
      Project boost:      10
      Co-working:         15  (only fires when both have subjects but none overlap)
    """

    WEIGHT_SHARED_SUBJECT      = 20
    WEIGHT_OVERLAPPING_TIME    = 5
    WEIGHT_STUDY_STYLE         = 8
    WEIGHT_SHARED_GOAL         = 6
    WEIGHT_COMPLEMENTARY_SKILL = 15
    WEIGHT_ADVANCED_PEER       = 10
    WEIGHT_SAME_SKILL_LEVEL    = 5   # both within 1 skill level, not already scored

    WEIGHT_SAME_COURSE         = 15
    WEIGHT_SAME_UNIVERSITY     = 10
    WEIGHT_SAME_CAMPUS         = 10
    WEIGHT_SAME_ZONE           = 8
    WEIGHT_ENVIRONMENT         = 6
    WEIGHT_VIBE                = 6
    WEIGHT_BACHELOR_MASTER     = 20
    WEIGHT_PROJECT_BASED       = 10

    THEORETICAL_MAX = 350

    # ── Core scoring ──────────────────────────────────────────────────────────

    @classmethod
    def calculate_compatibility(
        cls,
        user1: dict,
        user2: dict,
        avail1: set,
        avail2: set,
    ) -> Tuple[int, List[str], Dict[str, int]]:
        """
        Returns (normalised_score 0-100, human_readable_details, score_breakdown).
        score_breakdown maps category → raw points (may include negatives for conflicts).
        """
        raw = 0
        details: List[str] = []
        breakdown: Dict[str, int] = {}

        def add(category: str, points: int, detail: Optional[str] = None):
            nonlocal raw
            raw += points
            breakdown[category] = breakdown.get(category, 0) + points
            if detail:
                details.append(detail)

        # 1. Shared subjects (cap at 3)
        s1 = set(user1.get('subjects', []))
        s2 = set(user2.get('subjects', []))
        shared_subjects = s1.intersection(s2)
        if shared_subjects:
            pts = min(len(shared_subjects), 3) * cls.WEIGHT_SHARED_SUBJECT
            add("Subjects", pts, f"Shared subjects: {', '.join(sorted(shared_subjects))}")

        # 2. Overlapping availability (cap at 5 slots)
        shared_slots = avail1.intersection(avail2)
        if shared_slots:
            pts = min(len(shared_slots), 5) * cls.WEIGHT_OVERLAPPING_TIME
            add("Schedule", pts, f"{len(shared_slots)} overlapping availability slot(s)")

        # 3. Study styles (cap at 4)
        styles1 = set(user1.get('study_styles', []))
        styles2 = set(user2.get('study_styles', []))
        shared_styles = styles1.intersection(styles2)
        if shared_styles:
            pts = min(len(shared_styles), 4) * cls.WEIGHT_STUDY_STYLE
            add("Study Style", pts, f"Shared study styles: {', '.join(sorted(shared_styles))}")

        # 4. Shared goals (cap at 4)
        goals1 = set(user1.get('goals', []))
        goals2 = set(user2.get('goals', []))
        shared_goals = goals1.intersection(goals2)
        if shared_goals:
            pts = min(len(shared_goals), 4) * cls.WEIGHT_SHARED_GOAL
            add("Goals", pts, f"Shared goals: {', '.join(sorted(shared_goals))}")

        # 5. Skill scoring per shared subject (cap at 3 subjects each path)
        skills1 = user1.get('skill_levels', {})
        skills2 = user2.get('skill_levels', {})
        comp_count = adv_count = same_count = 0
        for subj in shared_subjects:
            sk1 = skills1.get(subj, 3)
            sk2 = skills2.get(subj, 3)
            if (sk1 >= 4 and sk2 <= 2) or (sk1 <= 2 and sk2 >= 4):
                comp_count += 1
            elif sk1 >= 4 and sk2 >= 4:
                adv_count += 1
            elif abs(sk1 - sk2) <= 1:
                # Same-level peers — studying together at equal footing
                same_count += 1

        if comp_count:
            pts = min(comp_count, 3) * cls.WEIGHT_COMPLEMENTARY_SKILL
            add("Skill Match", pts, f"Mentorship potential in {comp_count} subject(s)")
        if adv_count:
            pts = min(adv_count, 3) * cls.WEIGHT_ADVANCED_PEER
            add("Skill Match", pts, f"Advanced peer study in {adv_count} subject(s)")
        if same_count:
            pts = min(same_count, 3) * cls.WEIGHT_SAME_SKILL_LEVEL
            add("Skill Match", pts, f"Same-level peers in {same_count} subject(s)")

        # 6. Course match (case-insensitive)
        c1 = (user1.get('course') or '').strip().lower()
        c2 = (user2.get('course') or '').strip().lower()
        if c1 and c2 and c1 == c2:
            add("Location & Context", cls.WEIGHT_SAME_COURSE, f"Same course: {user1['course']}")

        # 7. University & Campus
        u1 = (user1.get('university') or '').strip().lower()
        u2 = (user2.get('university') or '').strip().lower()
        if u1 and u2 and u1 == u2:
            add("Location & Context", cls.WEIGHT_SAME_UNIVERSITY, f"Same university: {user1['university']}")
            cam1 = (user1.get('campus') or '').strip().lower()
            cam2 = (user2.get('campus') or '').strip().lower()
            if cam1 and cam2 and cam1 == cam2:
                add("Location & Context", cls.WEIGHT_SAME_CAMPUS, f"Same campus: {user1['campus']}")

        # 8. Location zone
        z1 = (user1.get('location_zone') or '').strip().lower()
        z2 = (user2.get('location_zone') or '').strip().lower()
        if z1 and z2 and z1 == z2:
            add("Location & Context", cls.WEIGHT_SAME_ZONE, f"Same neighbourhood: {user1['location_zone']}")

        # 9. Study environment (cap at 3)
        env1 = set(user1.get('study_environment', []))
        env2 = set(user2.get('study_environment', []))
        shared_env = env1.intersection(env2)
        if shared_env:
            pts = min(len(shared_env), 3) * cls.WEIGHT_ENVIRONMENT
            add("Vibe & Environment", pts, f"Shared environment: {', '.join(sorted(shared_env))}")

        # 10. Vibe match (cap at 3) + conflict penalties
        vibe1 = set(user1.get('study_vibe', []))
        vibe2 = set(user2.get('study_vibe', []))
        shared_vibe = vibe1.intersection(vibe2)
        if shared_vibe:
            pts = min(len(shared_vibe), 3) * cls.WEIGHT_VIBE
            add("Vibe & Environment", pts, f"Shared vibe: {', '.join(sorted(shared_vibe))}")

        for set_a, set_b in VIBE_CONFLICT_PAIRS:
            if (vibe1 & set_a and vibe2 & set_b) or (vibe1 & set_b and vibe2 & set_a):
                add("Vibe & Environment", -VIBE_CONFLICT_PENALTY, "⚠️ Conflicting study vibes")

        # 11. Bachelor–Master mentorship bridge
        deg1 = user1.get('degree_level')
        deg2 = user2.get('degree_level')
        if deg1 and deg2 and {deg1, deg2} == {"Bachelor", "Master"}:
            if shared_goals.intersection({"Application Preparation", "Exam Prep", "Research"}):
                add("Degree Level", cls.WEIGHT_BACHELOR_MASTER, "Bachelor–Master mentorship connection")
            else:
                add("Degree Level", cls.WEIGHT_BACHELOR_MASTER // 2, "Bachelor–Master cross-level connection")

        # 12. Project-based boost
        if "Project Work" in shared_goals or "Project Collaboration" in shared_goals:
            add("Goals", cls.WEIGHT_PROJECT_BASED, "Project collaboration alignment")

        # 13. General co-working bonus (both have subjects but none overlap; not sparse profiles)
        if not shared_subjects and s1 and s2 and shared_slots and len(shared_goals) >= 2:
            add("Schedule", 15, "Good for general co-working sessions")

        score = max(0, min(int((raw / cls.THEORETICAL_MAX) * 100), 100))
        return score, details, breakdown

    # ── Match retrieval ───────────────────────────────────────────────────────

    @classmethod
    def get_top_matches(
        cls,
        user_id: int,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> List[dict]:
        """
        Return all users with score > 0, sorted descending.
        Each result: {'user', 'score', 'raw_score', 'delta', 'details', 'breakdown'}.
        When custom_weights are active, 'score' is the adjusted value and 'delta'
        shows the change from the default score.
        """
        import streamlit as st
        cache_key = f"matches_{user_id}"
        if custom_weights is None and cache_key in st.session_state:
            return st.session_state[cache_key]

        current_user = database.get_user_by_id(user_id)
        if not current_user:
            return []

        all_users = database.get_all_users()
        all_availability = database.get_all_availability()
        current_avail = set(all_availability.get(user_id, []))

        results = []
        for other in all_users:
            if other['id'] == user_id:
                continue
            other_avail = set(all_availability.get(other['id'], []))
            base_score, details, breakdown = cls.calculate_compatibility(
                current_user, other, current_avail, other_avail,
            )

            if custom_weights:
                raw_adjusted = sum(
                    pts * custom_weights.get(cat, 1.0)
                    for cat, pts in breakdown.items()
                )
                adjusted_score = max(0, min(int((raw_adjusted / cls.THEORETICAL_MAX) * 100), 100))
            else:
                adjusted_score = base_score

            if adjusted_score > 0 or base_score > 0:
                results.append({
                    'user': other,
                    'score': adjusted_score,
                    'raw_score': base_score,
                    'delta': adjusted_score - base_score if custom_weights else 0,
                    'details': details,
                    'breakdown': breakdown,
                })

        results.sort(key=lambda x: x['score'], reverse=True)

        if custom_weights is None:
            st.session_state[cache_key] = results
        return results

    # ── Group fit & cohesion ──────────────────────────────────────────────────

    @classmethod
    def calculate_group_fit(cls, user_id: int, group_id: int) -> Tuple[int, int]:
        """
        Score a candidate against every current group member.
        Returns (avg_score, min_score). Both 0 if group is empty.
        """
        current_user = database.get_user_by_id(user_id)
        if not current_user:
            return 0, 0
        group = next((g for g in database.get_all_groups() if g['id'] == group_id), None)
        if not group or not group['members']:
            return 0, 0

        all_availability = database.get_all_availability()
        current_avail = set(all_availability.get(user_id, []))
        scores = []
        for member_id in group['members']:
            if member_id == user_id:
                continue
            member = database.get_user_by_id(member_id)
            if not member:
                continue
            s, _, _ = cls.calculate_compatibility(
                current_user, member,
                current_avail, set(all_availability.get(member_id, [])),
            )
            scores.append(s)
        if not scores:
            return 0, 0
        return int(sum(scores) / len(scores)), min(scores)

    @classmethod
    def calculate_group_cohesion(cls, group_id: int) -> Dict[str, any]:
        """
        Pairwise compatibility for all group members.
        Returns {'matrix': [[score,...], ...], 'names': [...], 'avg': int}.
        """
        group = next((g for g in database.get_all_groups() if g['id'] == group_id), None)
        if not group or len(group['members']) < 2:
            return {'matrix': [], 'names': [], 'avg': 0}

        all_availability = database.get_all_availability()
        members = [m for m in (database.get_user_by_id(mid) for mid in group['members']) if m]
        names = [m.get('name') or m['username'] for m in members]
        n = len(members)
        matrix = [[0] * n for _ in range(n)]
        scores = []

        for i in range(n):
            matrix[i][i] = 100
            for j in range(i + 1, n):
                avail_i = set(all_availability.get(members[i]['id'], []))
                avail_j = set(all_availability.get(members[j]['id'], []))
                s, _, _ = cls.calculate_compatibility(members[i], members[j], avail_i, avail_j)
                matrix[i][j] = matrix[j][i] = s
                scores.append(s)

        avg = int(sum(scores) / len(scores)) if scores else 0
        return {'matrix': matrix, 'names': names, 'avg': avg}

    # ── Session planner ───────────────────────────────────────────────────────

    @classmethod
    def suggest_meeting_slots(cls, group_id: int) -> List[Tuple[str, str, int]]:
        """Return top-3 (day, timeslot, member_count) tuples by coverage."""
        group = next((g for g in database.get_all_groups() if g['id'] == group_id), None)
        if not group or not group['members']:
            return []
        all_availability = database.get_all_availability()
        slot_counts: Dict[Tuple[str, str], int] = {}
        for member_id in group['members']:
            for slot in all_availability.get(member_id, []):
                slot_counts[slot] = slot_counts.get(slot, 0) + 1
        ranked = sorted(slot_counts.items(), key=lambda x: x[1], reverse=True)
        return [(day, ts, count) for (day, ts), count in ranked[:3]]

    # ── Outstanding Feature 2: Smart Group Formation ──────────────────────────

    @classmethod
    def suggest_optimal_group(
        cls,
        user_id: int,
        group_size: int = 3,
    ) -> Tuple[List[dict], int]:
        """
        Greedy algorithm that builds the highest-cohesion group of `group_size`
        members (including the current user).

        Returns (suggested_members_excluding_self, predicted_cohesion_pct).
        The greedy heuristic: at each step, add the candidate that maximises the
        average pairwise score across the growing group.
        """
        current_user = database.get_user_by_id(user_id)
        if not current_user:
            return [], 0

        top_matches = cls.get_top_matches(user_id)
        if not top_matches:
            return [], 0

        # Work with the top 15 candidates to bound complexity
        candidates = [m['user'] for m in top_matches[:15]]
        all_avail = database.get_all_availability()

        group = [current_user]

        for _ in range(group_size - 1):
            best_candidate = None
            best_avg: float = -1.0

            for candidate in candidates:
                if any(c['id'] == candidate['id'] for c in group):
                    continue
                temp = group + [candidate]
                pair_scores = []
                for i, m1 in enumerate(temp):
                    for m2 in temp[i + 1:]:
                        s, _, _ = cls.calculate_compatibility(
                            m1, m2,
                            set(all_avail.get(m1['id'], [])),
                            set(all_avail.get(m2['id'], [])),
                        )
                        pair_scores.append(s)
                avg = sum(pair_scores) / len(pair_scores) if pair_scores else 0
                if avg > best_avg:
                    best_avg = avg
                    best_candidate = candidate

            if best_candidate is None:
                break
            group.append(best_candidate)
            candidates = [c for c in candidates if c['id'] != best_candidate['id']]

        # Final cohesion over the complete proposed group
        final_scores = []
        for i, m1 in enumerate(group):
            for m2 in group[i + 1:]:
                s, _, _ = cls.calculate_compatibility(
                    m1, m2,
                    set(all_avail.get(m1['id'], [])),
                    set(all_avail.get(m2['id'], [])),
                )
                final_scores.append(s)
        cohesion = int(sum(final_scores) / len(final_scores)) if final_scores else 0

        return group[1:], cohesion  # exclude current user; they already know themselves

    # ── Outstanding Feature 1: Natural Language Match Story ──────────────────

    @classmethod
    def generate_match_story(
        cls,
        user1: dict,
        user2: dict,
        score: int,
        breakdown: Dict[str, int],
        shared_subjects: List[str],
        shared_slots: int,
    ) -> str:
        """
        Generate a 2-sentence human-readable compatibility narrative.
        No LLM required — purely rule-based template logic.
        """
        name2 = user2.get('name') or user2['username']
        lbl = score_label(score).lower()

        # Sentence 1 — lead with the dominant scoring dimension
        if breakdown:
            # Filter out negative-pointing categories for the lead
            positive = {k: v for k, v in breakdown.items() if v > 0}
            top_cat = max(positive.items(), key=lambda x: x[1])[0] if positive else ""
        else:
            top_cat = ""

        if top_cat == "Subjects" and shared_subjects:
            subj_str = " and ".join(shared_subjects[:2])
            sent1 = (
                f"You and **{name2}** are a {lbl} match ({score}%), "
                f"with your strongest connection in {subj_str}."
            )
        elif top_cat == "Schedule":
            sent1 = (
                f"You and **{name2}** are a {lbl} match ({score}%), "
                f"driven primarily by strong schedule compatibility."
            )
        elif top_cat == "Skill Match":
            sent1 = (
                f"You and **{name2}** are a {lbl} match ({score}%), "
                f"with meaningful skill synergy across your shared subjects."
            )
        elif top_cat == "Location & Context":
            sent1 = (
                f"You and **{name2}** are a {lbl} match ({score}%), "
                f"amplified by being in the same academic context."
            )
        else:
            sent1 = f"You and **{name2}** are a {lbl} match ({score}%)."

        # Sentence 2 — actionable detail
        parts: List[str] = []
        if shared_slots:
            parts.append(f"you share **{shared_slots} free time slot{'s' if shared_slots != 1 else ''}**")

        sk1 = user1.get('skill_levels', {})
        sk2 = user2.get('skill_levels', {})
        for subj in shared_subjects[:2]:
            l1, l2 = sk1.get(subj, 3), sk2.get(subj, 3)
            if l2 >= 4 and l1 <= 2:
                parts.append(f"{name2} can mentor you in **{subj}**")
                break
            elif l1 >= 4 and l2 <= 2:
                parts.append(f"you can mentor {name2} in **{subj}**")
                break

        shared_env = set(user1.get('study_environment', [])) & set(user2.get('study_environment', []))
        if shared_env:
            parts.append(f"you both prefer **{next(iter(shared_env))}** sessions")

        if parts:
            sent2 = "Together, " + ", ".join(parts[:2]) + "."
        else:
            sent2 = "Complete more profile fields to reveal deeper compatibility factors."

        return f"{sent1} {sent2}"

    # ── Improvement hints for low-scoring matches ─────────────────────────────

    @classmethod
    def get_improvement_hints(
        cls,
        user1: dict,
        avail1: set,
        avail2: set,
        score: int,
    ) -> List[str]:
        """Return up to 2 actionable hints to improve this match score."""
        if score >= 50:
            return []
        hints: List[str] = []
        if not avail1:
            hints.append("📅 Set your availability to unlock schedule compatibility")
        elif not (avail1 & avail2):
            hints.append("📅 Your schedules don't overlap — update your availability")
        if not user1.get('goals'):
            hints.append("🎯 Add study goals to find better-aligned peers")
        if not user1.get('study_environment'):
            hints.append("🏛️ Set preferred environment to discover shared preferences")
        if not user1.get('study_vibe'):
            hints.append("🎵 Add a study vibe to improve atmosphere matching")
        return hints[:2]


# Backwards-compatibility alias
get_top_matches = MatcherService.get_top_matches
