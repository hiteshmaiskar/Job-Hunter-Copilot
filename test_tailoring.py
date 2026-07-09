"""
test_tailoring.py — Standalone test for the Resume Tailoring pipeline.

Run this script BEFORE running the bot to verify:
    1. pdfplumber can extract text from your base resume PDF.
    2. Azure OpenAI credentials are correct and the model responds.
    3. reportlab generates a valid tailored PDF.

Usage:
    cd d:\\LEARNING\\Job-Hunter-Copilot
    .\\venv\\Scripts\\python test_tailoring.py

Expected output:
    [OK] Base resume text extracted (XXXX chars)
    [OK] Azure OpenAI tailored resume JSON received
    [OK] Tailored PDF generated at: <temp_dir>/TEST_JOB_001_resume.pdf
    
    === ALL TESTS PASSED ===
"""

import os
import sys

# Make sure we run from the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

SAMPLE_JOB_DESCRIPTION = """
Senior Full Stack Developer — Azure & Angular

We are looking for an experienced Full Stack Developer to join our team in Germany.

Requirements:
- 8+ years of software development experience
- Strong skills in Angular (v14+), .NET Core, C#
- Experience with Azure cloud services (Azure Functions, Azure DevOps, Azure OpenAI)
- Agentic AI / LLM integration experience is a plus
- Familiarity with CI/CD pipelines and Docker/Kubernetes
- Excellent communication skills and ability to work in cross-functional teams
- German language certification (B1 or higher) is a strong advantage
- Visa holder or EU work permit is preferred

Nice to have:
- Experience with Microservices architecture
- Knowledge of TypeScript and Node.js
- German business communication experience
"""

TEST_JOB_ID = "TEST_JOB_001"


def test_extraction():
    """Test 1: PDF text extraction from base resume."""
    print("\n[TEST 1] Extracting base resume text...")
    from modules.resumes.extractor import get_default_resume_text

    try:
        text = get_default_resume_text()
        assert len(text) > 100, "Extracted text is suspiciously short!"
        print(f"  [OK] Base resume text extracted ({len(text)} chars)")
        print(f"       Preview: {text[:200].replace(chr(10), ' ')}...")
        return text
    except Exception as e:
        print(f"  [FAIL] {e}")
        return None


def test_azure_client_sanity():
    """
    Test 0: Azure client connectivity sanity check.

    Sends a minimal 1-token chat completion to verify:
      - Endpoint URL is reachable
      - API key is valid
      - Deployment name exists
      - API version is supported

    This is intentionally cheap — max_tokens=5 so it burns almost no quota.
    """
    print("\n[TEST 0] Azure OpenAI client sanity check...")
    from modules.ai.azureOpenaiConnections import azure_create_client, azure_close_client
    from config.secrets import azure_openai_endpoint, azure_openai_deployment, azure_openai_api_version

    client = None
    try:
        client = azure_create_client()
        assert client is not None, "azure_create_client() returned None!"

        # Minimal ping: ask the model to reply with one word.
        # max_tokens=5 keeps cost near zero.
        response = client.chat.completions.create(
            model=azure_openai_deployment,
            messages=[{"role": "user", "content": "Reply with the single word: OK"}],
            max_tokens=5,
            stream=False,
        )
        reply = response.choices[0].message.content.strip()
        assert reply, "Empty response from Azure OpenAI!"

        print(f"  [OK] Azure client is healthy")
        print(f"       Endpoint  : {azure_openai_endpoint}")
        print(f"       Deployment: {azure_openai_deployment}")
        print(f"       API Ver   : {azure_openai_api_version}")
        print(f"       Model ping: {repr(reply)}")
        return True

    except Exception as e:
        print(f"  [FAIL] Azure client sanity check failed: {e}")
        print(f"         -> Check azure_openai_endpoint, azure_openai_key,")
        print(f"           azure_openai_deployment, and azure_openai_api_version")
        print(f"           in config/secrets.py")
        return False
    finally:
        if client:
            try:
                azure_close_client(client)
            except Exception:
                pass


