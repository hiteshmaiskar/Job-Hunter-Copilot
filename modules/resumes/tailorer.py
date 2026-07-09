'''
Resume Tailoring Pipeline Orchestrator
Author:     Hitesh Maiskar (extension of original Job-Hunter-Copilot)

This module ties together:
    1. PDF text extraction (extractor.py)
    2. Azure OpenAI tailoring call (azureOpenaiConnections.py)
    3. Tailored PDF generation (generator.py)

It exposes a single function tailor_resume_for_job() that the main bot
(runAiBot.py) calls when a Resume upload section is detected in the modal.

Original project:
    GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn
    License:    GNU Affero General Public License
                https://www.gnu.org/licenses/agpl-3.0.en.html
'''


# ──────────────────────────────────────────────────────────────────────────────
# Imports
# ──────────────────────────────────────────────────────────────────────────────
import os
import re
import tempfile

from config.secrets import (
    azure_tailoring_use_cache,
)

from modules.helpers import print_lg, critical_error_log
from modules.resumes.extractor import get_default_resume_text
from modules.resumes.generator import generate_tailored_pdf

# Azure client import is done lazily inside the function to avoid circular
# imports and to allow the bot to still run when use_resume_tailoring = False.


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _sanitize_filename(name: str, max_len: int = 80) -> str:
    """
    Converts a job title into a safe filename component.

    Replaces any character that is not alphanumeric, a hyphen, or an
    underscore with an underscore, collapses consecutive underscores, and
    trims to ``max_len`` characters.

    Example:
        _sanitize_filename("Senior Python Developer (Remote)") -> "Senior_Python_Developer_Remote"
    """
    sanitized = re.sub(r"[^\w\-]", "_", name)          # replace unsafe chars
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")  # collapse/trim _
    return sanitized[:max_len]


def get_tailored_resume_path(job_id: str, job_title: str) -> str:
    """
    Returns the absolute path for the tailored resume inside the system temp
    directory.

    File name pattern: ``<sanitized_job_title>_<job_id>.pdf``

    Args:
        job_id (str):    LinkedIn job ID (e.g. "3987654321").
        job_title (str): Job title string (e.g. "Senior Python Developer").

    Returns:
        str: Absolute path inside the OS temp dir.

    Example:
        get_tailored_resume_path("3987654321", "Senior Python Developer")
        # -> "/tmp/Senior_Python_Developer_3987654321.pdf"
    """
    safe_title = _sanitize_filename(job_title) if job_title else "Resume"
    filename   = f"{safe_title}_{job_id}.pdf"
    return os.path.join(tempfile.gettempdir(), filename)


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline function
# ──────────────────────────────────────────────────────────────────────────────
def tailor_resume_for_job(
    job_id:          str,
    job_title:       str,
    job_description: str,
    azure_client,           # AzureOpenAI — typed loosely to avoid circular import
) -> str | None:
    """
    Full resume tailoring pipeline for a single job application.

    Steps:
    1. Check cache — if a tailored PDF already exists for this job_id/title
       in the temp dir and azure_tailoring_use_cache is True, return it.
    2. Extract text from the base PDF resume.
    3. Call Azure OpenAI to tailor the resume JSON for this job_description.
    4. Render the JSON as a clean ATS-friendly PDF using reportlab.
    5. Save the PDF to: <temp_dir>/<job_title>_<job_id>.pdf

    On any failure → returns None so the caller can skip the upload and
    keep whatever resume LinkedIn already has on file.

    Args:
        job_id (str):           LinkedIn job ID string (e.g. "3987654321").
        job_title (str):        Job title from the listing (used as filename).
        job_description (str):  Full job description text scraped from LinkedIn.
        azure_client:           AzureOpenAI client from azure_create_client().
                                Pass None to skip tailoring (returns None).

    Returns:
        str | None: Absolute path to the tailored PDF on success, None on failure.

    Example (in runAiBot.py):
        tailored_path = tailor_resume_for_job(job_id, title, description, aiClient)
        if tailored_path:
            upload_resume(modal, tailored_path)
        # else: skip upload — LinkedIn retains the previously uploaded resume
    """
    output_path = get_tailored_resume_path(job_id, job_title)

    try:
        # ── Step 1: Cache check ───────────────────────────────────────────────
        if azure_tailoring_use_cache and os.path.exists(output_path):
            print_lg(
                f"[tailorer] Cache hit — reusing tailored resume for job {job_id}: "
                f"{output_path}"
            )
            return output_path

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
        print_lg("[tailorer] Extracting base resume text...")
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
        print_lg(f"[tailorer] Generating tailored PDF at: {output_path}")
        saved_path = generate_tailored_pdf(resume_data, output_path)

        print_lg(
            f"[tailorer] ✓ Tailored resume ready for job {job_id}: {saved_path}"
        )
        return saved_path

    except Exception as e:
        critical_error_log(
            f"[tailorer] Failed to tailor resume for job {job_id} ({job_title}).", e
        )
        print_lg(
            "[tailorer] Tailoring failed — skipping upload. "
            "LinkedIn will retain the previously uploaded resume."
        )
        return None
