import pandas as pd, re, ast, streamlit as st
from googleapiclient.discovery import build
from gservice import get_drive_service
from match_profiles import rank_resumes

scopes = [
    scope.strip()
    for scope in st.secrets["GOOGLE"]["scope"].split(",")
]
spreadsheet_id = st.secrets["GOOGLE"]["spreadsheet_id"]
resume_sheet_range = st.secrets["GOOGLE"]["resume_sheet_range"]
job_sheet_range = st.secrets["GOOGLE"]["job_sheet_range"]

creds = get_drive_service()

def generate_proxy_labels(df, relevance_threshold=80):
    """
    Creates pseudo ground-truth relevance labels
    """
    df = df.copy()
    df["is_relevant"] = (df["matching_score"] >= relevance_threshold).astype(int)
    return df

def precision_at_k(ranked_df, k=5):
    top_k = ranked_df.head(k)
    return top_k["is_relevant"].sum() / k

def recall_at_k(ranked_df, k=5):
    total_relevant = ranked_df["is_relevant"].sum()
    retrieved_relevant = ranked_df.head(k)["is_relevant"].sum()

    return retrieved_relevant / total_relevant if total_relevant else 0.0

def f1_at_k(ranked_df, k=5):
    p = precision_at_k(ranked_df, k)
    r = recall_at_k(ranked_df, k)
    return (2 * p * r / (p + r)) if (p + r) else 0.0

def evaluate_ranking(
    job_post_id,
    relevance_threshold=80,
    k=5,
    **rank_kwargs
):
    ranked_df = rank_resumes(job_post_id=job_post_id, **rank_kwargs)

    ranked_df = generate_proxy_labels(ranked_df, relevance_threshold)

    return {
        "precision@k": precision_at_k(ranked_df, k),
        "recall@k": recall_at_k(ranked_df, k),
        "f1@k": f1_at_k(ranked_df, k),
        "total_relevant": ranked_df["is_relevant"].sum()
    }

def mandatory_skill_recall(ranked_df, mandatory_skills):
    ranked_df["has_mandatory"] = ranked_df["matched_skills"].apply(
        lambda x: all(s in x for s in mandatory_skills)
    )
    return ranked_df["has_mandatory"].mean()


metrics = evaluate_ranking(
    job_post_id="7422102829710102528",
    relevance_threshold=75,
    k=5,
    spreadsheet_id=spreadsheet_id,
    job_sheet_range=job_sheet_range,
    resume_sheet_range=resume_sheet_range,
    credentials=creds,
    top_n=20
)

print(metrics)
