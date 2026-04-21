import streamlit as st
import os
import sqlite3
from scrape_youtube import extract_video_id, get_transcript, extract_metadata, download_thumbnail
from summarize_text_groq import summarize_text_groq
from summarize_text_openai import summarize_text_openai
from init_db import initialize_database
import bcrypt

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube AI Video Summarizer",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  ALL STYLES — consolidated in one place
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@600;700;800&family=Nunito:wght@300;400;500;600&display=swap');

/* ── Root variables ── */
:root {
    --bg:           #fff8f8;
    --surface:      #ffffff;
    --border:       #f5c6c6;
    --border-strong:#e89090;
    --sidebar-bg:   #f2f2f2;
    --sidebar-text: #1a1010;
    --sidebar-muted:#666666;
    --accent:       #c0392b;
    --accent-hover: #a93226;
    --accent-light: #fdecea;
    --text:         #1a1010;
    --muted:        #7a5555;
    --success:      #16a34a;
    --radius:       12px;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.block-container {
    max-width: 860px;
    margin: auto;
    padding: 2.5rem 2rem;
}

/* ── Hide default streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
/* Hide only deploy button — do NOT hide toolbar or header (breaks sidebar toggle) */
.stDeployButton { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: 1px solid #ddd;
}
[data-testid="stSidebar"] * {
    color: #1a1010 !important;
}
[data-testid="stSidebar"] a {
    color: #c0392b !important;
}

/* ── Sidebar welcome box ── */
.sidebar-welcome {
    background: #fff;
    border: 1.5px solid #f5c6c6;
    border-top: 4px solid #c0392b;
    border-radius: var(--radius);
    padding: 1.3rem 1rem 1rem;
    text-align: center;
    margin-bottom: 0.6rem;
    box-shadow: 0 2px 8px rgba(192,57,43,0.1);
}
.sidebar-username {
    font-family: 'Raleway', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #c0392b;
}

/* ── Sidebar buttons — visible on light grey ── */
[data-testid="stSidebar"] div.stButton > button {
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] div.stButton > button * {
    color: #ffffff !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: var(--accent-hover) !important;
}

/* ── Sidebar history expanders ── */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #f5c6c6 !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem;
}

/* ── App header banner ── */
.app-header {
    background: linear-gradient(135deg, #c0392b 0%, #a93226 60%, #922b21 100%);
    border-radius: var(--radius);
    padding: 2.2rem 2rem 1.8rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.app-header::before {
    content: '';
    position: absolute;
    top: -50px; right: -50px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.app-header h1 {
    font-family: 'Raleway', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    margin: 0 0 0.3rem !important;
    letter-spacing: -0.3px;
    color: #ffffff !important;
}
.app-header p {
    color: rgba(255,255,255,0.7) !important;
    font-size: 0.95rem;
    font-weight: 300;
    margin: 0;
}

/* ── Section labels ── */
.section-title {
    font-family: 'Raleway', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--accent);
    margin: 1.4rem 0 0.5rem;
}

/* ── Cards (video info) ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(192,57,43,0.06);
}
.card-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.3rem;
}
.card-value {
    font-size: 0.97rem;
    font-weight: 400;
    color: var(--text);
}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 0.95rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(192,57,43,0.1) !important;
}

/* ── Buttons ── */
div.stButton > button {
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.8rem !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.2px;
}
div.stButton > button:hover {
    background: var(--accent-hover) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(192,57,43,0.3) !important;
}

/* ── Summary output box ── */
.summary-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: var(--radius);
    padding: 1.6rem 1.8rem;
    line-height: 1.85;
    font-size: 0.97rem;
    color: var(--text);
    margin-top: 0.8rem;
    box-shadow: 0 1px 4px rgba(192,57,43,0.06);
}

/* ── Auth pages ── */
.auth-header {
    font-family: 'Raleway', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    text-align: center;
    color: var(--accent);
    margin-bottom: 0.3rem;
}
.auth-sub {
    text-align: center;
    color: var(--muted);
    font-size: 0.9rem;
    margin-bottom: 2rem;
}
.auth-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.5rem 0;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: 'Nunito', sans-serif !important;
}

