import docx2txt, re, spacy
from pdfminer.high_level import extract_text

def extract_resume_text(file_path):
    if file_path.endswith(".pdf"):
        return extract_text(file_path)
    elif file_path.endswith(".docx"):
        return docx2txt.process(file_path)
    else:
        raise ValueError("Unsupported file format")

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

resume_path = "/Users/satya/hr_chatbot/resume/resume.pdf" 
if __name__ == "__main__":
    parsed_data = parse_resume(resume_path)
    print(parsed_data)