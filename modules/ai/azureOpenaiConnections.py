'''
product: Job-Hunter-Copilot
version: v1.2026-07
'''


# ──────────────────────────────────────────────────────────────────────────────
# Imports
# ──────────────────────────────────────────────────────────────────────────────
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion
from typing import Literal

from config.secrets import (
    azure_openai_endpoint,
    azure_openai_key,
    azure_openai_deployment,
    azure_openai_api_version,
    stream_output,
)
from modules.helpers import print_lg, critical_error_log, convert_to_json
from modules.ai.prompts import (
    tailor_resume_prompt,
    tailor_resume_response_format,
    ai_answer_prompt,
)


# ──────────────────────────────────────────────────────────────────────────────
# Error instructions (consistent with existing openaiConnections.py style)
# ──────────────────────────────────────────────────────────────────────────────
azureApiCheckInstructions = """

1. Make sure your Azure OpenAI endpoint and key are set correctly in config/secrets.py
   under the 'Resume Tailoring with Azure OpenAI' section.
2. Check that the deployment name matches exactly what is shown in Azure AI Foundry.
3. Verify the api_version is supported by your Azure resource.

ERROR:
"""


# ──────────────────────────────────────────────────────────────────────────────
# Client creation
# ──────────────────────────────────────────────────────────────────────────────
def azure_create_client() -> AzureOpenAI | None:
    """
    Creates and returns an AzureOpenAI client using credentials from config/secrets.py.

    Returns:
        AzureOpenAI client if successful, None on failure.

    Usage:
        client = azure_create_client()
    """
    try:
        print_lg("Creating Azure OpenAI client for resume tailoring...")

        # Validate placeholders — prevent accidental submission with default values
        if "YOUR_AZURE" in azure_openai_endpoint or "YOUR_AZURE" in azure_openai_key:
            raise ValueError(
                "Azure OpenAI credentials are still set to placeholder values!\n"
                "Please update azure_openai_endpoint, azure_openai_key, and "
                "azure_openai_deployment in config/secrets.py"
            )

        client = AzureOpenAI(
            azure_endpoint=azure_openai_endpoint,
            api_key=azure_openai_key,
            api_version=azure_openai_api_version,
        )

        print_lg("---- SUCCESSFULLY CREATED AZURE OPENAI CLIENT! ----")
        print_lg(f"Endpoint  : {azure_openai_endpoint}")
        print_lg(f"Deployment: {azure_openai_deployment}")
        print_lg(f"API Ver   : {azure_openai_api_version}")
        print_lg("Check './config/secrets.py' for more details.\n")
        print_lg("----------------------------------------------------")

        return client

    except Exception as e:
        critical_error_log(
            f"Error creating Azure OpenAI client.{azureApiCheckInstructions}", e
        )
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Close client
# ──────────────────────────────────────────────────────────────────────────────
def azure_close_client(client: AzureOpenAI) -> None:
    """
    Closes the AzureOpenAI client connection.

    Args:
        client: AzureOpenAI client instance to close.
    """
    try:
        if client:
            print_lg("Closing Azure OpenAI client...")
            client.close()
    except Exception as e:
        critical_error_log("Error closing Azure OpenAI client.", e)


