from fastapi import FastAPI, UploadFile, HTTPException, File, Path, Response
import uvicorn

from routers import router
app = FastAPI(
    title="File Service",
    description="""
    API сервис для хранения и получения файлов.

    ## Возможности

    * Загрузка файлов на сервер
    * Получение файлов по имени

    ## Ограничения

    * Максимальный размер файла: 100MB
    * Поддерживаемые форматы: .txt, .pdf, .png, .jpg, .jpeg, .gif, .mp4, .mp3, .doc, .docx
    """
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)