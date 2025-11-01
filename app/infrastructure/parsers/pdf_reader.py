from typing import Iterable
from pypdf import PdfReader


def extract_text_pages(file_path: str) -> Iterable[str]:
    reader = PdfReader(file_path)
    for page in reader.pages:
        text = page.extract_text() or ""
        yield text
