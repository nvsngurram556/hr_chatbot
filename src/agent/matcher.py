from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def rank_profiles(job_desc, resumes, top_k=5):
    job_emb = model.encode(job_desc, convert_to_tensor=True)

    scored = []
    for r in resumes:
        skills = " ".join(r.get("skills", []))
        emb = model.encode(skills, convert_to_tensor=True)
        score = util.cos_sim(job_emb, emb).item()

        scored.append({
            "name": r.get("name"),
            "email": r.get("email"),
            "score": round(score, 3)
        })

    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]