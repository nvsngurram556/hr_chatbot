import streamlit as st
import bcrypt
from agent.agent import run_agent

# ===============================
# 🔐 CONFIGURATION
# ===============================

ORG_URN = "urn:li:organization:109573414"
ACCESS_TOKEN = "AQX8EopOhqQwRZUQew2ULpX1hZqCo9gmfyg7_hxU5QOolLHviBP-6EmPEJqM5K0MxvIDSK4YjxXCHzXvvzgTa8VkXuF_JbjSZ8UZpK8hisJ3mcYXScCEVc9FxZWNV3JhSUjlc9IA2hiEUCfmJrVRgkuOmdLlzbcdM24qhL9rSgwRGLrGHopDhryl9CXT5qkVCaDm-d71KjFVvwhqiPjs-78K-ic_t2byfLbs4norLAVsVFo1pTp-a4LauffXw3eaFz2NRef7p49dRzj0hLMYLEjg-vA2lqbVLZTJV2k3uurFvrACIHflBbqqn88t54ptwLFp8w6M-UZ1hdVYJvGw11vsxOmJng"

USERS = {
    "admin": "$2b$12$Kh4nkIDPKFOvcxdhuN2Theqir7gzxlYstA1o6SNo3B26Ie//YRijq",
    "hr_user": "$2b$12$zjA2jxAbjz./iQPXkw.8k.PJDDYcPyqFTBJUjZxmtGIQEfpr3PEja"
}

# ===============================
# 🔐 AUTH
# ===============================

def verify_password(p, h):
    return bcrypt.checkpw(p.encode(), h.encode())

def login(u, p):
    return u in USERS and verify_password(p, USERS[u])

def logout():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ===============================
# 🔐 SESSION INIT
# ===============================

defaults = {
    "logged_in": False,
    "username": None,
    "messages": [],
    "agent_state": {
        "job_id": None,
        "job_description": None,
        "resumes_parsed": False
    }
}

for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ===============================
# 🎨 PAGE
# ===============================

st.set_page_config(page_title="HR Chatbot", layout="centered")
st.title("🤖 HR Assistant Chatbot")

# ===============================
# 🔐 LOGIN
# ===============================

if not st.session_state.logged_in:
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if login(u, p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

# ===============================
# 🚪 LOGOUT
# ===============================

st.sidebar.success(f"👤 {st.session_state.username}")
if st.sidebar.button("Logout"):
    logout()

# ===============================
# 🤖 GREETING (ONCE)
# ===============================

if not st.session_state.messages:
    greeting = f"""
👋 Hi **{st.session_state.username}**

I can help you with:
• Job Posting  
• Resume Parsing  
• Candidate Matching  

How can I assist you today?
"""
    st.session_state.messages.append(
        {"role": "assistant", "content": greeting}
    )

# ===============================
# 💬 CHAT HISTORY
# ===============================

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ===============================
# 💬 USER INPUT → AGENT
# ===============================

user_input = st.chat_input("Ask me anything...")

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.spinner("Thinking..."):
        response = run_agent(
            user_input,
            st.session_state.agent_state
        )

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

    st.rerun()