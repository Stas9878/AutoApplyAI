import re
import io
import fitz
from pathlib import Path

from src.core.logger import logger


def _clean_text(text: str) -> str:
    '''Очищает текст резюме от лишних переносов и пробелов.'''
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def load_resume_text(pdf_path: Path) -> str:
    '''Загружает и парсит PDF-резюме в текст.'''

    if not pdf_path.exists():
        raise FileNotFoundError(f'Резюме не найдено: {pdf_path}')

    try:
        doc = fitz.open(pdf_path)
        raw_text = ''.join(page.get_text() for page in doc)
        doc.close()
        return _clean_text(raw_text)
    except Exception as e:
        logger.error(f'❌ Ошибка при чтении PDF: {e}')
        raise


def load_resume_text_from_bytes(pdf_bytes: bytes) -> str:
    '''Загружает текст из байтов PDF-файла.'''
    doc = fitz.open(stream=io.BytesIO(pdf_bytes), filetype='pdf')
    raw_text = ''.join(page.get_text() for page in doc)
    doc.close()
    return _clean_text(raw_text)