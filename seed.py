"""
seed.py — Populate the StudySync database with 100 realistic sample accounts.

Usage:
    python seed.py

All sample accounts share the password: StudySync123!
Sample admin login: demo_user / StudySync123!
"""

import random
import json
from datetime import datetime, timedelta
import database
from database import (
    SessionLocal, User, StudyGroup, WorkspaceTask,
    Availability, UserActivity, group_members, hash_password, Base, engine
)
from sqlalchemy import text

# ── Seed data pools ──────────────────────────────────────────────────────────

FIRST_NAMES = [
    "João", "Maria", "Pedro", "Ana", "Sofia", "Miguel", "Inês", "Diogo",
    "Beatriz", "Francisco", "Carolina", "Rodrigo", "Mariana", "Tiago",
    "Catarina", "André", "Filipa", "Gonçalo", "Marta", "Vasco", "Sara",
    "Luís", "Rita", "Afonso", "Mafalda", "Nuno", "Rafael", "Gabriela",
    "Eduardo", "Constança", "Emma", "Liam", "Sophia", "Oliver", "Isabella",
    "Noah", "Charlotte", "James", "Mia", "William", "Lucas", "Alexander",
    "Amelia", "Max", "Elena", "Nicolas", "Anna", "Thomas", "Laura", "Daniel",
    "Clara", "Hugo", "Matilde", "Bernardo", "Alice", "Rui", "Mónica", "Duarte",
    "Leonor", "Tomás", "Francisca", "Guilherme", "Teresa", "Henrique", "Vera",
    "Felipe", "Camila", "Diego", "Valentina", "Mateus", "Juliana", "Leandro",
    "Isabela", "Gabriel", "Fernanda", "Victor", "Renata", "Marcos", "Priya",
    "Arjun", "Yuki", "Lena", "Finn", "Hana", "Matteo", "Giulia", "Leon",
    "Sophie", "Elias", "Nora", "Oscar", "Ida", "Kasper", "Astrid",
]

LAST_NAMES = [
    "Silva", "Santos", "Ferreira", "Pereira", "Costa", "Oliveira", "Rodrigues",
    "Martins", "Sousa", "Fernandes", "Gomes", "Lopes", "Marques", "Alves",
    "Carvalho", "Ribeiro", "Pinto", "Teixeira", "Cunha", "Moreira", "Nunes",
    "Barbosa", "Monteiro", "Correia", "Melo", "Cardoso", "Fonseca", "Ramos",
    "Azevedo", "Vieira", "Smith", "Johnson", "Brown", "Garcia", "Martinez",
    "Rossi", "Bianchi", "Müller", "Schmidt", "Andersen", "Johansson",
    "Tanaka", "Yamamoto", "Park", "Kim", "Chen", "Wang", "Patel",
]

COURSES = [
    "Management", "Finance", "Economics", "Marketing",
    "Accounting", "International Business", "Strategy & Consulting",
    "Data Science & Advanced Analytics", "Finance (Master)",
    "Management (Master)", "Economics (Master)", "Business Analytics",
]

DEGREES = ["Bachelor", "Master", "PhD"]
DEGREE_WEIGHTS = [0.55, 0.38, 0.07]

LOCATION_ZONES = [
    "Cascais", "Lisbon Centre", "Almada", "Setúbal", "Sintra",
    "Oeiras", "Amadora", "Loures", "Online / Remote",
]

SUBJECTS_POOL = [
    "Mathematics", "Statistics & Probability", "Economics", "Microeconomics",
    "Macroeconomics", "Finance", "Accounting", "Marketing", "Management",
    "Strategy", "Data Science", "Machine Learning", "Computer Science",
    "Linear Algebra", "Calculus", "Operations Research", "Psychology",
    "Sociology", "International Relations", "Law", "Philosophy",
]

GOALS_POOL = [
    "Exam Prep", "Homework Help", "Deep Understanding", "Project Collaboration",
    "Casual Study", "Project Work", "Thesis / Dissertation", "Research", "Networking",
]

STYLES_POOL = [
    "Quiet Revision", "Discussion-based", "Practice Questions",
    "Group Problem-solving", "Teaching / Explaining", "Note Sharing",
    "Mind Mapping", "Flashcards",
]

ENVIRONMENTS_POOL = [
    "Library", "Café", "Home", "Campus", "Online / Remote", "Co-working Space",
]

VIBES_POOL = [
    "Pomodoro", "Silent 3 Hours", "Chatty", "Lofi Music",
    "Intense Focus", "Breaks Every 45 min", "Snacks & Study",
]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIMESLOTS = ["Morning (8am-12pm)", "Afternoon (12pm-5pm)", "Evening (5pm-10pm)"]

GROUP_TEMPLATES = [
    ("Finance Study Hub", "Finance", "We crack case studies, past papers, and CFA prep together."),
    ("Stats & Prob Grind", "Statistics & Probability", "Weekly problem sets and exam walkthroughs."),
    ("ML & AI Explorers", "Machine Learning", "Hands-on projects, Kaggle competitions and paper reviews."),
    ("Econ Theory Circle", "Economics", "Macro & micro theory deep dives and essay prep."),
    ("Accounting Aces", "Accounting", "IFRS standards, ratio analysis and past exam practice."),
    ("Strategy Casebook", "Strategy", "BCG/McKinsey frameworks and consulting case practice."),
    ("Data Science Lab", "Data Science", "Python, pandas, and real-world data projects."),
    ("Marketing Collective", "Marketing", "Brand strategy, digital campaigns and group projects."),
    ("Math Foundations", "Mathematics", "Calculus, linear algebra and proof techniques."),
    ("Operations Research", "Operations Research", "LP, simulation and scheduling models."),
    ("Law & Regulation", "Law", "Case law analysis and regulatory frameworks."),
    ("Thesis Writers Club", "Research", "Peer feedback on methodology, literature and drafts."),
    ("Microecon Masters", "Microeconomics", "Game theory, market structures and problem sets."),
    ("Macro Deep Dive", "Macroeconomics", "Monetary policy, IS-LM and global economics."),
    ("CS & Algorithms", "Computer Science", "Leetcode, algorithms and software engineering."),
    ("International Biz", "International Relations", "Global markets, trade law and cross-cultural mgmt."),
    ("Philosophy & Ethics", "Philosophy", "Applied ethics in business and critical thinking."),
    ("Psychology of Orgs", "Psychology", "Behavioural economics and organisational psychology."),
    ("Startup Launchpad", "Management", "Business models, pitching and entrepreneurship."),
    ("CFA Prep Group", "Finance", "Level I & II exam prep with mock exams every weekend."),
]

TASK_TITLES = [
    "Review lecture slides from Week {}", "Complete problem set {}", "Read chapter {}",
    "Prepare case study presentation", "Mock exam — {} topics",
    "Group assignment draft v{}", "Literature review outline",
    "Research paper summary", "Past paper walkthrough",
    "Flashcard deck for {} exam", "Statistics homework due Friday",
    "Finance model template", "Data cleaning & EDA",
    "Create study notes", "Peer review each other's essays",
]

SAMPLE_PASSWORD = "StudySync123!"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_username(first: str, last: str, used: set) -> str:
    base = (first[0] + last).lower().replace(" ", "").replace("ã", "a").replace("ç", "c") \
        .replace("é", "e").replace("ó", "o").replace("í", "i").replace("ú", "u") \
        .replace("â", "a").replace("ê", "e").replace("ô", "o").replace("à", "a") \
        .replace("ì", "i").replace("ü", "u").replace("ö", "o").replace("ä", "a")
    base = ''.join(c for c in base if c.isalnum() or c == '_')[:20]
    candidate = base
    n = 2
    while candidate in used or len(candidate) < 3:
        candidate = f"{base}{n}"
        n += 1
    used.add(candidate)
    return candidate


def _random_availability() -> list[tuple[str, str]]:
    """Generate a realistic weekly availability pattern."""
    slots = []
    pattern = random.choice(["weekday_heavy", "evening_only", "mixed", "full"])
    for day in DAYS:
        is_weekday = day not in ("Saturday", "Sunday")
        for slot in TIMESLOTS:
            if pattern == "weekday_heavy" and is_weekday and random.random() < 0.55:
                slots.append((day, slot))
            elif pattern == "evening_only" and "Evening" in slot and random.random() < 0.7:
                slots.append((day, slot))
            elif pattern == "mixed" and random.random() < 0.35:
                slots.append((day, slot))
            elif pattern == "full" and random.random() < 0.65:
                slots.append((day, slot))
    return slots


def _subject_cluster() -> tuple[list[str], dict]:
    """Return a coherent subject cluster and skill levels."""
    clusters = [
        ["Finance", "Accounting", "Economics", "Macroeconomics", "Microeconomics"],
        ["Statistics & Probability", "Mathematics", "Data Science", "Machine Learning", "Linear Algebra"],
        ["Management", "Marketing", "Strategy", "International Relations", "Psychology"],
        ["Computer Science", "Machine Learning", "Data Science", "Mathematics", "Operations Research"],
        ["Economics", "Microeconomics", "Macroeconomics", "Statistics & Probability", "Operations Research"],
        ["Law", "Philosophy", "Sociology", "International Relations", "Psychology"],
    ]
    cluster = random.choice(clusters)
    n = random.randint(2, 5)
    subjects = random.sample(cluster, min(n, len(cluster)))
    skill_levels = {s: random.randint(1, 5) for s in subjects}
    return subjects, skill_levels


# ── Main seeding logic ───────────────────────────────────────────────────────

def seed():
    database.init_db()
    db = SessionLocal()

    existing_groups = db.query(StudyGroup).count()
    if existing_groups >= 10:
        print(f"Database already fully seeded ({existing_groups} groups exist) — skipping.")
        db.close()
        return

    # ── 1. Create users (skip if already present) ────────────────────────────
    existing_users = db.query(User).filter(User.name.isnot(None)).all()
    users_created: list[User] = list(existing_users)

    if len(users_created) < 50:
        print("Seeding 100 sample accounts...")
        pw_hash = hash_password(SAMPLE_PASSWORD)
        used_usernames: set[str] = set(u.username for u in db.query(User).all())

        names_pool = list(zip(
            random.sample(FIRST_NAMES, min(len(FIRST_NAMES), 100)),
            [random.choice(LAST_NAMES) for _ in range(100)],
        ))
        while len(names_pool) < 100:
            names_pool.append((random.choice(FIRST_NAMES), random.choice(LAST_NAMES)))

        needed = 100 - len(users_created)
        for first, last in names_pool[:needed]:
            username = _make_username(first, last, used_usernames)
            subjects, skill_levels = _subject_cluster()
            goals = random.sample(GOALS_POOL, random.randint(1, 3))
            styles = random.sample(STYLES_POOL, random.randint(1, 3))
            environments = random.sample(ENVIRONMENTS_POOL, random.randint(1, 3))
            vibes = random.sample(VIBES_POOL, random.randint(1, 2))
            degree = random.choices(DEGREES, weights=DEGREE_WEIGHTS)[0]
            course = random.choice(COURSES)
            if "Finance" in subjects or "Accounting" in subjects:
                course = random.choice(["Finance", "Finance (Master)", "Accounting"])
            elif "Machine Learning" in subjects or "Data Science" in subjects:
                course = random.choice(["Data Science & Advanced Analytics", "Business Analytics", "Computer Science"])
            elif "Management" in subjects or "Marketing" in subjects:
                course = random.choice(["Management", "Marketing", "International Business"])

            u = User(
                username=username,
                password_hash=pw_hash,
                name=f"{first} {last}",
                course=course,
                degree_level=degree,
                university="Nova SBE",
                campus="Carcavelos",
                location_zone=random.choice(LOCATION_ZONES),
            )
            u.subjects = subjects
            u.goals = goals
            u.skill_levels = skill_levels
            u.study_styles = styles
            u.study_environment = environments
            u.study_vibe = vibes
            u.created_at = datetime.utcnow() - timedelta(days=random.randint(1, 120))
            db.add(u)
            users_created.append(u)

        db.commit()
        print(f"  + Created {len(users_created)} users")
    else:
        print(f"  + Using {len(users_created)} existing users")

    # Refresh to get IDs
    for u in users_created:
        db.refresh(u)

    # ── 2. Availability ──────────────────────────────────────────────────────
    avail_rows = []
    for u in users_created:
        for day, slot in _random_availability():
            avail_rows.append(Availability(user_id=u.id, day=day, time_slot=slot))
    db.add_all(avail_rows)
    db.commit()
    print(f"  + Added {len(avail_rows)} availability slots")

    # ── 3. Study groups ──────────────────────────────────────────────────────
    groups_created: list[StudyGroup] = []
    random.shuffle(users_created)

    for i, (gname, gsubject, gdesc) in enumerate(GROUP_TEMPLATES):
        # Find users who study this subject (or nearby cluster)
        relevant = [u for u in users_created if gsubject in u.subjects]
        if len(relevant) < 2:
            relevant = users_created  # fallback
        size = random.randint(3, 8)
        members = random.sample(relevant, min(size, len(relevant)))

        g = StudyGroup(
            name=gname,
            subject=gsubject,
            goals=gdesc,
            description=gdesc,
            max_members=random.choice([6, 8, 10]),
            is_private=random.random() < 0.15,
            created_at=datetime.utcnow() - timedelta(days=random.randint(5, 90)),
        )
        g.members = members
        db.add(g)
        groups_created.append(g)

    db.commit()
    print(f"  + Created {len(groups_created)} study groups")

    for g in groups_created:
        db.refresh(g)

    # ── 4. Tasks ─────────────────────────────────────────────────────────────
    statuses = ["To Do", "In Progress", "Done"]
    status_weights = [0.4, 0.35, 0.25]
    priorities = ["Low", "Medium", "High"]
    priority_weights = [0.25, 0.5, 0.25]

    task_count = 0
    for g in groups_created:
        n_tasks = random.randint(3, 8)
        member_ids = [m.id for m in g.members]
        for _ in range(n_tasks):
            title_tmpl = random.choice(TASK_TITLES)
            title = title_tmpl.format(random.randint(1, 12))
            due_offset = random.randint(-7, 30)
            due_date = datetime.utcnow() + timedelta(days=due_offset) if random.random() > 0.3 else None
            t = WorkspaceTask(
                group_id=g.id,
                title=title,
                status=random.choices(statuses, weights=status_weights)[0],
                priority=random.choices(priorities, weights=priority_weights)[0],
                due_date=due_date,
                assigned_to=random.choice(member_ids) if member_ids and random.random() > 0.4 else None,
                description="",
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            )
            db.add(t)
            task_count += 1

    db.commit()
    print(f"  + Added {task_count} tasks across groups")

    # ── 5. Activity log ──────────────────────────────────────────────────────
    event_types = ["profile_saved", "joined_group", "task_completed", "availability_saved"]
    activity_count = 0
    for u in random.sample(users_created, 60):
        for _ in range(random.randint(1, 5)):
            e = random.choice(event_types)
            db.add(UserActivity(
                user_id=u.id,
                event_type=e,
                payload=json.dumps({}),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            ))
            activity_count += 1

    db.commit()
    print(f"  + Logged {activity_count} activity events")

    sample_username = users_created[0].username if users_created else "nchen"
    db.close()

    print("\nDone! Sample credentials:")
    print(f"  Username: {sample_username}")
    print(f"  Password: {SAMPLE_PASSWORD}")
    print(f"\n  All seed accounts use the same password: {SAMPLE_PASSWORD}")


if __name__ == "__main__":
    seed()
