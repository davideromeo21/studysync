"""Shared configuration and constants for Study Group Matcher Pro."""

AVAILABLE_SUBJECTS = [
    # STEM
    "Mathematics", "Linear Algebra", "Calculus", "Statistics & Probability",
    "Computer Science", "Machine Learning", "Data Science", "Algorithms & Data Structures",
    "Web Development", "Software Engineering",
    "Physics", "Chemistry", "Biology", "Biochemistry",
    # Business
    "Economics", "Microeconomics", "Macroeconomics", "Finance",
    "Accounting", "Marketing", "Management", "Strategy", "Operations Research",
    # Humanities & Social Sciences
    "History", "Literature", "Philosophy", "Psychology", "Sociology",
    "Law", "Political Science", "International Relations",
    # Other
    "Architecture", "Engineering", "Medicine", "Nursing",
]

AVAILABLE_GOALS = [
    "Exam Prep",
    "Homework Help",
    "Deep Understanding",
    "Project Collaboration",
    "Casual Study",
    "Project Work",
    "Application Preparation",
    "Thesis / Dissertation",
    "Research",
    "Networking",
]

AVAILABLE_STYLES = [
    "Quiet Revision",
    "Discussion-based",
    "Practice Questions",
    "Group Problem-solving",
    "Teaching / Explaining",
    "Note Sharing",
    "Mind Mapping",
    "Flashcards",
]

AVAILABLE_ENVIRONMENTS = [
    "Library",
    "Café",
    "Home",
    "Campus",
    "Co-working Space",
    "Online / Remote",
    "Outdoor",
]

AVAILABLE_VIBES = [
    "Pomodoro",
    "Silent 3 Hours",
    "Chatty",
    "Lofi Music",
    "Intense Focus",
    "Breaks Every 45 min",
    "Snacks & Study",
]

AVAILABLE_DEGREES = ["Bachelor", "Master", "PhD", "Other"]

KANBAN_STATUSES = ["To Do", "In Progress", "Done"]
KANBAN_PRIORITIES = ["Low", "Medium", "High"]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIMESLOTS = ["Morning (8am-12pm)", "Afternoon (12pm-5pm)", "Evening (5pm-10pm)"]
SLOT_ICONS = ["🌅", "☀️", "🌙"]

# Score color thresholds
def score_color(score: int) -> str:
    if score >= 70:
        return "#10b981"   # green
    elif score >= 40:
        return "#f59e0b"   # amber
    else:
        return "#3b82f6"   # blue

def score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Strong"
    elif score >= 40:
        return "Good"
    elif score >= 20:
        return "Moderate"
    else:
        return "Low"
