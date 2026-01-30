import pandas as pd, re, ast
from googleapiclient.discovery import build

SKILL_ALIASES = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "mysql": "sql",
    "postgresql": "sql",
    "py": "python",
}

def parse_resume_skills(skill_value):
    """
    Handles:
    - Stringified Python lists
    - Stringified Python sets
    - Normal comma separated strings
    """
    if pd.isna(skill_value):
        return set()

    # Case 1: Proper Python literal (list / set)
    try:
        parsed = ast.literal_eval(skill_value)
        if isinstance(parsed, (list, set, tuple)):
            tokens = parsed
        else:
            tokens = [skill_value]
    except Exception:
        # Case 2: Fallback — clean string manually
        cleaned = re.sub(r"[\[\]\{\}']", "", skill_value)
        tokens = re.split(r"[,\|\n/•]+", cleaned)

    skills = set()
    for t in tokens:
        t = str(t).strip().lower()
        if not t:
            continue
        skills.add(SKILL_ALIASES.get(t, t))

    return skills

def parse_job_skills(skill_str):
    if pd.isna(skill_str):
        return set()

    tokens = re.split(r"[,\|\n/•]+", skill_str.lower())
    skills = set()

    for t in tokens:
        t = t.strip()
        if not t:
            continue
        skills.add(SKILL_ALIASES.get(t, t))

    return skills

def read_sheet_as_dataframe(service, spreadsheet_id, sheet_range):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_range
    ).execute()

    rows = result.get("values", [])
    if not rows:
        return pd.DataFrame()

    header = rows[0]
    data = rows[1:]

    return pd.DataFrame(data, columns=header)
# -------------------------------
# Utility function to normalize skills
# -------------------------------
def compute_match_score(job_skills, resume_skills):
    matched = job_skills & resume_skills
    match_count = len(matched)

    score = (match_count / len(job_skills)) * 100 if job_skills else 0.0

    return (
        round(score, 2),
        match_count,
        ", ".join(sorted(matched))
    )

# -------------------------------
# Core ranking function
# -------------------------------
def rank_resumes(
    job_post_id,
    spreadsheet_id,
    job_sheet_range,
    resume_sheet_range,
    credentials,
    top_n=5
):
    service = build("sheets", "v4", credentials=credentials)

    job_df = read_sheet_as_dataframe(service, spreadsheet_id, job_sheet_range)
    resume_df = read_sheet_as_dataframe(service, spreadsheet_id, resume_sheet_range)

    job_df["job_post_id"] = job_df["job_post_id"].astype(str)
    job_row = job_df[job_df["job_post_id"].str.strip() == str(job_post_id).strip()]
    if job_row.empty:
        raise ValueError("Job post ID not found")

    job_skills = parse_job_skills(job_row.iloc[0]["job_skills"])

    # Parse resume skills properly
    resume_df["resume_skills"] = resume_df["skills"].apply(parse_resume_skills)

    # Compute scores
    resume_df[["matching_score", "matched_count", "matched_skills"]] = resume_df["resume_skills"].apply(lambda x: pd.Series(compute_match_score(job_skills, x)))
    resume_df = resume_df.sort_values(by=["matching_score", "matched_count", "name"], ascending=[False, False, True])
    resume_df["rank"] = (resume_df["matching_score"].rank(method="dense", ascending=False).astype(int))

    # Rank
    ranked = resume_df.head(top_n)

    return ranked[["rank", "name", "email", "phone", "matching_score", "matched_count", "matched_skills"]]
# -------------------------------
# Example execution
# -------------------------------
if __name__ == "__main__":
    from gservice import get_gsheet_credentials

    creds = get_gsheet_credentials(st.secrets["google_service_account_file"])

    ranked_resumes = rank_resumes(
        job_post_id="JOB123",
        spreadsheet_id=st.secrets["spreadsheet_id"],
        job_sheet_range="JobPosts!A:D",
        resume_sheet_range="Resumes!A:D",
        credentials=creds,
        top_n=5
    )

    print(ranked_resumes)