# ──────────────────────────────────────────────────────────────────────────────
# Core completion call (internal helper)
# ──────────────────────────────────────────────────────────────────────────────
def _azure_completion(
    client: AzureOpenAI,
    messages: list[dict],
    response_format: dict = None,
    stream: bool = False,
) -> dict | str:
    """
    Internal helper that calls Azure OpenAI chat completions.

    Args:
        client: AzureOpenAI client.
        messages: List of message dicts e.g. [{"role": "user", "content": "..."}].
        response_format: Optional JSON schema for structured output.
        stream: Whether to stream the response.

    Returns:
        Parsed dict if response_format is given, raw string otherwise.
    """
    if not client:
        raise ValueError("Azure OpenAI client is not available!")

    params = {
        "model": azure_openai_deployment,
        "messages": messages,
        "stream": stream,
    }

    # Attach structured output schema if provided
    if response_format:
        params["response_format"] = response_format

    completion = client.chat.completions.create(**params)

    result = ""

    if stream:
        print_lg("--AZURE STREAMING STARTED")
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                chunk_text = chunk.choices[0].delta.content
                result += chunk_text
                print_lg(chunk_text, end="", flush=True)
        print_lg("\n--AZURE STREAMING COMPLETE")
    else:
        result = completion.choices[0].message.content

    if response_format:
        result = convert_to_json(result)

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Resume tailoring function (main public API)
# ──────────────────────────────────────────────────────────────────────────────
def azure_tailor_resume(
    client: AzureOpenAI,
    base_resume_text: str,
    job_description: str,
    stream: bool = stream_output,
) -> dict | None:
    """
    Sends the base resume text and job description to Azure OpenAI and returns
    a structured resume dict tailored to the job.

    Args:
        client:           AzureOpenAI client (from azure_create_client()).
        base_resume_text: Plain text extracted from the base PDF resume.
        job_description:  Full job description text scraped from LinkedIn.
        stream:           Whether to stream the API response (default from secrets.py).

    Returns:
        dict with keys: name, contact, summary, experience, skills, projects,
                        education, certifications
        Returns None on failure.

    Example:
        client = azure_create_client()
        resume_data = azure_tailor_resume(client, base_text, jd_text)
        if resume_data:
            generate_tailored_pdf(resume_data, output_path)
    """
    print_lg("-- TAILORING RESUME with Azure OpenAI (Azure AI Foundry)")
    try:
        if not base_resume_text or not base_resume_text.strip():
            raise ValueError("Base resume text is empty — cannot tailor resume.")
        if not job_description or not job_description.strip():
            raise ValueError("Job description is empty — cannot tailor resume.")

        # Build prompt using the template from prompts.py
        prompt = tailor_resume_prompt.format(
            base_resume_text.strip(),
            job_description.strip()
        )

        messages = [{"role": "user", "content": prompt}]

        print_lg("Sending resume + job description to Azure OpenAI...")
        result = _azure_completion(
            client,
            messages,
            response_format=tailor_resume_response_format,
            stream=stream,
        )

        # If convert_to_json returned an error dict, bubble it up
        if isinstance(result, dict) and "error" in result:
            raise ValueError(f"Failed to parse Azure response as JSON: {result}")

        print_lg("-- RESUME TAILORING COMPLETE")
        print_lg(f"Tailored sections: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        return result

    except Exception as e:
        critical_error_log(
            f"Error during Azure OpenAI resume tailoring.{azureApiCheckInstructions}", e
        )
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Question answering function (mirrors ai_answer_question from openaiConnections)
# ──────────────────────────────────────────────────────────────────────────────
def azure_answer_question(
    client: AzureOpenAI,
    question: str,
    options: list[str] | None = None,
    question_type: Literal["text", "textarea", "single_select", "multiple_select"] = "text",
    job_description: str = None,
    about_company: str = None,
    user_information_all: str = None,
    stream: bool = stream_output,
) -> str | None:
    """
    Answers a LinkedIn Easy Apply form question using Azure OpenAI.

    Mirrors ``ai_answer_question`` from openaiConnections.py so it can be used
    as a drop-in replacement when ``ai_provider == "azure"``.

    Args:
        client:               AzureOpenAI client (from azure_create_client()).
        question:             The question label text from the form.
        options:              List of option strings for select/radio questions
                              (informational — appended to the prompt when present).
        question_type:        One of "text", "textarea", "single_select",
                              "multiple_select".
        job_description:      Full job description for context (optional).
        about_company:        Company description for context (optional).
        user_information_all: Resume-style user info string for context (optional).
        stream:               Whether to stream the Azure response.

    Returns:
        str: The AI-generated answer, or None on failure.

    Example:
        answer = azure_answer_question(
            client, "How many years of Python experience do you have?",
            question_type="text", job_description=jd, user_information_all=resume
        )
    """
    print_lg("-- ANSWERING QUESTION using Azure OpenAI")
    try:
        # Build the base prompt using the shared ai_answer_prompt template
        prompt = ai_answer_prompt.format(user_information_all or "N/A", question)

        # Append select/radio options when available so the model can pick correctly
        if options:
            formatted = ", ".join(f'"{o}"' for o in options)
            prompt += f"\nAvailable options: [{formatted}]"
            if question_type == "single_select":
                prompt += "\nReturn ONLY one of the options above, exactly as written."
            elif question_type == "multiple_select":
                prompt += "\nReturn a comma-separated list of the best matching options above."

        # Append optional context
        if job_description and job_description not in ("", "Unknown"):
            prompt += f"\nJob Description:\n{job_description}"
        if about_company and about_company not in ("", "Unknown"):
            prompt += f"\nAbout the Company:\n{about_company}"

        messages = [{"role": "user", "content": prompt}]
        print_lg("Prompt sent to Azure OpenAI:\n", prompt)

        result = _azure_completion(client, messages, stream=stream)

        print_lg("\nAzure AI Answer to Question:\n")
        print_lg(result)
        return result

    except Exception as e:
        critical_error_log(
            f"Error during Azure OpenAI question answering.{azureApiCheckInstructions}", e
        )
        return None

