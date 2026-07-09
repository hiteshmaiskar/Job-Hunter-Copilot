'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

Support me: https://github.com/sponsors/GodsScion

version:    24.12.3.10.30
'''


###################################################### CONFIGURE YOUR TOOLS HERE ######################################################


# Login Credentials for LinkedIn (Optional)
username = "hitesh.maiskar89@gmail.com"       # Enter your username in the quotes
password = "erbeceH1!"           # Enter your password in the quotes


## Artificial Intelligence (Beta Not-Recommended)
# Use AI
use_AI = True                          # True or False, Note: True or False are case-sensitive
'''
Note: Set it as True only if you want to use AI, and If you either have a
1. Local LLM model running on your local machine, with it's APIs exposed. Example softwares to achieve it are:
    a. Ollama - https://ollama.com/
    b. llama.cpp - https://github.com/ggerganov/llama.cpp
    c. LM Studio - https://lmstudio.ai/ (Recommended)
    d. Jan - https://jan.ai/
2. OR you have a valid OpenAI API Key, and money to spare, and you don't mind spending it.
CHECK THE OPENAI API PIRCES AT THEIR WEBSITE (https://openai.com/api/pricing/). 
'''

##> ------ Yang Li : MARKYangL - Feature ------
##> ------ Tim L : tulxoro - Refactor ------
# Select AI Provider
ai_provider = "azure"               # "openai", "deepseek", "gemini"
'''
Note: Select your AI provider.
* "openai" - OpenAI API (GPT models) OR OpenAi-compatible APIs (like Ollama)
* "deepseek" - DeepSeek API (DeepSeek models)
* "gemini" - Google Gemini API (Gemini models)
* For any other models, keep it as "openai" if it is compatible with OpenAI's api.
'''



# Your LLM url or other AI api url and port
llm_api_url = "https://api.openai.com/v1/"       # Examples: "https://api.openai.com/v1/", "http://127.0.0.1:1234/v1/", "http://localhost:1234/v1/", "https://api.deepseek.com", "https://api.deepseek.com/v1"
'''
Note: Don't forget to add / at the end of your url. You may not need this if you are using Gemini.
'''

# Your LLM API key or other AI API key 
llm_api_key = "not-needed"              # Enter your API key in the quotes, make sure it's valid, if not will result in error.
'''
Note: Leave it empty as "" or "not-needed" if not needed. Else will result in error!
If you are using ollama, you MUST put "not-needed".
'''

# Your LLM model name or other AI model name
llm_model = "gpt-5-mini"          # Examples: "gpt-3.5-turbo", "gpt-4o", "llama-3.2-3b-instruct", "qwen3:latest", "gemini-pro", "gemini-1.5-flash", "gemini-2.5-flash", "deepseek-llm:latest"

llm_spec = "openai"                # Examples: "openai", "openai-like", "openai-like-github", "openai-like-mistral"
'''
Note: Currently "openai", "deepseek", "gemini" and "openai-like" api endpoints are supported.
Most LLMs are compatible with openai, so keeping it as "openai-like" will work.
'''

# # Yor local embedding model name or other AI Embedding model name
# llm_embedding_model = "nomic-embed-text-v1.5"

# Do you want to stream AI output?
stream_output = False                    # Examples: True or False. (False is recommended for performance, True is recommended for user experience!)
'''
Set `stream_output = True` if you want to stream AI output or `stream_output = False` if not.
'''
##


##> ------ Resume Tailoring with Azure OpenAI (Azure AI Foundry) ------

# Enable AI-powered resume tailoring per job description
use_resume_tailoring = True             # True or False — set True to generate a tailored resume for each job
'''
Note: When enabled, the bot will:
1. Extract text from your base resume (all resumes/default/)
2. Send it to Azure OpenAI along with the job description
3. Generate a tailored PDF saved to all resumes/tailored/<job_id>/resume.pdf
4. Upload the tailored resume instead of the default one
Set use_resume_tailoring = False to use the default static resume (original behavior).
'''

# Azure OpenAI endpoint — from Azure AI Foundry portal
azure_openai_endpoint = "https://job-hunter-copilot-resource.openai.azure.com/openai/v1"
# Example: "https://my-resource.openai.azure.com/"

# Azure OpenAI API key
azure_openai_key = "2PTisOhgbkP4vSqBX2bXEXZH0Unrb8CS2aE1n5fW7MssOMZ1Q3sIJQQJ99CGACHYHv6XJ3w3AAAAACOGZK3J"
# Example: "abc123def456..."

# Deployment name — the name you gave the model in Azure AI Foundry
azure_openai_deployment = "gpt-5-mini"
# Example: "gpt-4o", "gpt-35-turbo", or whatever name you chose during deployment

# Azure OpenAI API version
azure_openai_api_version = "2025-08-07"
# Example: "2024-02-01", "2025-01-01-preview" — check Azure docs for latest stable version

# Fallback to default resume if tailoring fails?
azure_tailoring_fallback = True         # True or False
'''
Note: If True, on any Azure API error or PDF generation failure, the bot will
silently fall back to uploading your default resume. If False, it will raise the error.
'''

# Skip re-tailoring if a tailored resume for this job_id already exists?
azure_tailoring_use_cache = True        # True or False
'''
Note: If True, if all resumes/tailored/<job_id>/resume.pdf already exists,
the bot reuses it without calling the Azure API again (saves tokens & time).
'''

##<



############################################################################################################
'''
THANK YOU for using my tool 😊! Wishing you the best in your job hunt 🙌🏻!

Sharing is caring! If you found this tool helpful, please share it with your peers 🥺. Your support keeps this project alive.

Support my work on <PATREON_LINK>. Together, we can help more job seekers.

As an independent developer, I pour my heart and soul into creating tools like this, driven by the genuine desire to make a positive impact.

Your support, whether through donations big or small or simply spreading the word, means the world to me and helps keep this project alive and thriving.

Gratefully yours 🙏🏻,
Sai Vignesh Golla
'''
############################################################################################################