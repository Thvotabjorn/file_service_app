from fastapi import APIRouter, FastAPI, UploadFile, HTTPException, File, Path, Response
from fastapi.responses import StreamingResponse
import os
import grpc_client as gh

from core.settings import settings

router = APIRouter()

ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3', '.doc', '.docx'}

def validate_filename(filename: str) -> bool:
    """Проверка валидности имени файла"""
    if not filename:
        return False
    
    # Проверяем расширение файла
    file_extension = os.path.splitext(filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False
    
    # Проверяем на недопустимые символы в имени файла
    invalid_chars = '<>:"/\\|?*'
    if any(char in filename for char in invalid_chars):
        return False
    
    return True

@router.get("/files/{filename}",
    summary="Получение файла",
    description="Загрузка файла с сервера по его имени",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Успешное получение файла",
            "content": {
                "application/octet-stream": {}
            },
        },
        404: {
            "description": "Файл не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Файл example.txt не найден"}
                }
            }
        },
        400: {
            "description": "Некорректное имя файла",
            "content": {
                "application/json": {
                    "example": {"detail": "Недопустимое имя файла"}
                }
            }
        }
    }
)
async def get_file(
    filename: str = Path(
        ...,
        description="Имя файла для загрузки",
        min_length=1,
        max_length=255,
        example="document.pdf"
    )
):
    """
    Загрузка файла с сервера.

    ## Параметры:
    * **filename**: имя файла для загрузки

    ## Возвращает:
    * Файл в виде потока байтов

    ## Ошибки:
    * **404**: Файл не найден
    * **400**: Некорректное имя файла
    * **500**: Внутренняя ошибка сервера
    """
    if not validate_filename(filename):
        raise HTTPException(
            status_code=400,
            detail="Недопустимое имя файла"
        )
    
    try:
        response = await gh.get_file_from_service(filename)
        return StreamingResponse(
            iter([response]), 
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        if "File not found" in str(e):
            raise HTTPException(
                status_code=404,
                detail=f"Файл {filename} не найден"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении файла: {str(e)}"
        )

@router.post("/files/upload/",
    summary="Загрузка файла",
    description="Загрузка файла на сервер",
    responses={
        200: {
            "description": "Успешная загрузка файла",
            "content": {
                "application/json": {
                    "example": {"message": "File example.txt uploaded successfully."}
                }
            }
        },
        400: {
            "description": "Ошибка валидации",
            "content": {
                "application/json": {
                    "example": {"detail": "Недопустимое имя файла или расширение"}
                }
            }
        },
        413: {
            "description": "Файл слишком большой",
            "content": {
                "application/json": {
                    "example": {"detail": "Размер файла превышает максимально допустимый (100MB)"}
                }
            }
        }
    }
)
async def upload_file(
    file: UploadFile = File(
        ...,
        description="Файл для загрузки",
    )
):
    """
    Загрузка файла на сервер.

    ## Ограничения:
    * Максимальный размер файла: 100MB
    * Поддерживаемые форматы: .txt, .pdf, .png, .jpg, .jpeg, .gif, .mp4, .mp3, .doc, .docx

    ## Ошибки:
    * **400**: Некорректный файл или имя файла
    * **413**: Превышен максимальный размер файла
    * **500**: Внутренняя ошибка сервера
    """
    # Проверка наличия файла
    if not file:
        raise HTTPException(
            status_code=400,
            detail="Файл не предоставлен"
        )

    # Валидация имени файла
    if not validate_filename(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Недопустимое имя файла или расширение"
        )

    # Проверка размера файла
    try:
        file_size = 0
        while chunk := await file.read(8192):
            file_size += len(chunk)
            if file_size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"Размер файла превышает максимально допустимый ({settings.MAX_FILE_SIZE // 1024 // 1024}MB)"
                )
        await file.seek(0)  # Возвращаем указатель в начало файла
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при проверке размера файла: {str(e)}"
        )

    try:
        response = await gh.send_file_to_file_service(file)
        return {"message": response.message}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )
