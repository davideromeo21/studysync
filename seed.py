"""
Seed realistic test data on first startup.
Skipped if any user other than the first admin already exists.
Password for every seeded account: Study123!
"""
import database
from config import DAYS, TIMESLOTS

_PASSWORD = "Study123!"

# ── User profiles ─────────────────────────────────────────────────────────────
USERS = [
    {
        "username": "alice_nova",
        "name": "Alice Ferreira",
        "course": "BSc Data Science",
        "degree_level": "Bachelor",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Cascais Line",
        "subjects": ["Data Science", "Machine Learning", "Statistics & Probability", "Mathematics"],
        "skill_levels": {"Data Science": 4, "Machine Learning": 3, "Statistics & Probability": 4, "Mathematics": 3},
        "goals": ["Deep Understanding", "Exam Prep", "Research"],
        "study_styles": ["Discussion-based", "Group Problem-solving", "Note Sharing"],
        "study_environment": ["Library", "Campus", "Online / Remote"],
        "study_vibe": ["Pomodoro", "Intense Focus"],
        "availability": [
            ("Monday", "Morning (8am-12pm)"), ("Monday", "Evening (5pm-10pm)"),
            ("Tuesday", "Afternoon (12pm-5pm)"), ("Wednesday", "Morning (8am-12pm)"),
            ("Thursday", "Afternoon (12pm-5pm)"), ("Friday", "Morning (8am-12pm)"),
        ],
    },
    {
        "username": "beto_codes",
        "name": "Beto Almeida",
        "course": "MSc Computer Science",
        "degree_level": "Master",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Cascais Line",
        "subjects": ["Computer Science", "Algorithms & Data Structures", "Software Engineering", "Web Development"],
        "skill_levels": {"Computer Science": 5, "Algorithms & Data Structures": 4, "Software Engineering": 4, "Web Development": 3},
        "goals": ["Project Collaboration", "Deep Understanding", "Project Work"],
        "study_styles": ["Group Problem-solving", "Practice Questions", "Teaching / Explaining"],
        "study_environment": ["Home", "Online / Remote", "Co-working Space"],
        "study_vibe": ["Lofi Music", "Breaks Every 45 min", "Snacks & Study"],
        "availability": [
            ("Monday", "Afternoon (12pm-5pm)"), ("Tuesday", "Evening (5pm-10pm)"),
            ("Wednesday", "Afternoon (12pm-5pm)"), ("Thursday", "Evening (5pm-10pm)"),
            ("Friday", "Afternoon (12pm-5pm)"), ("Saturday", "Morning (8am-12pm)"),
        ],
    },
    {
        "username": "carla_econ",
        "name": "Carla Mendes",
        "course": "BSc Economics",
        "degree_level": "Bachelor",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Lisbon Centre",
        "subjects": ["Economics", "Microeconomics", "Macroeconomics", "Mathematics"],
        "skill_levels": {"Economics": 4, "Microeconomics": 3, "Macroeconomics": 3, "Mathematics": 2},
        "goals": ["Exam Prep", "Homework Help", "Deep Understanding"],
        "study_styles": ["Quiet Revision", "Flashcards", "Practice Questions"],
        "study_environment": ["Library", "Café", "Campus"],
        "study_vibe": ["Silent 3 Hours", "Pomodoro"],
        "availability": [
            ("Monday", "Morning (8am-12pm)"), ("Tuesday", "Morning (8am-12pm)"),
            ("Wednesday", "Evening (5pm-10pm)"), ("Thursday", "Morning (8am-12pm)"),
            ("Friday", "Afternoon (12pm-5pm)"),
        ],
    },
    {
        "username": "dani_finance",
        "name": "Daniel Sousa",
        "course": "MSc Finance",
        "degree_level": "Master",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Cascais Line",
        "subjects": ["Finance", "Economics", "Accounting", "Statistics & Probability"],
        "skill_levels": {"Finance": 4, "Economics": 3, "Accounting": 4, "Statistics & Probability": 2},
        "goals": ["Exam Prep", "Thesis / Dissertation", "Networking"],
        "study_styles": ["Discussion-based", "Note Sharing", "Mind Mapping"],
        "study_environment": ["Café", "Library", "Campus"],
        "study_vibe": ["Chatty", "Snacks & Study", "Breaks Every 45 min"],
        "availability": [
            ("Tuesday", "Afternoon (12pm-5pm)"), ("Tuesday", "Evening (5pm-10pm)"),
            ("Thursday", "Afternoon (12pm-5pm)"), ("Thursday", "Evening (5pm-10pm)"),
            ("Saturday", "Afternoon (12pm-5pm)"),
        ],
    },
    {
        "username": "elena_ml",
        "name": "Elena Rodrigues",
        "course": "PhD Machine Learning",
        "degree_level": "PhD",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Sintra Line",
        "subjects": ["Machine Learning", "Statistics & Probability", "Mathematics", "Data Science"],
        "skill_levels": {"Machine Learning": 5, "Statistics & Probability": 5, "Mathematics": 4, "Data Science": 5},
        "goals": ["Research", "Deep Understanding", "Thesis / Dissertation"],
        "study_styles": ["Group Problem-solving", "Discussion-based", "Teaching / Explaining"],
        "study_environment": ["Online / Remote", "Campus", "Library"],
        "study_vibe": ["Intense Focus", "Silent 3 Hours", "Pomodoro"],
        "availability": [
            ("Monday", "Afternoon (12pm-5pm)"), ("Wednesday", "Morning (8am-12pm)"),
            ("Wednesday", "Afternoon (12pm-5pm)"), ("Friday", "Morning (8am-12pm)"),
            ("Friday", "Afternoon (12pm-5pm)"),
        ],
    },
    {
        "username": "filip_mkt",
        "name": "Filip Costa",
        "course": "BSc Marketing",
        "degree_level": "Bachelor",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Lisbon Centre",
        "subjects": ["Marketing", "Management", "Strategy", "Economics"],
        "skill_levels": {"Marketing": 4, "Management": 3, "Strategy": 3, "Economics": 2},
        "goals": ["Project Collaboration", "Casual Study", "Networking"],
        "study_styles": ["Discussion-based", "Mind Mapping", "Note Sharing"],
        "study_environment": ["Café", "Co-working Space", "Online / Remote"],
        "study_vibe": ["Chatty", "Lofi Music", "Snacks & Study"],
        "availability": [
            ("Monday", "Evening (5pm-10pm)"), ("Wednesday", "Evening (5pm-10pm)"),
            ("Thursday", "Afternoon (12pm-5pm)"), ("Friday", "Evening (5pm-10pm)"),
            ("Saturday", "Morning (8am-12pm)"), ("Sunday", "Afternoon (12pm-5pm)"),
        ],
    },
    {
        "username": "gabi_law",
        "name": "Gabriela Lima",
        "course": "LLM Law",
        "degree_level": "Master",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Almada",
        "subjects": ["Law", "Political Science", "International Relations", "Philosophy"],
        "skill_levels": {"Law": 4, "Political Science": 3, "International Relations": 4, "Philosophy": 3},
        "goals": ["Exam Prep", "Deep Understanding", "Application Preparation"],
        "study_styles": ["Quiet Revision", "Flashcards", "Practice Questions"],
        "study_environment": ["Library", "Home", "Campus"],
        "study_vibe": ["Silent 3 Hours", "Pomodoro", "Breaks Every 45 min"],
        "availability": [
            ("Monday", "Morning (8am-12pm)"), ("Monday", "Afternoon (12pm-5pm)"),
            ("Tuesday", "Morning (8am-12pm)"), ("Thursday", "Morning (8am-12pm)"),
            ("Friday", "Morning (8am-12pm)"),
        ],
    },
    {
        "username": "hugo_ops",
        "name": "Hugo Barbosa",
        "course": "MSc Management",
        "degree_level": "Master",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Cascais Line",
        "subjects": ["Management", "Operations Research", "Strategy", "Finance"],
        "skill_levels": {"Management": 4, "Operations Research": 3, "Strategy": 4, "Finance": 2},
        "goals": ["Project Work", "Exam Prep", "Homework Help"],
        "study_styles": ["Group Problem-solving", "Discussion-based", "Practice Questions"],
        "study_environment": ["Campus", "Library", "Online / Remote"],
        "study_vibe": ["Pomodoro", "Breaks Every 45 min"],
        "availability": [
            ("Tuesday", "Morning (8am-12pm)"), ("Tuesday", "Afternoon (12pm-5pm)"),
            ("Wednesday", "Morning (8am-12pm)"), ("Friday", "Afternoon (12pm-5pm)"),
            ("Saturday", "Morning (8am-12pm)"), ("Saturday", "Afternoon (12pm-5pm)"),
        ],
    },
    {
        "username": "iris_bio",
        "name": "Iris Oliveira",
        "course": "BSc Biochemistry",
        "degree_level": "Bachelor",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Lisbon Centre",
        "subjects": ["Biochemistry", "Biology", "Chemistry", "Medicine"],
        "skill_levels": {"Biochemistry": 4, "Biology": 4, "Chemistry": 3, "Medicine": 2},
        "goals": ["Exam Prep", "Deep Understanding", "Research"],
        "study_styles": ["Flashcards", "Practice Questions", "Note Sharing"],
        "study_environment": ["Library", "Campus", "Home"],
        "study_vibe": ["Silent 3 Hours", "Intense Focus", "Pomodoro"],
        "availability": [
            ("Monday", "Morning (8am-12pm)"), ("Wednesday", "Morning (8am-12pm)"),
            ("Wednesday", "Evening (5pm-10pm)"), ("Thursday", "Morning (8am-12pm)"),
            ("Sunday", "Morning (8am-12pm)"), ("Sunday", "Afternoon (12pm-5pm)"),
        ],
    },
    {
        "username": "joao_algo",
        "name": "João Pereira",
        "course": "BSc Computer Science",
        "degree_level": "Bachelor",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Sintra Line",
        "subjects": ["Algorithms & Data Structures", "Computer Science", "Mathematics", "Software Engineering"],
        "skill_levels": {"Algorithms & Data Structures": 3, "Computer Science": 3, "Mathematics": 3, "Software Engineering": 2},
        "goals": ["Homework Help", "Exam Prep", "Deep Understanding"],
        "study_styles": ["Practice Questions", "Group Problem-solving", "Flashcards"],
        "study_environment": ["Home", "Library", "Online / Remote"],
        "study_vibe": ["Lofi Music", "Breaks Every 45 min", "Pomodoro"],
        "availability": [
            ("Monday", "Evening (5pm-10pm)"), ("Tuesday", "Morning (8am-12pm)"),
            ("Thursday", "Morning (8am-12pm)"), ("Thursday", "Evening (5pm-10pm)"),
            ("Friday", "Morning (8am-12pm)"), ("Saturday", "Evening (5pm-10pm)"),
        ],
    },
    {
        "username": "kate_psych",
        "name": "Katarina Novak",
        "course": "MSc Psychology",
        "degree_level": "Master",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Lisbon Centre",
        "subjects": ["Psychology", "Sociology", "Philosophy", "Statistics & Probability"],
        "skill_levels": {"Psychology": 5, "Sociology": 4, "Philosophy": 3, "Statistics & Probability": 2},
        "goals": ["Research", "Thesis / Dissertation", "Deep Understanding"],
        "study_styles": ["Discussion-based", "Mind Mapping", "Note Sharing"],
        "study_environment": ["Café", "Library", "Online / Remote"],
        "study_vibe": ["Chatty", "Lofi Music", "Breaks Every 45 min"],
        "availability": [
            ("Tuesday", "Morning (8am-12pm)"), ("Tuesday", "Evening (5pm-10pm)"),
            ("Wednesday", "Afternoon (12pm-5pm)"), ("Friday", "Morning (8am-12pm)"),
            ("Friday", "Evening (5pm-10pm)"),
        ],
    },
    {
        "username": "leo_strat",
        "name": "Leonardo Fonseca",
        "course": "MBA Strategy",
        "degree_level": "Master",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Cascais Line",
        "subjects": ["Strategy", "Management", "Marketing", "Finance"],
        "skill_levels": {"Strategy": 5, "Management": 5, "Marketing": 3, "Finance": 4},
        "goals": ["Networking", "Project Collaboration", "Casual Study"],
        "study_styles": ["Discussion-based", "Teaching / Explaining", "Mind Mapping"],
        "study_environment": ["Co-working Space", "Café", "Online / Remote"],
        "study_vibe": ["Chatty", "Snacks & Study"],
        "availability": [
            ("Monday", "Afternoon (12pm-5pm)"), ("Wednesday", "Afternoon (12pm-5pm)"),
            ("Thursday", "Afternoon (12pm-5pm)"), ("Friday", "Afternoon (12pm-5pm)"),
            ("Saturday", "Morning (8am-12pm)"), ("Saturday", "Afternoon (12pm-5pm)"),
        ],
    },
    {
        "username": "mia_stats",
        "name": "Mia Zhang",
        "course": "MSc Data Science",
        "degree_level": "Master",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Sintra Line",
        "subjects": ["Statistics & Probability", "Data Science", "Machine Learning", "Linear Algebra"],
        "skill_levels": {"Statistics & Probability": 5, "Data Science": 4, "Machine Learning": 4, "Linear Algebra": 4},
        "goals": ["Research", "Deep Understanding", "Exam Prep"],
        "study_styles": ["Group Problem-solving", "Discussion-based", "Practice Questions"],
        "study_environment": ["Library", "Online / Remote", "Campus"],
        "study_vibe": ["Intense Focus", "Pomodoro", "Silent 3 Hours"],
        "availability": [
            ("Monday", "Morning (8am-12pm)"), ("Monday", "Afternoon (12pm-5pm)"),
            ("Tuesday", "Afternoon (12pm-5pm)"), ("Wednesday", "Morning (8am-12pm)"),
            ("Friday", "Afternoon (12pm-5pm)"), ("Friday", "Evening (5pm-10pm)"),
        ],
    },
    {
        "username": "nuno_acct",
        "name": "Nuno Carvalho",
        "course": "BSc Accounting",
        "degree_level": "Bachelor",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Almada",
        "subjects": ["Accounting", "Finance", "Economics", "Mathematics"],
        "skill_levels": {"Accounting": 4, "Finance": 3, "Economics": 3, "Mathematics": 2},
        "goals": ["Exam Prep", "Homework Help", "Application Preparation"],
        "study_styles": ["Flashcards", "Quiet Revision", "Practice Questions"],
        "study_environment": ["Library", "Home", "Campus"],
        "study_vibe": ["Pomodoro", "Breaks Every 45 min", "Silent 3 Hours"],
        "availability": [
            ("Tuesday", "Morning (8am-12pm)"), ("Wednesday", "Morning (8am-12pm)"),
            ("Thursday", "Morning (8am-12pm)"), ("Thursday", "Afternoon (12pm-5pm)"),
            ("Friday", "Morning (8am-12pm)"),
        ],
    },
    {
        "username": "olivia_web",
        "name": "Olivia Santos",
        "course": "BSc Software Engineering",
        "degree_level": "Bachelor",
        "university": "Nova SBE",
        "campus": "Carcavelos",
        "location_zone": "Lisbon Centre",
        "subjects": ["Web Development", "Software Engineering", "Computer Science", "Algorithms & Data Structures"],
        "skill_levels": {"Web Development": 4, "Software Engineering": 3, "Computer Science": 3, "Algorithms & Data Structures": 2},
        "goals": ["Project Work", "Project Collaboration", "Homework Help"],
        "study_styles": ["Group Problem-solving", "Note Sharing", "Discussion-based"],
        "study_environment": ["Co-working Space", "Home", "Café"],
        "study_vibe": ["Lofi Music", "Chatty", "Snacks & Study"],
        "availability": [
            ("Monday", "Afternoon (12pm-5pm)"), ("Monday", "Evening (5pm-10pm)"),
            ("Wednesday", "Evening (5pm-10pm)"), ("Thursday", "Evening (5pm-10pm)"),
            ("Friday", "Evening (5pm-10pm)"), ("Sunday", "Afternoon (12pm-5pm)"),
        ],
    },
]

