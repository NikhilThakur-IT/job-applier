import json
import os

import anthropic


def analyse_and_tailor(resume_text: str, job_description: str) -> dict:
    """Rate compatibility and generate a tailored resume.

    Returns dict with keys: rating (int 1-10), explanation (str), tailored_resume (str).
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

    prompt = f"""You are a professional resume consultant. You have been given a candidate's resume/experience and a job description.

Do two things:

1. **Rate compatibility** from 1 to 10 (10 = perfect match). Consider skills, experience level, industry fit, and qualifications.

2. **Tailor the resume** to this specific job. You MUST only use information that exists in the candidate's resume — do not invent, fabricate, or embellish any skills, experiences, or achievements. Reorder, rephrase, and emphasise the most relevant parts. Use Australian English spelling.

Output valid JSON with exactly these keys:
- "rating": integer 1-10
- "explanation": a short paragraph explaining the rating
- "tailored_resume": the full tailored resume as plain text, formatted with clear sections

---
CANDIDATE RESUME:
{resume_text}

---
JOB DESCRIPTION:
{job_description}
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text

    # Extract JSON from the response
    try:
        # Try direct parse first
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to find JSON block in markdown
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        raise ValueError("Could not parse AI response as JSON")
