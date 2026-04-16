import io
import os
import tempfile

import uvicorn
from docx import Document
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.analyser import analyse_and_tailor
from services.job_scraper import scrape_job_posting
from services.resume_parser import parse_resume

app = FastAPI(title="Job Applier")


@app.post("/api/analyse")
async def analyse(resume: UploadFile = File(...), job_url: str = Form(...)):
    # Save uploaded file to temp location
    suffix = os.path.splitext(resume.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await resume.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        resume_text = parse_resume(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse resume: {e}")
    finally:
        os.unlink(tmp_path)

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the resume.")

    try:
        job_description = scrape_job_posting(job_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not scrape job posting: {e}")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the job posting URL.")

    try:
        result = analyse_and_tailor(resume_text, job_description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    return result


class DocxRequest(BaseModel):
    content: str


@app.post("/api/download-docx")
async def download_docx(req: DocxRequest):
    doc = Document()
    for line in req.content.split("\n"):
        doc.add_paragraph(line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=tailored_resume.docx"},
    )


# Serve static files (must be last)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