# ── Groups ─────────────────────────────────────────────────────────────────────
GROUPS = [
    {
        "name": "ML Study Circle",
        "subject": "Machine Learning",
        "meeting_times": "Monday Afternoon, Wednesday Morning",
        "goals": "Work through ISLR textbook chapters, share Kaggle notebooks, prep for midterm.",
        "description": "A focused group tackling ML theory and practice together. All levels welcome.",
        "max_members": 6,
        "creator": "alice_nova",
        "members": ["elena_ml", "mia_stats", "beto_codes"],
        "tasks": [
            {"title": "Chapter 4: Classification exercises", "priority": "High", "status": "In Progress"},
            {"title": "Set up shared Jupyter notebook repo", "priority": "Medium", "status": "Done"},
            {"title": "Mock exam for midterm", "priority": "High", "status": "To Do"},
        ],
    },
    {
        "name": "Finance & Econ Masters",
        "subject": "Finance",
        "meeting_times": "Tuesday Afternoon, Thursday Evening",
        "goals": "CFA prep, case study discussions, thesis idea sharing.",
        "description": "Graduate students tackling finance theory and real-world applications.",
        "max_members": 8,
        "creator": "dani_finance",
        "members": ["carla_econ", "nuno_acct", "hugo_ops"],
        "tasks": [
            {"title": "CFA mock exam — Fixed Income section", "priority": "High", "status": "To Do"},
            {"title": "Case study: Novo Banco restructuring", "priority": "Medium", "status": "In Progress"},
            {"title": "Thesis topic brainstorm session", "priority": "Low", "status": "To Do"},
        ],
    },
    {
        "name": "CS Algorithms Bootcamp",
        "subject": "Algorithms & Data Structures",
        "meeting_times": "Monday Evening, Thursday Morning",
        "goals": "LeetCode weekly sessions, algorithm theory review, interview prep.",
        "description": "Weekly coding challenges and theory deep-dives. Bring your laptop!",
        "max_members": 8,
        "creator": "beto_codes",
        "members": ["joao_algo", "olivia_web"],
        "tasks": [
            {"title": "LeetCode: Graph traversal problems (20 questions)", "priority": "High", "status": "In Progress"},
            {"title": "Dynamic programming cheatsheet", "priority": "Medium", "status": "To Do"},
            {"title": "Mock technical interview round", "priority": "High", "status": "To Do"},
        ],
    },
    {
        "name": "Strategy & Leadership Lab",
        "subject": "Strategy",
        "meeting_times": "Wednesday Afternoon, Friday Afternoon",
        "goals": "Case competition prep, strategy frameworks, networking with peers.",
        "description": "MBA & master students sharpening business strategy skills.",
        "max_members": 6,
        "creator": "leo_strat",
        "members": ["filip_mkt", "hugo_ops", "dani_finance"],
        "tasks": [
            {"title": "Porter's 5 Forces: Amazon case", "priority": "High", "status": "Done"},
            {"title": "BCG matrix workshop", "priority": "Medium", "status": "In Progress"},
            {"title": "Case competition practice — McKinsey format", "priority": "High", "status": "To Do"},
        ],
    },
    {
        "name": "Statistics & Probability Hub",
        "subject": "Statistics & Probability",
        "meeting_times": "Monday Morning, Friday Afternoon",
        "goals": "Probability theory, statistical inference, Python/R exercises.",
        "description": "From basics to Bayesian — all stats topics covered together.",
        "max_members": 8,
        "creator": "mia_stats",
        "members": ["alice_nova", "elena_ml", "carla_econ", "nuno_acct"],
        "tasks": [
            {"title": "Hypothesis testing problem set", "priority": "High", "status": "In Progress"},
            {"title": "Bayesian inference intro session", "priority": "Medium", "status": "To Do"},
            {"title": "R vs Python for stats — comparison doc", "priority": "Low", "status": "To Do"},
        ],
    },
    {
        "name": "Law & Society Reading Group",
        "subject": "Law",
        "meeting_times": "Monday Morning, Thursday Morning",
        "goals": "Case law review, exam preparation, essay writing workshops.",
        "description": "Deep reading and discussion of key legal texts and current rulings.",
        "max_members": 6,
        "creator": "gabi_law",
        "members": ["kate_psych"],
        "tasks": [
            {"title": "EU competition law — summary notes", "priority": "High", "status": "To Do"},
            {"title": "Mock essay: constitutional law", "priority": "Medium", "status": "In Progress"},
        ],
    },
]


