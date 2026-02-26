import os
import uuid
import aiofiles
from fastapi import UploadFile
import mimetypes

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/webm", "video/ogg"]
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


async def save_uploaded_file(
    file_data: bytes, sender: str, file_info: dict = None
) -> str:
    """
    Сохраняет загруженный файл и возвращает URL для доступа к нему
    """
    # Создаем директорию для медиафайлов, если её нет
    media_dir = "static/media"
    os.makedirs(media_dir, exist_ok=True)

    # Генерируем уникальное имя файла
    file_extension = file_info.get("extension", "") if file_info else ""
    if not file_extension:
        # Пытаемся определить расширение из content_type
        content_type = file_info.get("file_type", "") if file_info else ""
        if content_type:
            ext = mimetypes.guess_extension(content_type)
            file_extension = ext if ext else ""

    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(media_dir, filename)

    # Сохраняем файл
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_data)

    # Формируем URL для доступа к файлу
    file_url = f"/static/media/{filename}"

    return file_url


async def save_uploaded_file_from_form(file: UploadFile):
    """
    Сохраняет файл из формы (для HTTP эндпоинтов)
    """
    media_dir = "static/media"
    os.makedirs(media_dir, exist_ok=True)

    # Генерируем уникальное имя файла
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(media_dir, filename)

    # Сохраняем файл
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    file_url = f"/static/media/{filename}"
    return file_url
