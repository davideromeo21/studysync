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
    initial_sidebar_state="collapsed",
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
        --violet:        #7c3aed;
        --cyan:          #06b6d4;
        --teal:          #0d9488;
        --emerald:       #059669;
        --amber:         #d97706;
        --rose:          #e11d48;
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
        --shadow-md:     0 4px 16px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.04);
        --shadow-lg:     0 20px 60px rgba(0,0,0,0.12), 0 6px 20px rgba(79,70,229,0.10);
        --font:          'Inter', system-ui, sans-serif;
    }

    /* ── Base ───────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] { font-family: var(--font); }

    /* Hide Streamlit chrome completely */
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"],
    header[data-testid="stHeader"],
    #MainMenu, footer { display: none !important; }

    /* Collapse the sidebar entirely — nav is top-bar only */
    section[data-testid="stSidebar"] { display: none !important; }

    /* Full-width main area */
    .block-container {
        max-width: 1280px !important;
        padding-top: 0.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    .stApp {
        background: linear-gradient(135deg, #f0f4ff 0%, #fafafa 40%, #f0fdf4 100%);
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

    /* ── Top navigation bar ─────────────────────────────────────── */
    .topnav-wrap {
        background: white;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border);
        padding: 10px 20px;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        animation: fadeIn 0.3s ease;
    }
    .topnav-brand {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -0.4px;
        background: linear-gradient(135deg, var(--primary) 0%, var(--violet) 60%, var(--cyan) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        white-space: nowrap;
    }
    .topnav-user {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .topnav-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border: 2.5px solid var(--primary-light);
        box-shadow: 0 0 0 3px rgba(129,140,248,0.15);
    }
    .topnav-name {
        font-size: 13px;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
    }
    .topnav-handle {
        font-size: 11px;
        color: var(--text-muted);
    }
    .topnav-progress-wrap {
        width: 80px;
        height: 4px;
        background: var(--border);
        border-radius: 999px;
        overflow: hidden;
        margin-top: 3px;
    }
    .topnav-progress-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.4s ease;
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

    /* ── Metric cards ───────────────────────────────────────────── */
    .metric-card {
        background: var(--surface);
        padding: 22px 20px;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        text-align: center;
        border-top: 4px solid var(--primary);
        transition: transform 0.22s ease, box-shadow 0.22s ease;
        animation: fadeInUp 0.4s ease both;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 100%;
        background: linear-gradient(180deg, rgba(79,70,229,0.04) 0%, transparent 60%);
        pointer-events: none;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-md);
    }
    .metric-card h4 {
        color: var(--text-muted);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1.6px;
        margin-bottom: 8px;
        font-weight: 700;
    }
    .metric-card h2 {
        color: var(--text-primary);
        font-size: 30px;
        font-weight: 700;
        margin: 0;
    }
    .metric-card.green  { border-top-color: var(--emerald); }
    .metric-card.green::before  { background: linear-gradient(180deg,rgba(5,150,105,0.05) 0%,transparent 60%); }
    .metric-card.amber  { border-top-color: var(--amber); }
    .metric-card.amber::before  { background: linear-gradient(180deg,rgba(217,119,6,0.05) 0%,transparent 60%); }
    .metric-card.purple { border-top-color: var(--violet); }
    .metric-card.purple::before { background: linear-gradient(180deg,rgba(124,58,237,0.05) 0%,transparent 60%); }
    .metric-card.cyan   { border-top-color: var(--cyan); }
    .metric-card.cyan::before   { background: linear-gradient(180deg,rgba(6,182,212,0.05) 0%,transparent 60%); }
    .metric-card.indigo { border-top-color: var(--primary); }
    .metric-card.rose   { border-top-color: var(--rose); }
    .metric-card.rose::before   { background: linear-gradient(180deg,rgba(225,29,72,0.05) 0%,transparent 60%); }

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
        padding: 3px 11px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px;
        border: 1px solid #e2e8f0;
        letter-spacing: 0.1px;
    }
    .tag-pill.blue   { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }
    .tag-pill.indigo { background: #eef2ff; color: #3730a3; border-color: #c7d2fe; }
    .tag-pill.violet { background: #f5f3ff; color: #5b21b6; border-color: #ddd6fe; }
    .tag-pill.green  { background: #f0fdf4; color: #065f46; border-color: #bbf7d0; }
    .tag-pill.teal   { background: #f0fdfa; color: #0f766e; border-color: #99f6e4; }
    .tag-pill.cyan   { background: #ecfeff; color: #0e7490; border-color: #a5f3fc; }
    .tag-pill.amber  { background: #fffbeb; color: #92400e; border-color: #fde68a; }
    .tag-pill.rose   { background: #fff1f2; color: #9f1239; border-color: #fecdd3; }
    .tag-pill.purple { background: #faf5ff; color: #6b21a8; border-color: #e9d5ff; }

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
        padding: 12px 16px;
        background: var(--surface);
        border-radius: var(--radius-sm);
        border-left: 3px solid var(--primary);
        margin-bottom: 8px;
        font-size: 13.5px;
        color: var(--text-primary);
        box-shadow: var(--shadow-sm);
        animation: fadeInUp 0.3s ease both;
        transition: border-color 0.2s ease;
    }
    .activity-item:hover { border-left-color: var(--violet); }

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
        border-bottom: 2px solid transparent;
        border-image: linear-gradient(90deg, var(--primary), var(--violet), var(--cyan)) 1;
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

    /* ── Score / match badges ───────────────────────────────────── */
    .match-score-high   { color: #059669; font-weight: 800; }
    .match-score-mid    { color: #d97706; font-weight: 800; }
    .match-score-low    { color: #dc2626; font-weight: 800; }

    /* ── Kanban columns ─────────────────────────────────────────── */
    .kanban-header.todo   { border-left: 3px solid #94a3b8; }
    .kanban-header.doing  { border-left: 3px solid #f59e0b; }
    .kanban-header.done   { border-left: 3px solid #10b981; }
    .kanban-header.review { border-left: 3px solid #8b5cf6; }

    /* ── Scrollbar ──────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

    /* ── Streamlit tab strip ────────────────────────────────────── */
    [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--surface-2) !important;
        border-radius: var(--radius-sm);
        padding: 4px;
    }
    [data-baseweb="tab"] {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    [aria-selected="true"][data-baseweb="tab"] {
        background: white !important;
        box-shadow: var(--shadow-sm) !important;
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


# ── Top navigation ────────────────────────────────────────────────────────────

_VIEW_NAMES = ["Dashboard", "My Profile", "Availability", "Matches & Groups", "Workspaces"]
_VIEW_ICONS = ["grid-1x2", "person-circle", "calendar3", "people-fill", "kanban"]


def render_topnav(user: dict, completion: int) -> str:
    from utils import get_avatar_url

    display_name = user.get('name') or user['username']
    avatar_url   = get_avatar_url(user['username'])
    comp_color   = "#059669" if completion == 100 else ("#d97706" if completion >= 50 else "#4f46e5")

    col_brand, col_spacer, col_user = st.columns([2, 1, 3])

    with col_brand:
        st.markdown("<div class='topnav-brand'>🎓 StudySync</div>", unsafe_allow_html=True)

    with col_user:
        uc1, uc2 = st.columns([3, 2])
        with uc1:
            st.markdown(
                f"<div class='topnav-user'>"
                f"<img src='{avatar_url}' class='topnav-avatar'>"
                f"<div>"
                f"<div class='topnav-name'>{display_name}</div>"
                f"<div class='topnav-handle'>@{user['username']}</div>"
                f"<div class='topnav-progress-wrap'>"
                f"<div class='topnav-progress-fill' style='width:{completion}%;background:{comp_color};'></div>"
                f"</div>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with uc2:
            if not st.session_state.get('confirm_signout'):
                if st.button("Sign Out", use_container_width=True, key="topnav_signout"):
                    st.session_state['confirm_signout'] = True
                    st.rerun()
            else:
                st.caption("Sign out?")
                so1, so2 = st.columns(2)
                with so1:
                    if st.button("Yes", type="primary", use_container_width=True, key="so_yes"):
                        for k in list(st.session_state.keys()):
                            del st.session_state[k]
                        st.rerun()
                with so2:
                    if st.button("No", use_container_width=True, key="so_no"):
                        st.session_state.pop('confirm_signout', None)
                        st.rerun()

    # Horizontal navigation menu
    current_view = st.session_state.get('selected_view', 'Dashboard')
    default_idx  = _VIEW_NAMES.index(current_view) if current_view in _VIEW_NAMES else 0

    selected = option_menu(
        menu_title=None,
        options=_VIEW_NAMES,
        icons=_VIEW_ICONS,
        default_index=default_idx,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "6px 8px",
                "background-color": "white",
                "border-radius": "14px",
                "box-shadow": "0 2px 12px rgba(79,70,229,0.10)",
                "border": "1px solid #e2e8f0",
                "margin-bottom": "4px",
            },
            "icon":       {"font-size": "15px"},
            "nav-link": {
                "font-size": "13px",
                "font-weight": "600",
                "padding": "9px 18px",
                "border-radius": "10px",
                "color": "#64748b",
                "--hover-color": "#eef2ff",
                "text-align": "center",
                "white-space": "nowrap",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                "color": "white",
                "font-weight": "700",
                "border-radius": "10px",
                "box-shadow": "0 4px 14px rgba(79,70,229,0.35)",
            },
        },
    )
    st.session_state['selected_view'] = selected
    return selected


# ── Main routing ─────────────────────────────────────────────────────────────

if not st.session_state.logged_in:
    render_auth()
else:
    user = database.get_user_by_id(st.session_state.user_id)

    from utils import calculate_profile_completion
    completion = calculate_profile_completion(user)

    maybe_show_onboarding(user)
    selected_view = render_topnav(user, completion)

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
