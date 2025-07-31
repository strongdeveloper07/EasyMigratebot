import logging
from google.cloud import vision
from google.oauth2 import service_account
from io import BytesIO
from pdf2image import convert_from_bytes
from PIL import Image
from config import SERVICE_ACCOUNT_JSON

logger = logging.getLogger(__name__)

if SERVICE_ACCOUNT_JSON:
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON)
    GCV_CLIENT = vision.ImageAnnotatorClient(credentials=credentials)
else:
    GCV_CLIENT = None

def convert_pdf_to_png(pdf_bytes: bytes, pages: list = None) -> list:
    if pages is None:
        pages = []
    images = convert_from_bytes(pdf_bytes, dpi=300, first_page=min(pages) if pages else 1, 
                                last_page=max(pages) if pages else None)
    result = []
    for img in images:
        buf = BytesIO()
        img.save(buf, format="PNG")
        result.append(buf.getvalue())
    return result

def gcv_ocr_multiple(images: list) -> str:
    if not GCV_CLIENT:
        logger.error("Google Cloud Vision client not initialized")
        return ""
    full_text = ""
    for img_bytes in images:
        image = vision.Image(content=img_bytes)
        response = GCV_CLIENT.text_detection(image=image)
        texts = response.text_annotations
        if texts:
            full_text += texts[0].description + "\n\n"
    return full_text.strip()

def gcv_ocr(file_bytes: bytes) -> str:
    if not GCV_CLIENT:
        logger.error("Google Cloud Vision client not initialized")
        return ""
    image = vision.Image(content=file_bytes)
    response = GCV_CLIENT.text_detection(image=image)
    texts = response.text_annotations
    if response.error.message:
        logger.error(f"Vision API error: {response.error.message}")
        return ""
    if not texts:
        return ""
    return texts[0].description or ""
