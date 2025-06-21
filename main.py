from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
import os
import re
import logging
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Setup Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Setup FastAPI app
app = FastAPI(title="CI/CD Log Analyzer", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input model
class LogInput(BaseModel):
    log: str

# Serve static frontend
app.mount("/static", StaticFiles(directory="Frontend"), name="static")

@app.get("/")
def read_index():
    return FileResponse("Frontend/index.html")


# POST endpoint to analyze CI/CD logs
@app.post("/analyze-log")
async def analyze_log(log_input: LogInput):
    prompt = f"""
You are an expert CI/CD assistant. Analyze the following CI/CD failure log and explain the root cause in plain English. Then suggest a fix.

Log:
\"\"\"{log_input.log}\"\"\"

Respond in this format:
Explanation:
Suggested Fix:
"""

    try:
        chat = model.start_chat()
        response = chat.send_message(prompt)
        output = response.text

        # Log the interaction
        logging.info(f"Prompt sent:\n{prompt}")
        logging.info(f"Response received:\n{output}")

        # Parse output into sections
        match = re.search(r"Explanation:(.*?)(Suggested Fix:.*)", output, re.DOTALL)
        if match:
            explanation = match.group(1).strip()
            suggested_fix = match.group(2).replace("Suggested Fix:", "").strip()
        else:
            # If pattern doesn't match, treat all as explanation
            explanation = output.strip()
            suggested_fix = "No specific fix provided."

        return {
            "explanation": explanation,
            "suggested_fix": suggested_fix
        }

    except Exception as e:
        logging.error(f"Error during Gemini call: {e}")
        raise HTTPException(status_code=502, detail="Error communicating with Gemini API. Please try again later.")
