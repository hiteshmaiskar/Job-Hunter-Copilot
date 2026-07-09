'''
Resume Tailoring Pipeline Orchestrator
Author:     Hitesh Maiskar (extension of original Job-Hunter-Copilot)

This module ties together:
    1. PDF text extraction (extractor.py)
    2. Azure OpenAI tailoring call (azureOpenaiConnections.py)
    3. Tailored PDF generation (generator.py)

It exposes a single function tailor_resume_for_job() that the main bot
(runAiBot.py) calls before each Easy Apply resume upload.

Original project:
    GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn
    License:    GNU Affero General Public License
                https://www.gnu.org/licenses/agpl-3.0.en.html
'''


# ──────────────────────────────────────────────────────────────────────────────
# Imports
# ──────────────────────────────────────────────────────────────────────────────
import os

from config.questions import default_resume_path
from config.secrets import (
    azure_tailoring_fallback,
    azure_tailoring_use_cache,
)

from modules.helpers import print_lg, critical_error_log
from modules.resumes.extractor import get_default_resume_text
from modules.resumes.generator import generate_tailored_pdf

# Azure client import is done lazily inside the function to avoid circular
# imports and to allow the bot to still run when use_resume_tailoring = False.


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
TAILORED_RESUMES_DIR = os.path.join("all resumes", "tailored")
"""Base directory where per-job tailored PDFs are saved."""


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────
def get_tailored_resume_path(job_id: str) -> str:
    """
    Returns the expected output path for a tailored resume given a job_id.

    Args:
        job_id (str): LinkedIn job ID (e.g. "3987654321").

    Returns:
        str: Relative path — "all resumes/tailored/<job_id>/resume.pdf"

    Example:
        path = get_tailored_resume_path("3987654321")
        # -> "all resumes/tailored/3987654321/resume.pdf"
    """
    return os.path.join(TAILORED_RESUMES_DIR, str(job_id), "resume.pdf")


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline function
# ──────────────────────────────────────────────────────────────────────────────
def tailor_resume_for_job(
    job_id: str,
    job_description: str,
    azure_client,           # AzureOpenAI — typed loosely to avoid circular import
) -> str:
    """
    Full resume tailoring pipeline for a single job application.

    Steps:
    1. Check cache — if a tailored PDF already exists for this job_id and
       azure_tailoring_use_cache is True, return the cached path immediately.
    2. Extract text from the base PDF resume (all resumes/default/).
    3. Call Azure OpenAI to tailor the resume JSON for this job_description.
    4. Render the JSON as a clean ATS-friendly PDF using reportlab.
    5. Save the PDF to: all resumes/tailored/<job_id>/resume.pdf

    On any failure:
    - If azure_tailoring_fallback is True  → returns default_resume_path (silent fallback).
    - If azure_tailoring_fallback is False → re-raises the exception.

    Args:
        job_id (str):           LinkedIn job ID string (e.g. "3987654321").
        job_description (str):  Full job description text scraped from LinkedIn.
        azure_client:           AzureOpenAI client from azure_create_client().
                                Pass None to skip tailoring and return default.

    Returns:
        str: Absolute path to the tailored resume PDF, or the default resume path
             if tailoring fails/is skipped.

    Example (in runAiBot.py):
        tailored_path = tailor_resume_for_job(job_id, description, azure_client)
        uploaded, resume = upload_resume(modal, tailored_path)
    """
    output_path = get_tailored_resume_path(job_id)
    abs_output  = os.path.abspath(output_path)

    try:
        # ── Step 1: Cache check ───────────────────────────────────────────────
        if azure_tailoring_use_cache and os.path.exists(abs_output):
            print_lg(
                f"[tailorer] Cache hit — reusing tailored resume for job {job_id}: "
                f"{abs_output}"
            )
            return abs_output

        # ── Guard: client must exist ──────────────────────────────────────────
        if azure_client is None:
            raise ValueError(
                "Azure OpenAI client is None. "
                "Cannot tailor resume without a valid client."
            )

        # ── Guard: job description must be meaningful ─────────────────────────
        if not job_description or job_description.strip() in ("", "Unknown"):
            raise ValueError(
                "Job description is empty or 'Unknown'. "
                "Cannot tailor resume without a job description."
            )

        # ── Step 2: Extract base resume text ──────────────────────────────────
        print_lg(f"[tailorer] Extracting base resume text...")
        base_resume_text = get_default_resume_text()
        print_lg(
            f"[tailorer] Extracted {len(base_resume_text)} characters from base resume."
        )

        # ── Step 3: Azure OpenAI — tailor resume JSON ─────────────────────────
        print_lg(f"[tailorer] Calling Azure OpenAI to tailor resume for job {job_id}...")
        from modules.ai.azureOpenaiConnections import azure_tailor_resume
        resume_data = azure_tailor_resume(
            azure_client, base_resume_text, job_description
        )

        if not resume_data or not isinstance(resume_data, dict):
            raise ValueError(
                "Azure OpenAI returned an empty or invalid response. "
                "Cannot generate tailored PDF."
            )

        # ── Step 4: Generate tailored PDF ─────────────────────────────────────
        print_lg(f"[tailorer] Generating tailored PDF at: {abs_output}")
        saved_path = generate_tailored_pdf(resume_data, output_path)

        print_lg(
            f"[tailorer] ✓ Tailored resume ready for job {job_id}: {saved_path}"
        )
        return saved_path

    except Exception as e:
        critical_error_log(
            f"[tailorer] Failed to tailor resume for job {job_id}.", e
        )

        if azure_tailoring_fallback:
            print_lg(
                f"[tailorer] Falling back to default resume: {default_resume_path}"
            )
            return os.path.abspath(default_resume_path)
        else:
            # Re-raise so the caller can decide what to do
            raise
