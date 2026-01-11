import streamlit as st, os, csv, pandas as pd
from user_auth import authenticate_user

# ---------------- LOGIN STATE ----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

ORG_URN = "urn:li:organization:109573414"
ACCESS_TOKEN = " AQX8EopOhqQwRZUQew2ULpX1hZqCo9gmfyg7_hxU5QOolLHviBP-6EmPEJqM5K0MxvIDSK4YjxXCHzXvvzgTa8VkXuF_JbjSZ8UZpK8hisJ3mcYXScCEVc9FxZWNV3JhSUjlc9IA2hiEUCfmJrVRgkuOmdLlzbcdM24qhL9rSgwRGLrGHopDhryl9CXT5qkVCaDm-d71KjFVvwhqiPjs-78K-ic_t2byfLbs4norLAVsVFo1pTp-a4LauffXw3eaFz2NRef7p49dRzj0hLMYLEjg-vA2lqbVLZTJV2k3uurFvrACIHflBbqqn88t54ptwLFp8w6M-UZ1hdVYJvGw11vsxOmJng"
job_post_file = "/Users/satya/hr_chatbot/output/job_post.csv"
positions_file = "/Users/satya/hr_chatbot/output/parsed_resumes.csv"

# ---------------- AGENT LAYER (NON-INTRUSIVE) ----------------

class HRChatAgent:
    def __init__(self):
        self.tools = {
            "JOB_POST": self.job_post_agent,
            "SCAN_RESUME": self.scan_resume_agent,
            "SHOW_OPEN_POSITIONS": self.show_open_positions_agent,
            "END_CHAT": self.end_chat_agent
        }

    def run(self, intent: str):
        handler = self.tools.get(intent, self.unknown_agent)
        return handler()

    def job_post_agent(self):
        return {
            "action": "JOB_POST",
            "message": "📝 Agent activated job posting capability."
        }

    def scan_resume_agent(self):
        return {
            "action": "SCAN_RESUME",
            "message": "📄 Agent activated resume scanning capability."
        }

    def show_open_positions_agent(self):
        return {
            "action": "SHOW_OPEN_POSITIONS",
            "message": "📋 Here are the open positions:"
        }

    def end_chat_agent(self):
        return {
            "action": "END_CHAT",
            "message": "👋 Agent decided to end the chat."
        }

    def unknown_agent(self):
        return {
            "action": "UNKNOWN",
            "message": "❓ Agent could not determine a valid action."
        }

agent = HRChatAgent()
# ---------------- LOGIN UI ----------------
def login_ui():
    st.set_page_config(page_title="HR Chatbot Login", layout="centered")
    st.title("🔐 HR Chatbot Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        user = authenticate_user(username, password)
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.success(f"Welcome {user['full_name']} 👋")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

if not st.session_state.authenticated:
    login_ui()
    st.stop()
# ---------------- CHATBOT UI ----------------
st.sidebar.success(f"Logged in as {st.session_state.user['full_name']}")

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()
st.set_page_config(page_title="HR Chatbot", layout="centered")
st.title("🤖 HR Assistant Chatbot")

if "intent" not in st.session_state:
    st.session_state.intent = None

if "messages" not in st.session_state:
    st.session_state.messages = []

def detect_intent(user_input: str) -> str:
    text = user_input.lower()
    if "job" in text or "post" in text:
        return "JOB_POST"
    if "resume" in text or "scan" in text or "cv" in text:
        return "SCAN_RESUME"
    if "end" in text or "exit" in text or "quit" in text:
        return "END_CHAT"
    if "open positions" in text or "show open positions" in text or "open list" in text:
        return "SHOW_OPEN_POSITIONS"
    return "UNKNOWN"

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.intent != "END_CHAT":
    user_input = st.chat_input("Type: 'Post Job' or 'Scan Resume'")

    if user_input:
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        intent = detect_intent(user_input)
        st.session_state.intent = intent

        agent_result = agent.run(intent)
        st.session_state.messages.append(
            {"role": "assistant", "content": agent_result["message"]}
        )

        st.rerun()

if st.session_state.intent == "JOB_POST":
    with st.chat_message("assistant"):
        with st.form("job_post_form"):
            job_description = st.text_area(
                "Job Description",
                placeholder="Enter job role, skills, experience..."
            )
            job_skills = st.text_area(
                "Job skills required",
                placeholder="Enter job role, skills, experience..."
            )
            submitted = st.form_submit_button("Submit Job Post")

        if submitted:
            from linkedin_api import publish_linkedin_post
            try:
                response = publish_linkedin_post(
                    ORG_URN,
                    ACCESS_TOKEN,
                    job_description
                )
                file_exists = os.path.isfile(job_post_file)
                os.makedirs(os.path.dirname(job_post_file), exist_ok=True)
                with open(job_post_file, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["job_description", "job_skills", "job_post_id", "status"])
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow({
                        "job_description": job_description,
                        "job_skills": job_skills,
                        "job_post_id": response.get("post_id"),
                        "status": "open"
                    })

                st.success("✅ Job posted successfully on LinkedIn!")

                st.json(response)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": "🎉 Job successfully posted on LinkedIn."
                    }
                )

            except Exception as e:
                st.error(f"❌ Error posting job: {e}")

elif st.session_state.intent == "SCAN_RESUME":
    with st.chat_message("assistant"):
        from resume_parser import parse_resume, resume_path
        try:
            parsed_data = parse_resume(resume_path)
            file_exists = os.path.isfile(positions_file)
            os.makedirs(os.path.dirname(positions_file), exist_ok=True)
            with open(positions_file, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Name", "email", "phone", "skills"])
                if not file_exists:
                    writer.writeheader()
                writer.writerow({
                    "Name": parsed_data.get("name"),
                    "email": parsed_data.get("email"),
                    "phone": parsed_data.get("phone"),
                    "skills": parsed_data.get("skills")
                })
            st.warning("⚠️ Please upload a resume file.")
            st.success("✅ Resume parsed successfully!")
            st.json(parsed_data)
            st.session_state.messages.append({
                "role": "assistant",
                "content": "📄 Resume parsed successfully."
            })
        except Exception as e:
            st.error(f"❌ Error parsing resume: {e}")

elif st.session_state.intent == "SHOW_OPEN_POSIPTIONS":
    with st.chat_message("assistant"):
        try:
            file_exists = os.path.isfile(job_post_file)
            if file_exists:
                st.success("✅ Open positions found!")
                df = pd.read_csv(job_post_file)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "📋 Here are the open positions:"
                })
                open_list = pd.DataFrame(df).filter(items=["job_post_id"]).where(df['status'] == "open")
                st.table(open_list)
            else:
                st.warning("⚠️ No open positions found.")
        except Exception as e:
            st.error(f"❌ Error retrieving open positions: {e}")

elif st.session_state.intent == "END_CHAT":
    with st.chat_message("assistant"):
        st.markdown("👋 Thank you for using the HR Assistant Chatbot. Goodbye!")