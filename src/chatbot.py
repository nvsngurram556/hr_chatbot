import streamlit as st

# ---------------- Streamlit Setup ---------------- #
ORG_URN = "urn:li:organization:109573414"
# Your Developer Access Token (must have the w_organization_social permission)
ACCESS_TOKEN = "AQXZ9DGnlPHsZImVe_4T_aqzij_i1Q1IpBtSRifpdO3xknIgHccIIHFg3HowXE4YO5LUFJ1Fw4iaHtR5Fw2mmKrcTkmvThJMVWRxj-CnCtBtKJxapdil7owOU9gLyG1DaRWEwZ5T_kNJWrPW_4yBn9GdW0s1b-yiDQkaPFNJJbbuWwaID0GD1Dl7I6y8v4nXBkWgepjI5POas0_g8yWJjX6oXHu4lIzx5jH22sTxv4AVmnojqQuzE2Rsdyox2g3dse5MZlbiPVB2Esh5k81gecNcu7nFeheUSGVanyjHpfqQThAF9fEBPvGSR8aI61htlv549qf0WLDCWl8xPxjhBx7v6_2Ozg"

st.set_page_config(page_title="HR Chatbot", layout="centered")
st.title("🤖 HR Assistant Chatbot")

# ---------------- Session State ---------------- #

if "intent" not in st.session_state:
    st.session_state.intent = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- Helper: Intent Detection ---------------- #

def detect_intent(user_input: str) -> str:
    text = user_input.lower()
    if "job" in text or "post" in text:
        return "JOB_POST"
    if "resume" in text or "scan" in text or "cv" in text:
        return "SCAN_RESUME"
    if "end" in text or "exit" in text or "quit" in text:
        return "END_CHAT"
    return "UNKNOWN"

# ---------------- Display Chat History ---------------- #

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- User Chat Input ---------------- #

if st.session_state.intent != "END_CHAT":
    user_input = st.chat_input("Type: 'Post Job' or 'Scan Resume'")

    if user_input:
        # Store user message
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        intent = detect_intent(user_input)
        st.session_state.intent = intent

        if intent == "JOB_POST":
            assistant_msg = "📝 Please enter the **job description** and click **Submit**."
        elif intent == "SCAN_RESUME":
            assistant_msg = "📄 Please **upload a resume file** and click **Parse Resume**."
        elif intent == "END_CHAT":
            assistant_msg = "👋 Thank you for using the HR Assistant Chatbot. Goodbye!"
        else:
            assistant_msg = "❓ I can help with **Job Posting** or **Resume Scanning**."

        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_msg}
        )

        st.rerun()

# ================= JOB POST FLOW ================= #

if st.session_state.intent == "JOB_POST":
    with st.chat_message("assistant"):
        with st.form("job_post_form"):
            job_description = st.text_area(
                "Job Description",
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

# ================= RESUME PARSER FLOW ================= #

elif st.session_state.intent == "SCAN_RESUME":
    with st.chat_message("assistant"):
        from resume_parser import parse_resume, resume_path
        parsed_data = parse_resume(resume_path)
        try:
            st.warning("⚠️ Please upload a resume file.")
            st.success("✅ Resume parsed successfully!")
            st.json(parsed_data)
            st.session_state.messages.append({
                "role": "assistant",
                "content": "📄 Resume parsed successfully."
            })
        except Exception as e:
            st.error(f"❌ Error parsing resume: {e}")

# ================= END CHAT FLOW ================= #

elif st.session_state.intent == "END_CHAT":
    with st.chat_message("assistant"):
        st.markdown("👋 Thank you for using the HR Assistant Chatbot. Goodbye!")