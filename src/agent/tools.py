from langchain.tools import tool
import json
from linkedin_api import publish_linkedin_post
from agent.matcher import rank_profiles
from google_drive_client import fetch_resumes_from_drive
from resume_parser import parse_resume
folder_id = "1DZqpjkVpMoA3M578oVe8gdaTAQWtJ1y9_AX0LJQHwpkGJlPTdn4YW-plf7LsOpk5QerTQVEC"
ORG_URN = "urn:li:organization:109573414"
ACCESS_TOKEN = "AQX8EopOhqQwRZUQew2ULpX1hZqCo9gmfyg7_hxU5QOolLHviBP-6EmPEJqM5K0MxvIDSK4YjxXCHzXvvzgTa8VkXuF_JbjSZ8UZpK8hisJ3mcYXScCEVc9FxZWNV3JhSUjlc9IA2hiEUCfmJrVRgkuOmdLlzbcdM24qhL9rSgwRGLrGHopDhryl9CXT5qkVCaDm-d71KjFVvwhqiPjs-78K-ic_t2byfLbs4norLAVsVFo1pTp-a4LauffXw3eaFz2NRef7p49dRzj0hLMYLEjg-vA2lqbVLZTJV2k3uurFvrACIHflBbqqn88t54ptwLFp8w6M-UZ1hdVYJvGw11vsxOmJng"   

@tool
def job_post_tool(job_description: str) -> str:
    """Post job and return job id"""

    from datetime import datetime
    import os

    if os.path.exists("data/jobs/job_metadata.json"):
        return "⚠️ A job is already posted. Please update or delete before reposting."
    job_description = f"{job_description}\n\nPosted at: {datetime.utcnow().isoformat()}"
    response = publish_linkedin_post(
        ORG_URN,
        ACCESS_TOKEN,
        job_description
    )

    # 🔴 HANDLE API FAILURE
    if not response or not isinstance(response, dict):
        return "❌ Job post failed (duplicate or API error). Please modify the job description."

    job_id = response.get("id")

    if not job_id:
        return "⚠️ Job posted but LinkedIn did not return a Job ID."

    with open("data/jobs/job_metadata.json", "w") as f:
        json.dump(
            {"job_id": job_id, "description": job_description},
            f
        )

    return f"✅ Job posted on LinkedIn\n🆔 Job ID: {job_id}"


@tool
def resume_parse_tool(query: str) -> str:
    """
    Fetch resumes from Google Drive, parse each resume,
    and save the structured resume data for later matching.
    """
    paths = fetch_resumes_from_drive(folder_id)

    parsed = []
    for path in paths:
        data = parse_resume(path)
        parsed.append(data)

    with open("data/resumes/parsed_resumes.json", "w") as f:
        json.dump(parsed, f)

    return f"📄 Parsed {len(parsed)} resumes successfully"


@tool
def match_profiles_tool(query: str) -> str:
    """Match resumes with job and rank candidates"""
    with open("data/jobs/job_metadata.json") as j:
        job = json.load(j)

    with open("data/resumes/parsed_resumes.json") as r:
        resumes = json.load(r)

    ranked = rank_profiles(job["description"], resumes)

    return "\n".join(
        [f"{i+1}. {c['name']} → Score: {c['score']}"
         for i, c in enumerate(ranked)]
    )