from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import io, os
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SERVICE_ACCOUNT_FILE = "/Users/satya/hr_chatbot/src/agent/secrets/poised-graph-470206-f8-cae5285f6afc.json"
folder_id = "1DZqpjkVpMoA3M578oVe8gdaTAQWtJ1y9_AX0LJQHwpkGJlPTdn4YW-plf7LsOpk5QerTQVEC"

def get_drive_service():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    service = build("drive", "v3", credentials=creds)
    return service

def list_files_in_folder(folder_id):
    service = get_drive_service()

    query = f"'{folder_id}' in parents and trashed=false"

    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)"
    ).execute()

    return results.get("files", [])

def download_file(file_id, file_name, save_dir="/Users/satya/hr_chatbot/src/data/resumes/raw"):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)

    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, file_name)

    fh = io.FileIO(file_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    return file_path

def fetch_resumes_from_drive(folder_id):
    files = list_files_in_folder(folder_id)
    downloaded = []

    for f in files:
        if f["name"].endswith((".pdf", ".docx")):
            path = download_file(f["id"], f["name"])
            downloaded.append(path)

    return downloaded



def parse_all_resumes_from_drive(folder_id):
    resume_paths = fetch_resumes_from_drive(folder_id)

    parsed = []
    for path in resume_paths:
        data = parse_resume(path)
        parsed.append(data)

    return parsed