from pathlib import Path
from pypdf import PdfReader

def load_text_file(path: Path | str) -> str:
    path = Path(path)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def load_pdf(path: Path | str) -> str:
    path = Path(path)
    text = []
    reader = PdfReader(path)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return "\n".join(text)

def load_file(path: Path | str) -> str:
    path = Path(path)
    if path.suffix.lower() == '.pdf':
        return load_pdf(path)
    elif path.suffix.lower() in ['.txt', '.md']:
        return load_text_file(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
