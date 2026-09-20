# Learn From Your Notes 📚

Learn From Your Notes is an AI-powered study assistant that converts
study material into active learning content.

## Features

- Upload study PDFs
- Enter study-material URLs
- Filter out unrelated/non-study content
- Generate an overall summary
- Generate topic-by-topic explanations
- Generate 10 high-yield MCQs
- Generate a fresh quiz from the same notes
- Show correct answers and explanations after submission
- Track weak topics
- Provide review material for weak topics
- Generate focused quizzes for weak topics
- Stop tracking a topic after the student's performance improves

## How It Works

```text
📄 Upload PDF / Enter URL
        ↓
   📥 Extract Text
        ↓
 🔍 Check Study Material
        ↓
   📝 Generate Summary
        ↓
 📚 Identify Major Topics
        ↓
📖 Topic-wise Explanations
        ↓
    🧠 Generate Quiz
        ↓
   ✏️ Answer Quiz
        ↓
📊 Score + Explanations
        ↓
 ⚠️ Detect Weak Topics
        ↓
  📖 Targeted Review
        ↓
🎯 Focused Weak-Topic Quiz
        ↓
📈 Improved Performance
        ↓
  Stop Tracking Topic
```


## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python, FastAPI
- AI: Google Gemini API
- PDF Processing: PyPDF2
- Web Parsing: BeautifulSoup4, Requests
- Database: SQLite

## Project Structure

```text
learn-from-your-notes/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── parsers.py
│   └── venv/
├── frontend/
│   └── index.html
├── .gitignore
├── README.md
├── requirements.txt
└── notes_app.db
