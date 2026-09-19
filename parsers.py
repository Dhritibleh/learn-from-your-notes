import io
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

def extract_text_from_pdf_bytes(file_bytes:bytes)-> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text =""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text[:4000]

def extract_text_from_url(url: str)-> str:
    headers = {'User-Agent':'Mozilla/5.0'}
    response = requests.get(url,headers=headers,timeout=10)

    if url.lower().endswith('.pdf') or 'application/pdf' in response.headers.get('Content-Type',):
       return
    extract_text_from_pdf_bytes(response.content)

    soup = BeautifulSoup(response.content,'html.parser')
    for script in soup(["script","style"]):
       script.decompose()
    paragraphs = soup.find_all('p')
    return "".join([p.get_text() for p in paragraphs])[:4000]
                         

