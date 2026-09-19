import os
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from google import genai
from parsers import extract_text_from_pdf_bytes

app = FastAPI(title="Learn From Your Notes API")

# Initialize Gemini Client using environment variable
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_quiz_from_text(raw_text: str):
    prompt = (
        "Generate a structured quiz with multiple-choice questions "
        f"and answer keys based on the following text:\n\n{raw_text}"
    )
    
    # Using gemini-3.6-flash as required by your SDK access
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text

@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.post("/generate/file")
async def generate_from_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        print(f"--- File Received: {file.filename} ({len(contents)} bytes) ---")
        
        raw_text = extract_text_from_pdf_bytes(contents)
        print(f"--- Text Extracted: {len(raw_text)} characters ---")
        
        quiz_output = generate_quiz_from_text(raw_text)
        return {"quiz": quiz_output}
        
    except Exception as e:
        print("================ ERROR TRACEBACK ================")
        traceback.print_exc()
        print("=================================================")
        raise HTTPException(status_code=500, detail=str(e))