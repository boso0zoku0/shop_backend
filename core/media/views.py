from fastapi import APIRouter, Depends, Request, File, UploadFile, Form
from core.auth.crud import get_current_user
from core.media.helper import save_uploaded_file_from_form
from pydantic import BaseModel

router = APIRouter(
    prefix="/media",
    tags=["Websocket Media"],
    dependencies=[Depends(get_current_user)],
)


class FileUploadResponse(BaseModel):
    file_url: str
    file_name: str
    file_size: int
    mime_type: str  # 'image' или 'video'


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
):
    try:
        file_url = await save_uploaded_file_from_form(file)

        # Определяем тип автоматически по content_type
        content_type = file.content_type or "application/octet-stream"

        return FileUploadResponse(
            file_url=file_url,
            file_name=file.filename,
            file_size=file.size,
            mime_type=content_type,
        )

    except Exception as e:
        return {"error": str(e)}
