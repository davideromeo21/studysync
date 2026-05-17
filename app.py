import streamlit as st
from streamlit_option_menu import option_menu
import database
from views import dashboard, profile, calendar_view, matches, workspace

database.init_db()

# Auto-seed sample data on first run (runs once; skipped if groups already exist)
try:
    import seed as _seed_module
    _seed_module.seed()
except Exception:
    pass

st.set_page_config(
    page_title="StudySync — Find Your Study Partner",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design System & CSS ──────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    /* ── Design tokens ──────────────────────────────────────────── */
    :root {
        --primary:       #4f46e5;
        --primary-dark:  #3730a3;
        --primary-light: #818cf8;
        --accent:        #06b6d4;
        --success:       #10b981;
        --warning:       #f59e0b;
        --danger:        #ef4444;
        --surface:       #ffffff;
        --surface-2:     #f8fafc;
        --border:        #e2e8f0;
        --border-focus:  #818cf8;
        --text-primary:  #0f172a;
        --text-secondary:#64748b;
        --text-muted:    #94a3b8;
        --radius-sm:     8px;
        --radius-md:     12px;
        --radius-lg:     18px;
        --radius-xl:     24px;
        --shadow-sm:     0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md:     0 4px 16px rgba(0,0,0,0.07), 0 2px 6px rgba(0,0,0,0.04);
        --shadow-lg:     0 20px 60px rgba(0,0,0,0.10), 0 6px 20px rgba(79,70,229,0.08);
        --font:          'Inter', system-ui, sans-serif;
    }

    /* ── Base ───────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] { font-family: var(--font); }

    /* Hide Streamlit chrome without touching the sidebar toggle */
    [data-testid="stToolbar"]      { display: none !important; }
    [data-testid="stDecoration"]   { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    #MainMenu                      { display: none !important; }
    footer                         { display: none !important; }
    /* Make header transparent so sidebar toggle buttons remain interactive */
    header[data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
        border-bottom: none !important;
    }

    .stApp {
        background: linear-gradient(145deg, #eef2ff 0%, #f8fafc 45%, #ecfdf5 100%);
        min-height: 100vh;
    }

    /* ── Animations ─────────────────────────────────────────────── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; } to { opacity: 1; }
    }
    @keyframes shimmer {
        0%   { background-position: -600px 0; }
        100% { background-position: 600px 0; }
    }
    @keyframes pulse-ring {
        0%   { box-shadow: 0 0 0 0 rgba(79,70,229,0.35); }
        70%  { box-shadow: 0 0 0 10px rgba(79,70,229,0); }
        100% { box-shadow: 0 0 0 0 rgba(79,70,229,0); }
    }
    @keyframes gradientShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* ── Auth layout ────────────────────────────────────────────── */
    .auth-shell {
        display: flex;
        min-height: 100vh;
        align-items: center;
        justify-content: center;
        padding: 32px 16px;
        animation: fadeIn 0.5s ease;
    }
    .auth-panel {
        background: var(--surface);
        border-radius: var(--radius-xl);
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border);
        width: 100%;
        max-width: 460px;
        overflow: hidden;
        animation: fadeInUp 0.45s ease;
    }
    .auth-brand {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #06b6d4 100%);
        background-size: 200% 200%;
        animation: gradientShift 6s ease infinite;
        padding: 36px 32px 28px;
        text-align: center;
    }
    .auth-brand-icon {
        font-size: 40px;
        margin-bottom: 10px;
        display: block;
    }
    .auth-brand-title {
        color: white;
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.3px;
        margin: 0 0 4px;
    }
    .auth-brand-sub {
        color: rgba(255,255,255,0.75);
        font-size: 13px;
        font-weight: 400;
        margin: 0;
    }
    .auth-body { padding: 28px 32px 32px; }
    .auth-tabs {
        display: flex;
        gap: 4px;
        background: var(--surface-2);
        border-radius: var(--radius-sm);
        padding: 4px;
        margin-bottom: 24px;
    }
    .auth-tab {
        flex: 1;
        text-align: center;
        padding: 8px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        color: var(--text-secondary);
        transition: all 0.2s ease;
    }
    .auth-tab.active {
        background: var(--surface);
        color: var(--primary);
        box-shadow: var(--shadow-sm);
    }

    /* ── Field group ────────────────────────────────────────────── */
    .field-group { margin-bottom: 16px; }
    .field-label {
        display: block;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 6px;
    }
    .field-error {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 12px;
        color: var(--danger);
        margin-top: 5px;
        animation: fadeIn 0.2s ease;
    }
    .field-hint {
        font-size: 11.5px;
        color: var(--text-muted);
        margin-top: 4px;
    }

    /* ── Password strength ──────────────────────────────────────── */
    .strength-bar-wrap {
        height: 4px;
        background: var(--border);
        border-radius: 999px;
        margin-top: 8px;
        overflow: hidden;
    }
    .strength-bar-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.3s ease, background 0.3s ease;
    }
    .strength-label {
        font-size: 11px;
        font-weight: 600;
        margin-top: 4px;
    }

    /* ── Primary button ─────────────────────────────────────────── */
    .stButton > button {
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.22s ease !important;
        letter-spacing: 0.1px;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(79,70,229,0.38) !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 22px rgba(79,70,229,0.46) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 8px rgba(79,70,229,0.30) !important;
    }
    .stButton > button[kind="secondary"] {
        border: 1.5px solid var(--border) !important;
        background: var(--surface) !important;
        color: var(--text-primary) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--primary-light) !important;
        color: var(--primary) !important;
    }
    .stButton > button:disabled { opacity: 0.45 !important; }

    /* ── Input fields ───────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextInput > div > div > input[type="password"] {
        border-radius: var(--radius-sm) !important;
        border: 1.5px solid var(--border) !important;
        font-size: 14px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 3px rgba(129,140,248,0.18) !important;
    }

    /* ── Sidebar ────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    .sidebar-user-card {
        background: linear-gradient(135deg, #eef2ff, #e0e7ff);
        border-radius: var(--radius-md);
        padding: 14px;
        margin-bottom: 4px;
        border: 1px solid #c7d2fe;
    }
    .sidebar-avatar {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        border: 2px solid #a5b4fc;
        display: block;
        margin-bottom: 10px;
    }
    .sidebar-user-card .username {
        color: var(--primary-dark);
        font-weight: 700;
        font-size: 15px;
    }
    .sidebar-user-card .handle {
        color: var(--text-secondary);
        font-size: 12px;
        margin-top: 2px;
    }
    .sidebar-completion {
        margin-top: 10px;
        font-size: 11px;
        color: var(--text-secondary);
        font-weight: 500;
    }
    .sidebar-completion-bar {
        height: 5px;
        background: #c7d2fe;
        border-radius: 999px;
        margin-top: 4px;
        overflow: hidden;
    }
    .sidebar-completion-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--primary), var(--accent));
        border-radius: 999px;
        transition: width 0.5s ease;
    }

    /* ── Metric cards ───────────────────────────────────────────── */
    .metric-card {
        background: var(--surface);
        padding: 22px 20px;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        text-align: center;
        border-top: 4px solid var(--primary);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        animation: fadeInUp 0.4s ease both;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-md);
    }
    .metric-card h4 {
        color: var(--text-muted);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1.4px;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .metric-card h2 {
        color: var(--text-primary);
        font-size: 30px;
        font-weight: 700;
        margin: 0;
    }
    .metric-card.green  { border-top-color: var(--success); }
    .metric-card.amber  { border-top-color: var(--warning); }
    .metric-card.purple { border-top-color: #8b5cf6; }
    .metric-card.indigo { border-top-color: var(--primary); }

    /* ── Section headers ────────────────────────────────────────── */
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 4px;
        letter-spacing: -0.2px;
    }
    .subtitle {
        color: var(--text-secondary);
        font-size: 14px;
        margin-top: -8px;
        margin-bottom: 20px;
    }

    /* ── Cards / containers ─────────────────────────────────────── */
    div[data-testid="stVerticalBlock"] div[style*="border"] {
        background: rgba(255,255,255,0.88);
        backdrop-filter: blur(10px);
        border-radius: var(--radius-md) !important;
        border: 1px solid rgba(226,232,240,0.8) !important;
        box-shadow: var(--shadow-sm);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stVerticalBlock"] div[style*="border"]:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }

    /* ── Tag pills ──────────────────────────────────────────────── */
    .tag-pill {
        display: inline-block;
        background: #f1f5f9;
        color: var(--text-secondary);
        border-radius: 999px;
        padding: 3px 10px;
        font-size: 12px;
        font-weight: 500;
        margin: 2px;
    }
    .tag-pill.blue   { background: #e0e7ff; color: #3730a3; }
    .tag-pill.green  { background: #d1fae5; color: #065f46; }
    .tag-pill.purple { background: #ede9fe; color: #5b21b6; }
    .tag-pill.amber  { background: #fef3c7; color: #92400e; }

    /* ── Score badge ────────────────────────────────────────────── */
    .score-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
    }

    /* ── Activity feed ──────────────────────────────────────────── */
    .activity-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 12px 14px;
        background: var(--surface);
        border-radius: var(--radius-sm);
        border-left: 3px solid var(--primary);
        margin-bottom: 8px;
        font-size: 13.5px;
        color: var(--text-primary);
        box-shadow: var(--shadow-sm);
        animation: fadeInUp 0.3s ease both;
    }

    /* ── Kanban ─────────────────────────────────────────────────── */
    .kanban-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: var(--surface-2);
        border-radius: var(--radius-sm);
        padding: 10px 14px;
        margin-bottom: 12px;
        font-weight: 600;
        font-size: 13px;
        color: var(--text-secondary);
        border: 1px solid var(--border);
    }
    .kanban-count {
        background: var(--border);
        color: var(--text-secondary);
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 12px;
        font-weight: 700;
    }
    .kanban-count.blue   { background: #e0e7ff; color: #3730a3; }
    .kanban-count.amber  { background: #fef3c7; color: #92400e; }
    .kanban-count.green  { background: #d1fae5; color: #065f46; }

    /* ── Profile progress bar ───────────────────────────────────── */
    .profile-progress-bar {
        height: 7px;
        border-radius: 999px;
        background: var(--border);
        overflow: hidden;
        margin-top: 6px;
    }
    .profile-progress-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, var(--primary), var(--accent));
        transition: width 0.5s ease;
    }

    /* ── Skeleton loader ────────────────────────────────────────── */
    .skeleton {
        background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
        background-size: 600px 100%;
        animation: shimmer 1.4s infinite;
        border-radius: var(--radius-sm);
    }

    /* ── Page header ────────────────────────────────────────────── */
    .page-header {
        padding: 4px 0 20px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 24px;
        animation: fadeInUp 0.35s ease;
    }
    .page-header h2 {
        font-size: 26px;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.4px;
        margin: 0 0 4px;
    }
    .page-header p {
        color: var(--text-secondary);
        font-size: 14px;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)

inject_css()

# ── Session state defaults ───────────────────────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ── Auth helpers ─────────────────────────────────────────────────────────────

def _password_strength(pw: str) -> tuple[int, str, str]:
    """Returns (score 0-100, label, css-color)."""
    if not pw:
        return 0, "", "#e2e8f0"
    score = 0
    if len(pw) >= 8:  score += 25
    if len(pw) >= 12: score += 15
    if any(c.isupper() for c in pw): score += 20
    if any(c.isdigit() for c in pw): score += 20
    if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in pw): score += 20
    if score <= 25:   return score, "Weak",   "#ef4444"
    if score <= 50:   return score, "Fair",   "#f59e0b"
    if score <= 75:   return score, "Good",   "#3b82f6"
    return score, "Strong", "#10b981"


def render_auth():
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("""
        <div class='auth-panel'>
            <div class='auth-brand'>
                <span class='auth-brand-icon'>🎓</span>
                <p class='auth-brand-title'>StudySync</p>
                <p class='auth-brand-sub'>Find your perfect study partner with AI-powered matching</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["Sign In", "Create Account"])

        # ── Login ──────────────────────────────────────────────────────
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            login_user = st.text_input(
                "Username", key="login_user",
                placeholder="your_username",
            )
            login_pass = st.text_input(
                "Password", key="login_pass",
                type="password",
                placeholder="••••••••",
            )
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Sign In", type="primary", use_container_width=True, key="btn_login"):
                if not login_user.strip() or not login_pass:
                    st.error("Please enter both username and password.")
                else:
                    with st.spinner("Signing in…"):
                        user = database.authenticate_user(login_user.strip(), login_pass)
                    if user:
                        st.session_state.logged_in   = True
                        st.session_state.user_id     = user['id']
                        st.session_state.username    = user['username']
                        st.toast(f"Welcome back, {user.get('name') or user['username']}!", icon="👋")
                        st.rerun()
                    else:
                        # Distinguish "no such user" from "wrong password"
                        exists = database.get_user_by_username(login_user.strip())
                        if not exists:
                            st.error("No account found with that username. Create one above.")
                        else:
                            st.error("Incorrect password. Please try again.")

        # ── Register ───────────────────────────────────────────────────
        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_user = st.text_input(
                "Username", key="reg_user",
                placeholder="e.g. alice_smith",
                help="3–30 characters · letters, numbers, underscores only",
            )
            reg_pass = st.text_input(
                "Password", key="reg_pass",
                type="password",
                placeholder="Min. 8 characters",
            )

            # Live password strength meter
            if reg_pass:
                strength_score, strength_label, strength_color = _password_strength(reg_pass)
                st.markdown(
                    f"<div class='strength-bar-wrap'>"
                    f"<div class='strength-bar-fill' style='width:{strength_score}%;background:{strength_color};'></div>"
                    f"</div>"
                    f"<span class='strength-label' style='color:{strength_color};'>{strength_label}</span>",
                    unsafe_allow_html=True,
                )

            reg_confirm = st.text_input(
                "Confirm Password", key="reg_confirm",
                type="password",
                placeholder="Repeat your password",
            )

            # Inline mismatch warning (before submit)
            if reg_confirm and reg_pass and reg_pass != reg_confirm:
                st.markdown(
                    "<div class='field-error'>⚠ Passwords do not match</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account", type="primary", use_container_width=True, key="btn_reg"):
                errors = []
                if not reg_user.strip():
                    errors.append("Username is required.")
                if not reg_pass:
                    errors.append("Password is required.")
                elif len(reg_pass) < 8:
                    errors.append("Password must be at least 8 characters.")
                if reg_pass and reg_confirm and reg_pass != reg_confirm:
                    errors.append("Passwords do not match.")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    with st.spinner("Creating your account…"):
                        result = database.create_user(reg_user.strip(), reg_pass)
                    if result == 'ok':
                        st.success("Account created! Sign in with the tab above.")
                        st.balloons()
                    elif result == 'taken':
                        st.error("That username is already taken. Please choose another.")
                    else:
                        st.error("Invalid username. Use 3–30 characters: letters, numbers, underscores.")

        st.markdown("<br>", unsafe_allow_html=True)
        feat_cols = st.columns(3)
        feats = [("🎯", "Smart Matching"), ("📅", "Schedule Sync"), ("🛠️", "Group Workspaces")]
        for col_f, (icon, label) in zip(feat_cols, feats):
            with col_f:
                st.markdown(
                    f"<div style='text-align:center;padding:10px 4px;background:#f8fafc;"
                    f"border-radius:10px;border:1px solid #e2e8f0;'>"
                    f"<div style='font-size:22px;'>{icon}</div>"
                    f"<div style='font-size:11px;font-weight:600;color:#64748b;margin-top:4px;'>{label}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


# ── Onboarding dialog ────────────────────────────────────────────────────────

def maybe_show_onboarding(user: dict):
    if user.get('name') or st.session_state.get('onboarding_dismissed'):
        return

    @st.dialog("🎓 Welcome to StudySync!")
    def _onboarding():
        step = st.session_state.get('onboarding_step', 1)
        prog_html = "".join(
            f"<span style='display:inline-block;width:30px;height:30px;border-radius:50%;"
            f"background:{'#4f46e5' if i+1<=step else '#e2e8f0'};"
            f"color:{'white' if i+1<=step else '#94a3b8'};"
            f"text-align:center;line-height:30px;font-weight:700;font-size:13px;margin:0 4px;'>"
            f"{i+1}</span>"
            for i in range(3)
        )
        st.markdown(f"<div style='text-align:center;margin-bottom:20px;'>{prog_html}</div>",
                    unsafe_allow_html=True)

        steps_content = [
            ("Build your profile", "Tell us your name, course, subjects, and study style — the algorithm uses this to find your best peers.", "Head to **My Profile** in the sidebar."),
            ("Set your availability", "Mark which days and time slots you're free each week so matches can see when to sync.", "Go to **Availability** and tick your free slots."),
            ("Find your matches 🎯", "Your compatibility scores are ready! See who you align with and join or create a study group.", "Visit **Matches & Groups** to get started."),
        ]
        title, body, cta = steps_content[step - 1]
        st.markdown(f"### Step {step}: {title}")
        st.markdown(body)
        st.info(cta)

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if step > 1 and st.button("← Back", use_container_width=True):
                st.session_state['onboarding_step'] = step - 1
                st.rerun()
        with c2:
            if step < 3:
                if st.button("Next →", type="primary", use_container_width=True):
                    st.session_state['onboarding_step'] = step + 1
                    st.rerun()
            else:
                if st.button("Let's go! 🚀", type="primary", use_container_width=True):
                    st.session_state['onboarding_dismissed'] = True
                    st.rerun()
        with c3:
            if st.button("Skip", use_container_width=True):
                st.session_state['onboarding_dismissed'] = True
                st.rerun()

    _onboarding()


# ── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar(user: dict, completion: int):
    from utils import get_avatar_url
    with st.sidebar:
        display_name = user.get('name') or user['username']
        avatar_url   = get_avatar_url(user['username'])

        st.markdown(
            f"""<div class='sidebar-user-card'>
                <img src='{avatar_url}' class='sidebar-avatar'>
                <div class='username'>🎓 {display_name}</div>
                <div class='handle'>@{user['username']}</div>
                <div class='sidebar-completion'>{completion}% profile complete</div>
                <div class='sidebar-completion-bar'>
                    <div class='sidebar-completion-fill' style='width:{completion}%;'></div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "My Profile", "Availability", "Matches & Groups", "Workspaces"],
            icons=["grid-1x2", "person-circle", "calendar3", "people-fill", "kanban"],
            default_index=0,
            styles={
                "container":  {"padding": "0!important", "background-color": "transparent"},
                "icon":       {"color": "#4f46e5", "font-size": "16px"},
                "nav-link": {
                    "font-size": "14px", "text-align": "left", "margin": "2px 0",
                    "--hover-color": "#eef2ff", "border-radius": "10px",
                    "padding": "10px 14px",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #4f46e5, #3730a3)",
                    "color": "white", "font-weight": "600", "border-radius": "10px",
                },
            }
        )

        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    return selected


# ── Main routing ─────────────────────────────────────────────────────────────

if not st.session_state.logged_in:
    render_auth()
else:
    user = database.get_user_by_id(st.session_state.user_id)

    # Compute completion for sidebar
    from views.dashboard import calculate_profile_completion
    completion = calculate_profile_completion(user)

    maybe_show_onboarding(user)
    selected_view = render_sidebar(user, completion)

    if selected_view == "Dashboard":
        dashboard.render()
    elif selected_view == "My Profile":
        profile.render()
    elif selected_view == "Availability":
        calendar_view.render()
    elif selected_view == "Matches & Groups":
        matches.render()
    elif selected_view == "Workspaces":
        workspace.render()