/* ── Progress bar ── */
[data-testid="stProgress"] > div > div {
    background: var(--accent) !important;
    border-radius: 99px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  DATABASE HELPERS
# ─────────────────────────────────────────────
if "db_initialized" not in st.session_state:
    initialize_database()
    st.session_state["db_initialized"] = True

def get_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def get_languages():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT name FROM languages")
    langs = [row[0] for row in c.fetchall()]
    conn.close()
    return langs

def save_summary(username, url, summary, title):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO summaries (username, url, summary, title) VALUES (?, ?, ?, ?)",
        (username, url, summary, title)
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────
for key, default in [
    ("authenticated", False),
    ("username", ""),
    ("page", "login"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────────
#  AUTH PAGES
# ─────────────────────────────────────────────
def login():
    st.markdown("<div class='auth-header'>▶ YouTube AI Video Summarizer</div>", unsafe_allow_html=True)
    st.markdown("<div class='auth-sub'>Sign in to your YouTube AI Video Summarizer account</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if st.button("Sign In", use_container_width=True):
            user = get_user(username)
            if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["page"] = "main"
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown("<hr class='auth-divider'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#7a5555; font-size:0.9rem;'>New here?</p>", unsafe_allow_html=True)
        if st.button("Create an Account", use_container_width=True):
            st.session_state["page"] = "create_account"
            st.rerun()


def create_account():
    st.markdown("<div class='auth-header'>▶ Create Account</div>", unsafe_allow_html=True)
    st.markdown("<div class='auth-sub'>Join YouTube AI Video Summarizer and start summarizing</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        new_username = st.text_input("Choose a Username", placeholder="e.g. john_doe")
        new_password = st.text_input("Choose a Password", type="password", placeholder="Min. 6 characters")

        if st.button("Sign Up", use_container_width=True):
            if get_user(new_username):
                st.error("Username already taken.")
            elif new_username and new_password:
                if add_user(new_username, new_password):
                    st.success("Account created! Please sign in.")
                    st.session_state["page"] = "login"
                    st.rerun()
                else:
                    st.error("Failed to create account.")
            else:
                st.error("Please fill in all fields.")

        st.markdown("<hr class='auth-divider'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#7a5555; font-size:0.9rem;'>Already have an account?</p>", unsafe_allow_html=True)
        if st.button("Back to Sign In", use_container_width=True):
            st.session_state["page"] = "login"
            st.rerun()


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────

@st.dialog("📄 Full Summary", width="large")
def show_summary_popup(title, summary, url):
    st.markdown(f"### {title}")
    st.markdown(f"[▶ Watch on YouTube]({url})")
    st.markdown("<hr style='border:none; border-top:1px solid #f5c6c6; margin:0.8rem 0;'>", unsafe_allow_html=True)
    st.markdown(f"<div class='summary-box'>{summary}</div>", unsafe_allow_html=True)
    
def render_sidebar():
    st.sidebar.markdown(
        f"""
        <div class='sidebar-welcome'>
            <div style='font-size:1.5rem; margin-bottom:0.4rem; color:#c0392b;'>▶</div>
            <div class='sidebar-username'>{st.session_state['username']}</div>
            <div style='font-size:0.75rem; color:#888; margin-top:0.2rem;'>Signed in</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.sidebar.button("Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.session_state["page"] = "login"
        # Clear last summary so it doesn't show after re-login
        for key in ["last_summary", "last_title", "last_url"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.sidebar.markdown("<hr style='border:none; border-top:1px solid #ddd; margin:0.8rem 0;'>", unsafe_allow_html=True)
    st.sidebar.markdown(
        "<p style='font-size:0.68rem; letter-spacing:2px; text-transform:uppercase; color:#c0392b; font-weight:700; margin:0.4rem 0 0.5rem;'>Recent Summaries</p>",
        unsafe_allow_html=True
    )

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "SELECT url, title, summary, timestamp FROM summaries WHERE username = ? ORDER BY timestamp DESC",
        (st.session_state["username"],)
    )
    rows = c.fetchall()
    conn.close()

    if rows:
        for url, title, summary, timestamp in rows[:5]:
            with st.sidebar.expander(f"{title or 'Video'} · {timestamp.split()[0]}", expanded=False):
                st.markdown(f"[▶ Watch on YouTube]({url})", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='font-size:0.82rem; color:#666; margin-top:0.4rem;'>{summary[:180]}...</div>",
                    unsafe_allow_html=True
                )
                if st.button("View Full Summary", key=f"view_{url}_{timestamp}"):
                    show_summary_popup(title, summary, url)
    else:
        st.sidebar.markdown(
            "<div style='color:#888; font-size:0.85rem; text-align:center; padding:1rem 0;'>No summaries yet.<br>Paste a URL to get started!</div>",
            unsafe_allow_html=True
        )




# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
def main_app():
    if not st.session_state["authenticated"]:
        login()
        return

    render_sidebar()
    

    # ── Header ──
    st.markdown("""
    <div class='app-header'>
        <h1>▶ YouTube AI Video Summarizer</h1>
        <p>Paste any YouTube link and get an instant AI-powered summary</p>
    </div>
    """, unsafe_allow_html=True)

    # ── URL Input ──
    st.markdown("<div class='section-title'>🔗 Video URL</div>", unsafe_allow_html=True)
    url = st.text_input("Video URL", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")

    # ── Options row ──
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='section-title'>🌐 Language</div>", unsafe_allow_html=True)
        language = st.selectbox("Language", get_languages(), label_visibility="collapsed")
    with col2:
        st.markdown("<div class='section-title'>📏 Summary Type</div>", unsafe_allow_html=True)
        size_option = st.selectbox(
            "Summary Type",
            options=["Short (100-200 words)", "Medium (200-400 words)", "Long (400-600 words)", "Topic Based Summary"],
            index=3,
            label_visibility="collapsed"
        )

    size_map = {
        "Short (100-200 words)":  "short",
        "Medium (200-400 words)": "medium",
        "Long (400-600 words)":   "long",
        "Topic Based Summary":    "topic"
    }
    st.session_state["summary_size"] = size_map[size_option]

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Summarize Button ──
    if st.button("▶  Generate Summary"):
        if not url:
            st.warning("Please enter a YouTube URL to continue.")
        else:
            with st.spinner("Fetching video info..."):
                title, channel = extract_metadata(url)
                video_id = extract_video_id(url)
                download_thumbnail(video_id)

            st.markdown("<div class='section-title'>🎬 Video Info</div>", unsafe_allow_html=True)
            colA, colB = st.columns([1.2, 1])
            with colA:
                st.markdown(f"""
                <div class='card'>
                    <div class='card-label'>Title</div>
                    <div class='card-value'>{title}</div>
                    <div class='card-label' style='margin-top:1rem;'>Channel</div>
                    <div class='card-value'>{channel}</div>
                </div>
                """, unsafe_allow_html=True)
            with colB:
                st.image(os.path.join(os.getcwd(), "thumbnail.jpg"), use_container_width=True)

            st.markdown("<div class='section-title'>📝 Summary</div>", unsafe_allow_html=True)
            progress_bar = st.progress(0)
            status_text  = st.empty()

            def update_progress(current, total, message):
                pct = int((current / total) * 100) if total > 0 else 0
                progress_bar.progress(pct)
                status_text.markdown(
                    f"<span style='color:#7a5555; font-size:0.85rem;'>⏳ {message} — {pct}%</span>",
                    unsafe_allow_html=True
                )

            use_timestamps = st.session_state["summary_size"] == "topic"
            transcript = get_transcript(video_id, include_timestamps=use_timestamps)

            # Groq  / OpenAI (swap as needed). Now OpenAI is active
            
            # summary = summarize_text_groq(transcript, lang=language, size=st.session_state["summary_size"])
            summary = summarize_text_openai(transcript, lang=language, size=st.session_state["summary_size"])

            progress_bar.progress(100)
            status_text.markdown(
                "<span style='color:#16a34a; font-size:0.85rem;'>✅ Summary complete!</span>",
                unsafe_allow_html=True
            )

            with st.container(border=True):
                st.markdown(summary)
            save_summary(st.session_state["username"], url, summary, title)
            st.success("Summary saved to your history!")


# ─────────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────────
if st.session_state["page"] == "login":
    login()
elif st.session_state["page"] == "create_account":
    create_account()
elif st.session_state["page"] == "main":
    main_app()