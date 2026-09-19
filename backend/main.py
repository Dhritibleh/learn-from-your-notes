import os
import json

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai

from parsers import (
    extract_text_from_pdf_bytes,
    extract_text_from_url
)

load_dotenv()

app = FastAPI(
    title="Learn From Your Notes API"
)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to the .env file."
    )

client = genai.Client(
    api_key=api_key
)


class URLRequest(BaseModel):
    url: str


def generate_quiz_from_text(raw_text: str):

    prompt = f"""
You are an educational quiz generator.

Create a quiz from the study material below.

Rules:
- Generate exactly 3 multiple-choice questions.
- Each question must have exactly 4 options.
- Questions must be based ONLY on the provided study material.
- Do not invent information.
- Return ONLY valid JSON.
- Do not use Markdown.
- The answer field must contain the exact correct option text.

Return this exact structure:

{{
    "topic": "main topic of the material",
    "questions": [
        {{
            "question": "Question text",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": "Correct option text"
        }}
    ]
}}

Study material:

{raw_text}
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={
            "temperature": 0.2
        }
    )

    content = response.text

    if not content:
        raise ValueError(
            "Gemini returned an empty response."
        )

    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    quiz = json.loads(content)

    return quiz


@app.get("/")
def read_root():

    return FileResponse(
        "../frontend/index.html"
    )


@app.post("/generate/file")
async def generate_from_file(
    file: UploadFile = File(...)
):

    try:

        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Please upload a PDF file."
            )

        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty."
            )

        raw_text = extract_text_from_pdf_bytes(
            contents
        )

        quiz = generate_quiz_from_text(
            raw_text
        )

        return {
            "status": "success",
            "quiz": quiz
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/generate/url")
async def generate_from_url(
    request: URLRequest
):

    try:

        if not request.url.startswith(
            ("http://", "https://")
        ):
            raise HTTPException(
                status_code=400,
                detail="Please enter a valid HTTP or HTTPS URL."
            )

        raw_text = extract_text_from_url(
            request.url
        )

        quiz = generate_quiz_from_text(
            raw_text
        )

        return {
            "status": "success",
            "quiz": quiz
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
