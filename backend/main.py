import os
import json

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI

from parsers import (
    extract_text_from_pdf_bytes,
    extract_text_from_url
)


load_dotenv()


app = FastAPI(
    title="Learn From Your Notes API"
)


api_key = os.getenv("XAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "XAI_API_KEY is missing. Add it to the .env file."
    )


client = OpenAI(
    api_key=api_key,
    base_url="https://api.x.ai/v1"
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

    response = client.chat.completions.create(
        model="grok-4.6",
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate educational "
                    "multiple-choice quizzes."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "Grok returned an empty response."
        )

    content = content.strip()

    if content.startswith("```"):
        content = content.replace(
            "```json",
            ""
        )
        content = content.replace(
            "```",
            ""
        )
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
                detail=(
                    "Please enter a valid "
                    "HTTP or HTTPS URL."
                )
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