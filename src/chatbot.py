import streamlit as st, os, csv, pandas as pd
import gspread, configparser
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from agent import HRChatAgent
from gservice import authenticate_user, get_drive_service
from utils.config_loader import load_config

# Load configuration
config, _ = load_config()

ORG_URN = config["LINKEDIN_AUTH"]["org_urn"]
ACCESS_TOKEN = config["LINKEDIN_AUTH"]["access_token"]
folder_id = config["DRIVE_FOLDERS"]["folder_id"]
sheet_id = config["GOOGLE"]["spreadsheet_id"]
job_sheet_range = config["GOOGLE"]["job_sheet_range"]
resume_sheet_range = config["GOOGLE"]["resume_sheet_range"]
scope = [
    scope.strip()
    for scope in config["GOOGLE"]["scope"].split(",")
]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)
client = gspread.authorize(creds)

# Open Google Sheet
sheet = client.open("candidate_info").worksheet("job")

# ---------------- LOGIN STATE ----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None
# ---------------- FILE PATHS ----------------
agent = HRChatAgent()
# ---------------- LOGIN UI ----------------

def login_ui():
    st.set_page_config(page_title="HR Chatbot Login", layout="centered")
    st.title("🔐 HR Chatbot Login")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        user = authenticate_user(username, password)

        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.success(f"Welcome {user['name']} 👋")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

if not st.session_state.authenticated:
    login_ui()
    st.stop()
# ---------------- CHATBOT UI ----------------
st.sidebar.success(f"Logged in as {st.session_state.user['name']}")

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
    if "job post" in text or "upload job post" in text:
        return "JOB_POST"
    if "resume scan" in text or " resume cv" in text:
        return "SCAN_RESUME"
    if "end" in text or "exit" in text or "quit" in text:
        return "END_CHAT"
    if "open positions" in text or "show open positions" in text or "open list" in text:
        return "SHOW_OPEN_POSITIONS"
    if "match profiles" in text or "rank profiles" in text:
        return "MATCH_PROFILES"
    if "update job status" in text or "close job" in text:
        return "UPDATE_JOB_STATUS"
    return "UNKNOWN"

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.intent != "END_CHAT":
    user_input = st.chat_input("Type: 'job post' or 'resume scan'")

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
                sheet = client.open("candidate_info").worksheet("job")
                sheet.append_row([
                    job_description,
                    job_skills,
                    response.get("post_id"),
                    "open"
                ])
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
        from resume_parser import parse_resumes_from_drive, save_resumes_to_sheet

        try:
            parsed_count = 0
            parsed_resumes = parse_resumes_from_drive(folder_id, creds)
            save_resumes_to_sheet(sheet_id, "info", parsed_resumes, creds)
            parsed_count = len(parsed_resumes)
            if not parsed_count:
                st.warning("⚠️ No resumes were parsed successfully")
                st.stop()

            st.success(f"✅ Parsed {parsed_count} resume(s) successfully")

            st.session_state.messages.append({
                "role": "assistant",
                "content": f"📄 {parsed_count} resumes parsed and saved successfully."
            })

        except Exception as e:
            st.error(f"❌ Error during resume scanning: {e}")

elif st.session_state.intent == "SHOW_OPEN_POSITIONS":
    with st.chat_message("assistant"):
        try:
            service = build("sheets", "v4", credentials=get_drive_service())

            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=job_sheet_range
            ).execute()

            rows = result.get("values", [])

            if not rows:
                st.warning("⚠️ No job data found.")
                st.stop()

            # First row = header
            header = [h.lower() for h in rows[0]]
            data_rows = rows[1:]
            print(header)

            if "status" not in header:
                st.error("❌ 'status' column not found in job sheet")
                st.stop()

            status_index = header.index("status")

            # Convert to DataFrame
            df = pd.DataFrame(data_rows, columns=header)

            # Filter OPEN positions (case-insensitive)
            open_df = df[df["status"].str.lower() == "open"]

            if open_df.empty:
                st.warning("⚠️ No open positions found.")
            else:
                st.success(f"✅ {len(open_df)} open position(s) found!")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "📋 Here are the open positions:"
                })
                st.table(open_df)

        except Exception as e:
            st.error(f"❌ Error retrieving open positions: {e}")

elif st.session_state.intent == "MATCH_PROFILES":
    with st.chat_message("assistant"):
        try:
            job_post_id = st.text_input("Enter Job Post ID to match profiles:")
            if job_post_id:
                from match_profiles import rank_resumes
                ranked_profiles = rank_resumes(
                    job_post_id,
                    sheet_id,
                    job_sheet_range,
                    resume_sheet_range,
                    creds
                )
                if not ranked_profiles.empty:
                    st.success("✅ Profiles matched and ranked successfully!")
                    st.table(ranked_profiles)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "📄 Profiles matched and ranked successfully."
                    })
                else:
                    st.warning("⚠️ No matching profiles found.")
        except Exception as e:
            st.error(f"❌ Error matching profiles: {e}")

elif st.session_state.intent == "UPDATE_JOB_STATUS":
    with st.chat_message("assistant"):
        try:
            job_post_id = st.text_input("Enter Job Post ID to update status:")
            new_status = st.selectbox("Select new status:", ["inprogress", "closed"])

            if job_post_id and new_status:
                service = build("sheets", "v4", credentials=get_drive_service())

                # Read job sheet
                result = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=job_sheet_range
                ).execute()

                rows = result.get("values", [])

                if not rows:
                    st.warning("⚠️ Job sheet is empty.")
                    st.stop()

                header = [h.lower() for h in rows[0]]

                if "job_post_id" not in header or "status" not in header:
                    st.error("❌ Required columns not found (job_post_id / status)")
                    st.stop()

                job_id_index = header.index("job_post_id")
                status_index = header.index("status")

                updated = False

                # Iterate data rows (skip header)
                for idx, row in enumerate(rows[1:], start=2):  # sheet rows start at 1
                    if len(row) > job_id_index and row[job_id_index] == job_post_id:
                        # Update status cell
                        cell_range = f"{job_sheet_range.split('!')[0]}!{chr(65 + status_index)}{idx}"

                        service.spreadsheets().values().update(
                            spreadsheetId=sheet_id,
                            range=cell_range,
                            valueInputOption="RAW",
                            body={"values": [[new_status]]}
                        ).execute()

                        updated = True
                        break

                if updated:
                    st.success(f"✅ Job post {job_post_id} status updated to {new_status}!")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"🔄 Job post {job_post_id} status updated to {new_status}."
                    })
                else:
                    st.warning("⚠️ Job Post ID not found.")

        except Exception as e:
            st.error(f"❌ Error updating job status: {e}")

elif st.session_state.intent == "END_CHAT":
    with st.chat_message("assistant"):
        st.markdown("👋 Thank you for using the HR Assistant Chatbot. Goodbye!")