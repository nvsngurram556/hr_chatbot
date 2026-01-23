import docx2txt
from pdfminer.high_level import extract_text
import re
import os
import csv
import spacy, configparser, streamlit as st

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
base_dir = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(base_dir, "config/config.ini")

config = configparser.ConfigParser()
config.read(CONFIG_PATH)

scopes = [
    scope.strip()
    for scope in config["GOOGLE"]["scope"].split(",")
]
service_account_file = config["GOOGLE"]["service_account_file"]
spreadsheet_id = config["GOOGLE"]["spreadsheet_id"]
resume_sheet_range = config["GOOGLE"]["resume_sheet_range"]
folder_id = config["DRIVE_FOLDERS"]["folder_id"]

creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

def extract_resume_text(file_path=None, file_bytes=None, filename=None):
    """
    Extract text from resume.
    Supports:
    - Local file path
    - In‑memory bytes from Google Drive
    """
    if file_path:
        if file_path.endswith(".pdf"):
            return extract_text(file_path)
        elif file_path.endswith(".docx"):
            return docx2txt.process(file_path)
        else:
            raise ValueError("Unsupported file format")

    if file_bytes and filename:
        if filename.endswith(".pdf"):
            from io import BytesIO
            return extract_text(BytesIO(file_bytes))
        elif filename.endswith(".docx"):
            from io import BytesIO
            return docx2txt.process(BytesIO(file_bytes))
        else:
            raise ValueError("Unsupported file format")

    raise ValueError("Either file_path or file_bytes must be provided")

def extract_email(text):
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    return re.findall(email_pattern, text)

def extract_phone(text):
    phone_pattern = r'(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    return re.findall(phone_pattern, text)

nlp = spacy.load("en_core_web_sm")

def extract_name(text):
    doc = nlp(text[:800])

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            start = ent.start
            end = ent.end

            # Extend right for comma + proper noun
            while end < len(doc):
                if doc[end].text == ",":
                    end += 1
                elif doc[end].pos_ == "PROPN":
                    end += 1
                else:
                    break

            return doc[start:end].text

    return None

SKILLS_DB = [
    "python", "java", "sql", "aws", "docker", "kubernetes",
    "machine learning", "deep learning", "nlp", "pandas",
    "numpy", "tensorflow", "pytorch", "scikit-learn",
    "airflow", "mlflow", "fastapi", "flask"
]

def extract_skills(text):
    text = text.lower()
    found_skills = []
    for skill in SKILLS_DB:
        if skill in text:
            found_skills.append(skill)
    return list(set(found_skills))

def parse_resume(file_path):
    text = extract_resume_text(file_path)

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text)
    }

def parse_resumes_from_drive(folder_id, creds):
    """
    Read all resumes from a Google Drive folder and parse each resume
    """
    service = build("drive", "v3", credentials=creds)

    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)"
    ).execute()

    parsed_resumes = []

    for file in results.get("files", []):
        filename = file["name"].lower()

        if not (filename.endswith(".pdf") or filename.endswith(".docx")):
            continue

        request = service.files().get_media(fileId=file["id"])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)

        text = extract_resume_text(
            file_bytes=fh.read(),
            filename=file["name"]
        )

        resume_data = {
            "name": extract_name(text),
            "email": extract_email(text),
            "phone": extract_phone(text),
            "skills": extract_skills(text)
        }

        parsed_resumes.append(resume_data)

    return parsed_resumes

def save_to_csv(data, csv_file):
    file_exists = os.path.isfile(csv_file)

    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())

        if not file_exists:
            writer.writeheader()   # Write header only once

        writer.writerow(data)

def save_resumes_to_sheet(spreadsheet_id: str, sheet_name: str, resumes: list, credentials_file: str):
    """
    Saves parsed resume data to Google Sheet
    """
    service = build("sheets", "v4", credentials=credentials_file)

    values = []

    for r in resumes:
        values.append([
            r.get("name"),
            ", ".join(r.get("email", [])),
            ", ".join(r.get("phone", [])),
            ", ".join(r.get("skills", []))
        ])

    body = {
        "values": values
    }

    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()



if __name__ == "__main__":
    parsed_data = parse_resumes_from_drive(folder_id, creds)
    save_resumes_to_sheet(
        spreadsheet_id,
        "info",
        parsed_data,
        credentials_file=creds
    )
    print("✅ Resume parsed and saved to Google Sheets successfully.")
    print(len(parsed_data))