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
    message: str


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    from_: str = Form(..., alias="from"),
):

    try:
        file_url = await save_uploaded_file_from_form(file, from_)

        return FileUploadResponse(
            file_url=file_url,
            file_name=file.filename,
            file_size=file.size,
            message="Файл успешно загружен",
        )

    except Exception as e:
        return {"error": str(e)}
