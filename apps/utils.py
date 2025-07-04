from PIL import Image
from io import BytesIO

def convert_imagefile_to_webp(file, quality=80):
    """
    Принимает файл (InMemoryUploadedFile), возвращает bytes webp изображения.
    """
    image = Image.open(file)
    image = image.convert('RGB')  # Убираем альфа-канал, если есть
    buffer = BytesIO()
    image.save(buffer, format='WEBP', quality=quality)
    return buffer.getvalue()
