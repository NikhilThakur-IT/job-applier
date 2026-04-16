import io
import os
import tempfile
from typing import Optional

import uvicorn
from docx import Document
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.analyser import analyse_and_tailor
from services.database import (
    delete_application,
    get_all_applications,
    get_application,
    init_db,
    save_application,
    update_application_status,
)
from services.job_scraper import scrape_job_posting
from services.resume_parser import parse_resume

app = FastAPI(title="Job Applier")


@app.on_event("startup")
def startup():
    init_db()


@app.post("/api/analyse")
async def analyse(
    resume: UploadFile = File(...),
    job_url: str = Form(...),
    job_title: str = Form(""),
    company: str = Form(""),
):
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

    # Auto-save to dashboard
    app_id = save_application(
        job_title=job_title or "Untitled Position",
        company=company or "",
        job_url=job_url,
        rating=result["rating"],
        explanation=result["explanation"],
        tailored_resume=result["tailored_resume"],
    )
    result["id"] = app_id

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


# --- Dashboard API ---

@app.get("/api/applications")
async def list_applications():
    return get_all_applications()


@app.get("/api/applications/{app_id}")
async def get_app(app_id: int):
    app_data = get_application(app_id)
    if not app_data:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_data


class StatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


@app.patch("/api/applications/{app_id}")
async def update_app(app_id: int, update: StatusUpdate):
    update_application_status(app_id, update.status, update.notes)
    return get_application(app_id)


@app.delete("/api/applications/{app_id}")
async def delete_app(app_id: int):
    delete_application(app_id)
    return {"ok": True}


# Serve static files (must be last)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