def test_azure_tailoring(base_text: str):
    """Test 2: Azure OpenAI resume tailoring."""
    print("\n[TEST 2] Calling Azure OpenAI to tailor resume...")
    from modules.ai.azureOpenaiConnections import azure_create_client, azure_tailor_resume, azure_close_client

    client = None
    try:
        client = azure_create_client()
        assert client is not None, "azure_create_client() returned None!"

        resume_data = azure_tailor_resume(client, base_text, SAMPLE_JOB_DESCRIPTION, stream=False)
        assert isinstance(resume_data, dict), f"Expected dict, got {type(resume_data)}"
        assert "name" in resume_data, "Missing 'name' key in response"
        assert "summary" in resume_data, "Missing 'summary' key in response"

        print(f"  [OK] Azure OpenAI tailored resume JSON received")
        print(f"       Name    : {resume_data.get('name', 'N/A')}")
        print(f"       Summary : {resume_data.get('summary', 'N/A')[:120]}...")
        print(f"       Sections: {list(resume_data.keys())}")
        return resume_data

    except Exception as e:
        print(f"  [FAIL] {e}")
        return None
    finally:
        if client:
            try:
                azure_close_client(client)
            except Exception:
                pass


def test_pdf_generation(resume_data: dict):
    """Test 3: PDF generation with reportlab."""
    print("\n[TEST 3] Generating tailored PDF with reportlab...")
    import tempfile
    from modules.resumes.generator import generate_tailored_pdf

    output_path = os.path.join(tempfile.gettempdir(), f"TEST_JOB_001_resume.pdf")
    try:
        saved_path = generate_tailored_pdf(resume_data, output_path)
        assert os.path.exists(saved_path), f"PDF not found at: {saved_path}"
        size_kb = os.path.getsize(saved_path) / 1024
        assert size_kb > 5, f"PDF is suspiciously small ({size_kb:.1f} KB)"
        print(f"  [OK] Tailored PDF generated at: {saved_path} ({size_kb:.1f} KB)")
        return saved_path
    except Exception as e:
        print(f"  [FAIL] {e}")
        return None


def test_full_pipeline():
    """Test 4: Full pipeline via tailorer.py (with cache)."""
    print("\n[TEST 4] Full pipeline via tailor_resume_for_job()...")
    from modules.resumes.tailorer import tailor_resume_for_job
    from modules.ai.azureOpenaiConnections import azure_create_client, azure_close_client

    TEST_JOB_TITLE = "Senior Full Stack Developer Azure Angular"
    client = None
    try:
        client = azure_create_client()
        # Updated signature: (job_id, job_title, job_description, azure_client)
        result_path = tailor_resume_for_job(
            TEST_JOB_ID + "_PIPELINE",
            TEST_JOB_TITLE,
            SAMPLE_JOB_DESCRIPTION,
            client,
        )
        assert result_path, "tailor_resume_for_job returned None (tailoring failed)"
        print(f"  [OK] Pipeline result path: {result_path}")
        return result_path
    except Exception as e:
        print(f"  [FAIL] {e}")
        return None
    finally:
        if client:
            try: azure_close_client(client)
            except Exception: pass


if __name__ == "__main__":
    print("=" * 60)
    print("  Resume Tailoring — Pipeline Test")
    print("=" * 60)

    results = {}

    # Test 0 — Azure client sanity check
    # sanity_ok = test_azure_client_sanity()
    # results["azure_client_sanity"] = sanity_ok

    # if not sanity_ok:
    #     print("\n[ABORT] Azure client failed sanity check — skipping remaining tests.")
    #     print("=" * 60)
    #     print("  [FAIL] azure_client_sanity")
    #     print("=" * 60)
    #     sys.exit(1)

    # Test 1
    base_text = test_extraction()
    results["extraction"] = base_text is not None

    # Test 2 (only if extraction passed)
    if base_text:
        resume_data = test_azure_tailoring(base_text)
        results["azure_tailoring"] = resume_data is not None
    else:
        print("\n[SKIP] Test 2 (Azure tailoring) — skipped due to Test 1 failure")
        resume_data = None
        results["azure_tailoring"] = False

    # Test 3 (only if tailoring passed)
    if resume_data:
        pdf_path = test_pdf_generation(resume_data)
        results["pdf_generation"] = pdf_path is not None
    else:
        print("\n[SKIP] Test 3 (PDF generation) — skipped due to Test 2 failure")
        results["pdf_generation"] = False

    # Test 4 — full pipeline
    pipeline_path = test_full_pipeline()
    results["full_pipeline"] = pipeline_path is not None

    # Summary
    print("\n" + "=" * 60)
    all_passed = all(results.values())
    for test, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {test}")

    print("=" * 60)
    if all_passed:
        print("  === ALL TESTS PASSED ===")
        print("  You can now set use_resume_tailoring = True in config/secrets.py")
    else:
        print("  === SOME TESTS FAILED — check errors above ===")
        sys.exit(1)
