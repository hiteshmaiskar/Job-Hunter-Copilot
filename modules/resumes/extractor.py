'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

Support me: https://github.com/sponsors/GodsScion

'''


# ──────────────────────────────────────────────────────────────────────────────
# Original imports (preserved)
# ──────────────────────────────────────────────────────────────────────────────
from config.personals import *
from config.questions import default_resume_path


# ──────────────────────────────────────────────────────────────────────────────
# New imports for PDF text extraction (Resume Tailoring Feature)
# ──────────────────────────────────────────────────────────────────────────────
import os

try:
    import pdfplumber                   # pip install pdfplumber
    _PDFPLUMBER_AVAILABLE = True
except ImportError:
    _PDFPLUMBER_AVAILABLE = False


# ──────────────────────────────────────────────────────────────────────────────
# PDF Text Extractor
# ──────────────────────────────────────────────────────────────────────────────
def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts plain text from a PDF file using pdfplumber.

    Reads every page of the PDF and concatenates the text. Used to feed the
    base resume content to Azure OpenAI for resume tailoring.

    Args:
        pdf_path (str): Absolute or relative path to the PDF file.
                        Example: "all resumes/default/resume.pdf"

    Returns:
        str: Extracted plain text from all pages of the PDF.
             Returns an empty string if extraction fails or pdfplumber is not installed.

    Raises:
        FileNotFoundError: If the PDF file does not exist at the given path.

    Example:
        text = extract_text_from_pdf("all resumes/default/resume.pdf")
        print(text[:500])  # preview first 500 chars
    """
    # Resolve path
    abs_path = os.path.abspath(pdf_path)

    if not os.path.exists(abs_path):
        raise FileNotFoundError(
            f"Resume PDF not found at: {abs_path}\n"
            f"Please ensure your base resume is placed in 'all resumes/default/'"
        )

    if not _PDFPLUMBER_AVAILABLE:
        raise ImportError(
            "pdfplumber is not installed. Run: pip install pdfplumber\n"
            "Or activate your virtual environment and run: pip install pdfplumber"
        )

    extracted_pages = []

    with pdfplumber.open(abs_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text.strip())
            else:
                # Some PDF pages may be image-based — log a warning
                print(
                    f"[extractor] Warning: Page {page_num} of '{pdf_path}' "
                    "returned no text (may be image-based)."
                )

    full_text = "\n\n".join(extracted_pages)

    if not full_text.strip():
        raise ValueError(
            f"No text could be extracted from: {abs_path}\n"
            "The PDF may be image-based (scanned). "
            "Please use a text-based PDF resume."
        )

    return full_text


def get_default_resume_text() -> str:
    """
    Convenience function to extract text from the default resume path
    as configured in config/questions.py (default_resume_path).

    First tries the configured default_resume_path, then auto-discovers
    the first PDF found inside 'all resumes/default/'.

    Returns:
        str: Extracted plain text from the default base resume.

    Example:
        base_text = get_default_resume_text()
    """
    # First try the configured path
    try:
        return extract_text_from_pdf(default_resume_path)
    except FileNotFoundError:
        pass

    # Fallback: find first PDF in 'all resumes/default/'
    default_dir = os.path.join("all resumes", "default")
    if os.path.isdir(default_dir):
        for filename in os.listdir(default_dir):
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(default_dir, filename)
                print(f"[extractor] Using discovered base resume: {pdf_path}")
                return extract_text_from_pdf(pdf_path)

    raise FileNotFoundError(
        f"No PDF resume found in '{default_dir}'. "
        "Please place your base resume PDF in 'all resumes/default/'."
    )
