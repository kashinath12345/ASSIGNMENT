import os
import cv2
import pytesseract
import json
import re
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pdf2image import convert_from_path
from docx import Document
import pandas as pd

app = FastAPI()

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

OUTPUT_JSON = "./output.json"

def extract_fields_from_text(text):
    fields = {
        "Invoice Number": None,
        "Invoice Date": None,
        "Vendor Name": None,
        "Total Amount": None,
        "Tax Amount": None,
        "P.O. Number": None,
    }

    invoice_number_match = re.search(r"INVOICE\s*#\s*(\d+)", text, re.IGNORECASE)
    if invoice_number_match:
        fields["Invoice Number"] = invoice_number_match.group(1).strip()

    invoice_date_match = re.search(r"INVOICE\s*DATE\s*([\d/]+)", text, re.IGNORECASE)
    if invoice_date_match:
        fields["Invoice Date"] = invoice_date_match.group(1).strip()

    vendor_name_match = re.search(r"BILL TO\s*(.*?)(?:\n|$)", text, re.IGNORECASE)
    if vendor_name_match:
        fields["Vendor Name"] = vendor_name_match.group(1).strip()

    total_amount_match = re.search(r"TOTAL\s*\$?([\d,]+\.\d{2})", text, re.IGNORECASE)
    if total_amount_match:
        fields["Total Amount"] = total_amount_match.group(1).strip()

    tax_amount_match = re.search(r"TAX\s*\$?([\d,]+\.\d{2})", text, re.IGNORECASE)
    if tax_amount_match:
        fields["Tax Amount"] = tax_amount_match.group(1).strip()

    po_number_match = re.search(r"P\.O\.\s*#\s*(\d+)", text, re.IGNORECASE)
    if po_number_match:
        fields["P.O. Number"] = po_number_match.group(1).strip()

    return fields

# Helper function to convert non-image files into images
def convert_to_image(file_path, file_extension):
    images = []
    if file_extension == ".pdf":
        images = convert_from_path(file_path)
    elif file_extension == ".docx":
        document = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in document.paragraphs])
        img = cv2.putText(
            np.ones((1000, 1000, 3), dtype=np.uint8) * 255,
            text,
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )
        images.append(img)
    elif file_extension in [".xls", ".xlsx"]:
        df = pd.read_excel(file_path)
        text = df.to_string()
        img = cv2.putText(
            np.ones((1000, 1000, 3), dtype=np.uint8) * 255,
            text,
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )
        images.append(img)
    else:
        images.append(cv2.imread(file_path))
    return images

@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...)):
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    file_extension = os.path.splitext(file.filename)[1].lower()
    images = convert_to_image(file_path, file_extension)
    combined_text = ""

    for image in images:
        if isinstance(image, str):  
            combined_text += image
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binarized = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
            combined_text += pytesseract.image_to_string(binarized)

    
    extracted_fields = extract_fields_from_text(combined_text)
    with open(OUTPUT_JSON, "w") as json_file:
        json.dump(extracted_fields, json_file, indent=4)

    return JSONResponse(content={"message": "Extraction successful", "data": extracted_fields})
