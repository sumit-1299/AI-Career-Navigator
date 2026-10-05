"""Bounded, isolated text extraction. No network, OCR, file storage or code execution."""
import io
import json
import sys
import zipfile
from xml.etree import ElementTree

MAX_TEXT = 30000
MAX_FILE = 2 * 1024 * 1024


def extract(data, kind):
    if not data or len(data) > MAX_FILE:
        raise ValueError("Choose a nonempty resume file up to 2 MB.")
    if kind == ".txt":
        text = data.decode("utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
    elif kind == ".docx":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 1000 or sum(i.file_size for i in entries) > 12 * 1024 * 1024:
                raise ValueError("This Word file is too complex. Paste the resume text instead.")
            info = archive.getinfo("word/document.xml")
            if info.file_size > 4 * 1024 * 1024 or info.flag_bits & 1:
                raise ValueError("Use an unencrypted Word file with a smaller document body.")
            xml = archive.read(info)
            if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
                raise ValueError("This Word file contains unsupported XML declarations.")
            root = ElementTree.fromstring(xml)
            ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            text = "\n".join("".join(node.text or "" for node in paragraph.iter(ns + "t"))
                             for paragraph in root.iter(ns + "p"))
    elif kind == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ValueError("Use an unlocked PDF or paste its text.")
        if len(reader.pages) > 10:
            raise ValueError("Use a resume of up to 10 pages or paste a relevant excerpt.")
        chunks = []
        length = 0
        for page in reader.pages:
            chunk = page.extract_text() or ""
            length += len(chunk)
            if length > MAX_TEXT:
                raise ValueError("Resume text exceeds 30,000 characters. Paste a shorter excerpt.")
            chunks.append(chunk)
        text = "\n".join(chunks)
    else:
        raise ValueError("Choose PDF, DOCX or TXT, or paste your resume text.")
    text = text.replace("\x00", "").strip()
    if len(text) > MAX_TEXT:
        raise ValueError("Resume text exceeds 30,000 characters. Paste a shorter excerpt.")
    if len(text) < 40:
        raise ValueError("Not enough readable text was found. Scanned images need OCR; paste the text instead.")
    return text


if __name__ == "__main__":
    # On POSIX, bound parser memory and CPU as well as the parent's wall timeout.
    # Windows uses the parent's wall timeout and the same input/page/text limits.
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (384 * 1024 * 1024, 384 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (7, 7))
    except ImportError:
        pass
    try:
        text = extract(sys.stdin.buffer.read(MAX_FILE + 1), sys.argv[1])
        print(json.dumps({"text": text}))
    except (ValueError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc)}))
    except Exception:
        print(json.dumps({"error": "This file could not be read. Try another export or paste the resume text."}))
