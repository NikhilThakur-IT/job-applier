# Job Applier

A personal tool that tailors your resume to job postings using only your real experience.

## Project Overview

- **User uploads** their resume and work experience (source of truth)
- **User provides** a job posting URL
- **System scrapes** the job description from the URL
- **System rates** compatibility between the user's experience and the job requirements
- **System generates** a tailored resume using *only* experience from the uploaded document — no fabrication

## Key Principles

- **Honesty-first**: The tailored resume must only reference skills, roles, and achievements present in the user's uploaded experience. Never invent or embellish.
- **Single user**: This is a personal tool, not multi-tenant. No auth system beyond basic local access.
- **AU English**: All UI text uses Australian English spelling.

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: Simple HTML/CSS/JS (served by FastAPI)
- **Resume parsing**: python-docx (Word), PyPDF2 (PDF)
- **Job scraping**: BeautifulSoup + requests
- **AI**: Anthropic Claude API for rating and tailoring
- **Output**: Word document (.docx) + copyable plain text

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Then open http://localhost:8000

## Project Structure

```
main.py              — FastAPI app entry point
requirements.txt     — Python dependencies
/static              — Frontend HTML/CSS/JS
/services
  resume_parser.py   — Parse PDF/Word uploads
  job_scraper.py     — Scrape job posting from URL
  analyser.py        — Rate compatibility + tailor resume
```
