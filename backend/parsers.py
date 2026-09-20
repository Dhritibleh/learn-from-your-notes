import io
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

MAX_CHARS = 100000


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))

    text = ""

    for page in reader.pages:
        page_text = page.extract_text() or ""
        text += page_text + "\n"

    text = text.strip()

    if not text:
        raise ValueError("No readable text was found in the PDF.")

    return text[:MAX_CHARS]


def extract_text_from_url(url: str) -> str:

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type", ""
    ).lower()

    # If URL is a PDF
    if (
        url.lower().endswith(".pdf")
        or "application/pdf" in content_type
    ):
        return extract_text_from_pdf_bytes(
            response.content
        )

    # Otherwise treat it as a webpage
    soup = BeautifulSoup(
        response.content,
        "html.parser"
    )

    for element in soup(
        ["script", "style", "noscript"]
    ):
        element.decompose()

    paragraphs = soup.find_all("p")

    text = "\n".join(
        paragraph.get_text(
            " ",
            strip=True
        )
        for paragraph in paragraphs
    )

    text = text.strip()

    if not text:
        raise ValueError(
            "No readable paragraph text was found on this webpage."
        )

    return text[:MAX_CHARS]