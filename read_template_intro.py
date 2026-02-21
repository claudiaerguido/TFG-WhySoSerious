from docx import Document
import os

def read_template_intro(path):
    try:
        doc = Document(path)
        print("--- EXTRACTING START OF DOCUMENT ---")
        count = 0
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                print(text)
                count += 1
            if count > 50: # Read enough lines to cover the Table of Contents/Introduction definition
                break
    except Exception as e:
        print(f"Error: {e}")

read_template_intro("documentacion/Plantilla TFG_GISI_v4.0-m1.docx")
