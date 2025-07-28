import pytesseract
from PIL import Image

def extract_passport_info_from_image(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang='eng+rus')
        lines = text.splitlines()

        passport_id = None
        personal_number = None

        for line in lines:
            line = line.strip()

            # Находим строку ID (обычно IDKGZ...)
            if "IDKGZ" in line or line.startswith("ID"):
                passport_id = line

            # Находим персональный номер (обычно 14-цифровой)
            if len(line) == 14 and line.isdigit():
                personal_number = line

        return passport_id, personal_number
    except Exception as e:
        return None, None
