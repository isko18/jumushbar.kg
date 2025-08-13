import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import logging

logger = logging.getLogger(__name__)

def extract_passport_info_from_image(image_path):
    try:
        image = Image.open(image_path)
        image = image.convert('L')  # grayscale
        image = image.filter(ImageFilter.SHARPEN)
        image = ImageEnhance.Contrast(image).enhance(2.0)
        image = image.resize((image.width * 2, image.height * 2))

        text = pytesseract.image_to_string(image, lang='eng+rus')
        logger.info(f"🧾 OCR TEXT: {text}")

        clean_text = text.replace(" ", "").replace("\n", "").replace("\t", "")
        clean_text = clean_text.upper()

        # 🔁 Попытка 1: стандартный ID
        passport_id_match = re.search(r'I[DО0]\s*[\-:]?\s*\d{6,10}', clean_text, re.IGNORECASE)
        passport_id = passport_id_match.group(0) if passport_id_match else None
        if passport_id:
            passport_id = passport_id.upper().replace(" ", "").replace("-", "").replace(":", "")
            passport_id = passport_id.replace("О", "D").replace("0", "D")

        # ✅ Попытка 2: из MRZ-блока, если обычный ID не найден
        if not passport_id:
            mrz_match = re.search(r'IDKGZID(\d{7,9})', clean_text)
            if mrz_match:
                passport_id = f"ID{mrz_match.group(1)}"

        # 🔎 ИНН (14 цифр)
        inn_match = re.search(r'\d{14}', clean_text)
        personal_number = inn_match.group(0) if inn_match else None

        logger.info(f"✅ Распознанный ID: {passport_id}, ИНН: {personal_number}")
        return passport_id, personal_number

    except Exception as e:
        logger.exception(f"❌ Ошибка OCR в extract_passport_info_from_image: {e}")
        return None, None
