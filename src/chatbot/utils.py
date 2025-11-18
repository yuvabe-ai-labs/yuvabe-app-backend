import re
from typing import List
import PyPDF2


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    text = re.sub(r'[_\-]{2,}', ' ', text)
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def extract_text_from_pdf_fileobj(fileobj) -> str:
    reader = PyPDF2.PdfReader(fileobj)
    all_text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            all_text.append(page_text)
    return clean_text(" ".join(all_text))


def split_into_sentences(text: str) -> List[str]:
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_sentences_with_overlap(sentences: List[str], max_words: int = 200, overlap_words: int = 40) -> List[str]:
    chunks = []
    current = []
    current_len = 0

    for sentence in sentences:
        words = sentence.split()
        wc = len(words)

        if current_len + wc > max_words and current:
            chunks.append(" ".join(current))

            if overlap_words > 0:
                last_words = " ".join(" ".join(current).split()[-overlap_words:])
                current = [last_words] if last_words else []
                current_len = len(last_words.split())
            else:
                current = []
                current_len = 0

        current.append(sentence)
        current_len += wc

    if current:
        chunks.append(" ".join(current))

    return chunks