def seed():
    """Insert test data. Skips if more than 2 users already exist."""
    if len(database.get_all_users()) > 2:
        return

    print("Seeding test users, groups and tasks…")

    # Create users and profiles
    user_ids = {}
    for u in USERS:
        result = database.create_user(u["username"], _PASSWORD)
        if result != "ok":
            continue

        user = database.get_user_by_username(u["username"])
        if not user:
            continue
        uid = user["id"]
        user_ids[u["username"]] = uid

        database.update_user_profile(uid, {
            "name": u["name"],
            "course": u["course"],
            "degree_level": u["degree_level"],
            "university": u["university"],
            "campus": u["campus"],
            "location_zone": u["location_zone"],
            "subjects": u["subjects"],
            "skill_levels": u["skill_levels"],
            "goals": u["goals"],
            "study_styles": u["study_styles"],
            "study_environment": u["study_environment"],
            "study_vibe": u["study_vibe"],
        })

        database.set_user_availability(uid, u["availability"])
        database.log_activity(uid, "profile_saved", {})

    # Create groups + tasks
    for g in GROUPS:
        creator_username = g["creator"]
        creator_id = user_ids.get(creator_username)
        if not creator_id:
            continue

        gid = database.create_group(
            name=g["name"],
            subject=g["subject"],
            meeting_times=g["meeting_times"],
            goals=g["goals"],
            creator_user_id=creator_id,
            description=g["description"],
            max_members=g["max_members"],
        )
        if gid < 0:
            continue

        for member_username in g["members"]:
            mid = user_ids.get(member_username)
            if mid:
                database.join_group(gid, mid)

        for task in g.get("tasks", []):
            database.add_group_task(
                group_id=gid,
                title=task["title"],
                priority=task["priority"],
            )

    print(f"Seeded {len(user_ids)} users and {len(GROUPS)} groups.")
