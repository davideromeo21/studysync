import database
from typing import List, Dict, Tuple, Optional


class MatcherService:
    """
    Multi-factor compatibility scoring engine.
    Scores are normalized to a 0–100 scale.

    Theoretical max derivation (all caps are applied):
      Subjects:        min(n,3)*20  = 60
      Time slots:      min(n,5)*5   = 25
      Study styles:    min(n,4)*8   = 32   (cap 4 styles)
      Goals:           min(n,4)*6   = 24   (cap 4 goals)
      Comp. skill:     min(n,3)*15  = 45   (cap 3 subjects)
      Advanced peer:   min(n,3)*10  = 30   (cap 3 subjects)
      Same course:     15
      Same university: 10
      Same campus:     10
      Same zone:       8
      Environment:     min(n,3)*6   = 18   (cap 3 environments)
      Vibe:            min(n,3)*6   = 18   (cap 3 vibes)
      Bach-Master:     20
      Project based:   10
      Co-working:      25
      TOTAL MAX:       350  → use as divisor so top matches land in 70-100% band
    """

    # ── Scoring weights ──────────────────────────────────────────────────────
    WEIGHT_SHARED_SUBJECT      = 20   # per shared subject (capped at 3)
    WEIGHT_OVERLAPPING_TIME    = 5    # per shared time slot (capped at 5 slots)
    WEIGHT_STUDY_STYLE         = 8    # per shared style (capped at 4)
    WEIGHT_SHARED_GOAL         = 6    # per shared goal (capped at 4)
    WEIGHT_COMPLEMENTARY_SKILL = 15   # mentorship pair in shared subject (capped at 3)
    WEIGHT_ADVANCED_PEER       = 10   # both high-skill in shared subject (capped at 3)

    WEIGHT_SAME_COURSE         = 15
    WEIGHT_SAME_UNIVERSITY     = 10
    WEIGHT_SAME_CAMPUS         = 10
    WEIGHT_SAME_ZONE           = 8
    WEIGHT_ENVIRONMENT         = 6    # per shared environment (capped at 3)
    WEIGHT_VIBE                = 6    # per shared vibe (capped at 3)
    WEIGHT_BACHELOR_MASTER     = 20
    WEIGHT_PROJECT_BASED       = 10

    # Calibrated maximum: sum of all capped factor ceilings (see docstring)
    THEORETICAL_MAX = 350

    @classmethod
    def calculate_compatibility(
        cls,
        user1: dict,
        user2: dict,
        avail1: set,
        avail2: set,
    ) -> Tuple[int, List[str], Dict[str, int]]:
        """
        Returns (normalized_score 0-100, human_readable_details, score_breakdown).
        score_breakdown maps category → raw points contributed.
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

        # 5. Skill complementarity per shared subject (cap at 3 subjects each)
        skills1 = user1.get('skill_levels', {})
        skills2 = user2.get('skill_levels', {})
        comp_count = adv_count = 0
        for subj in shared_subjects:
            sk1 = skills1.get(subj, 3)
            sk2 = skills2.get(subj, 3)
            if (sk1 >= 4 and sk2 <= 2) or (sk1 <= 2 and sk2 >= 4):
                comp_count += 1
            elif sk1 >= 4 and sk2 >= 4:
                adv_count += 1
        if comp_count:
            pts = min(comp_count, 3) * cls.WEIGHT_COMPLEMENTARY_SKILL
            add("Skill Match", pts, f"Mentorship potential in {comp_count} subject(s)")
        if adv_count:
            pts = min(adv_count, 3) * cls.WEIGHT_ADVANCED_PEER
            add("Skill Match", pts, f"Advanced peer study in {adv_count} subject(s)")

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

        # 9. Study environment & vibe (cap at 3 each)
        env1 = set(user1.get('study_environment', []))
        env2 = set(user2.get('study_environment', []))
        shared_env = env1.intersection(env2)
        if shared_env:
            pts = min(len(shared_env), 3) * cls.WEIGHT_ENVIRONMENT
            add("Vibe & Environment", pts, f"Shared environment: {', '.join(sorted(shared_env))}")

        vibe1 = set(user1.get('study_vibe', []))
        vibe2 = set(user2.get('study_vibe', []))
        shared_vibe = vibe1.intersection(vibe2)
        if shared_vibe:
            pts = min(len(shared_vibe), 3) * cls.WEIGHT_VIBE
            add("Vibe & Environment", pts, f"Shared vibe: {', '.join(sorted(shared_vibe))}")

        # 10. Bachelor–Master mentorship bridge
        deg1 = user1.get('degree_level')
        deg2 = user2.get('degree_level')
        if deg1 and deg2 and {deg1, deg2} == {"Bachelor", "Master"}:
            if shared_goals.intersection({"Application Preparation", "Exam Prep", "Research"}):
                add("Degree Level", cls.WEIGHT_BACHELOR_MASTER, "Bachelor–Master mentorship connection")
            else:
                add("Degree Level", cls.WEIGHT_BACHELOR_MASTER // 2, "Bachelor–Master cross-level connection")

        # 11. Project-based boost
        if "Project Work" in shared_goals or "Project Collaboration" in shared_goals:
            add("Goals", cls.WEIGHT_PROJECT_BASED, "Project collaboration alignment")

        # 12. General co-working bonus (no shared subjects but overlapping time + goals)
        if not shared_subjects and shared_slots and len(shared_goals) >= 2:
            add("Schedule", 25, "Good for general co-working sessions")

        score = min(int((raw / cls.THEORETICAL_MAX) * 100), 100)
        return score, details, breakdown

    @classmethod
    def get_top_matches(cls, user_id: int, custom_weights: Optional[Dict[str, float]] = None) -> List[dict]:
        """
        Returns all users with score > 0, sorted descending by compatibility.
        Each result dict includes 'user', 'score', 'details', 'breakdown'.
        custom_weights: optional dict mapping category name → multiplier (1.0 = default).
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
            score, details, breakdown = cls.calculate_compatibility(current_user, other, current_avail, other_avail)

            if custom_weights:
                raw_adjusted = sum(
                    pts * custom_weights.get(cat, 1.0)
                    for cat, pts in breakdown.items()
                )
                score = min(int((raw_adjusted / cls.THEORETICAL_MAX) * 100), 100)

            if score > 0:
                results.append({'user': other, 'score': score, 'details': details, 'breakdown': breakdown})

        results.sort(key=lambda x: x['score'], reverse=True)

        if custom_weights is None:
            st.session_state[cache_key] = results
        return results

    @classmethod
    def calculate_group_fit(cls, user_id: int, group_id: int) -> Tuple[int, int]:
        """
        Scores the candidate user against every current group member.
        Returns (average_score, min_score). Both 0 if group has no members.
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
            member_avail = set(all_availability.get(member_id, []))
            score, _, _ = cls.calculate_compatibility(current_user, member, current_avail, member_avail)
            scores.append(score)

        if not scores:
            return 0, 0
        return int(sum(scores) / len(scores)), min(scores)

    @classmethod
    def calculate_group_cohesion(cls, group_id: int) -> Dict[str, any]:
        """
        Computes pairwise compatibility for all group members.
        Returns {'matrix': [[score,...], ...], 'names': [...], 'avg': float}.
        """
        group = next((g for g in database.get_all_groups() if g['id'] == group_id), None)
        if not group or len(group['members']) < 2:
            return {'matrix': [], 'names': [], 'avg': 0}

        all_availability = database.get_all_availability()
        members = [database.get_user_by_id(mid) for mid in group['members']]
        members = [m for m in members if m]

        names = [m.get('name') or m['username'] for m in members]
        n = len(members)
        matrix = [[0] * n for _ in range(n)]

        scores = []
        for i in range(n):
            matrix[i][i] = 100
            for j in range(i + 1, n):
                avail_i = set(all_availability.get(members[i]['id'], []))
                avail_j = set(all_availability.get(members[j]['id'], []))
                score, _, _ = cls.calculate_compatibility(members[i], members[j], avail_i, avail_j)
                matrix[i][j] = score
                matrix[j][i] = score
                scores.append(score)

        avg = int(sum(scores) / len(scores)) if scores else 0
        return {'matrix': matrix, 'names': names, 'avg': avg}

    @classmethod
    def suggest_meeting_slots(cls, group_id: int) -> List[Tuple[str, str, int]]:
        """
        Returns top-3 (day, timeslot, member_count) tuples where the most members are free.
        """
        group = next((g for g in database.get_all_groups() if g['id'] == group_id), None)
        if not group or not group['members']:
            return []

        all_availability = database.get_all_availability()
        slot_counts: Dict[Tuple[str, str], int] = {}
        total_members = len(group['members'])

        for member_id in group['members']:
            for slot in all_availability.get(member_id, []):
                slot_counts[slot] = slot_counts.get(slot, 0) + 1

        ranked = sorted(slot_counts.items(), key=lambda x: x[1], reverse=True)
        return [(day, ts, count) for (day, ts), count in ranked[:3]]


# Backwards-compatibility alias
get_top_matches = MatcherService.get_top_matches
