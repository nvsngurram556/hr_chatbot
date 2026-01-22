import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from utils.config_loader import load_config
import streamlit as st
import io, pandas as pd, configparser
import os

config, project_root = load_config()

scope = [
    scope.strip()
    for scope in config["GOOGLE"]["scope"].split(",")
]
spreadsheet_id = config["GOOGLE"]["spreadsheet_id"]
resume_sheet_range = config["GOOGLE"]["resume_sheet_range"]
job_sheet_range = config["GOOGLE"]["job_sheet_range"]
users_sheet_range = config["GOOGLE"]["users_sheet_range"]
folder_id = config["DRIVE_FOLDERS"]["folder_id"]


def get_drive_service():
    config, project_root = load_config()

    scopes = [
        s.strip()
        for s in config["GOOGLE"]["scope"].split(",")
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    return creds


def authenticate_user(input_username, input_password):
    service = build("sheets", "v4", credentials=get_drive_service())

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=users_sheet_range
    ).execute()

    rows = result.get("values", [])

    for row in rows:
        # Defensive checks to avoid index errors
        if len(row) < 3:
            continue

        name = row[0]
        username = row[1]
        password = row[2]
        email = row[3] if len(row) > 3 else None

        if username == input_username and password == input_password:
            return {
                "name": name,
                "username": username,
                "email": email
            }

    return None

if __name__ == "__main__":
   pass