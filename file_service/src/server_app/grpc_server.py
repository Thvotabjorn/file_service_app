import os
from concurrent import futures
import logging
import sys

import aiofiles
import grpc
import file_service_pb2_grpc, file_service_pb2

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('grpc_server.log')
    ]
)
logger = logging.getLogger(__name__)

class FileService(file_service_pb2_grpc.FileServiceServicer):
    async def UploadFile(self, request_iterator, context):
        try:
            first_chunk = await anext(request_iterator)
            filename = first_chunk.filename or "uploaded_file"
            
            logger.info(f"Начало загрузки файла: {filename}")

            storage_dir = "../storage"
            os.makedirs(storage_dir, exist_ok=True)
            file_path = os.path.join(storage_dir, filename)

            async with aiofiles.open(file_path, 'wb') as file:
                # Записываем содержимое первого чанка
                await file.write(first_chunk.content)
                bytes_written = len(first_chunk.content)
                logger.debug(f"Записан первый чанк: {bytes_written} байт")
                
                # Записываем остальные чанки
                async for chunk in request_iterator:
                    await file.write(chunk.content)
                    bytes_written += len(chunk.content)
                    logger.debug(f"Записан чанк: {len(chunk.content)} байт")
                
            logger.info(f"Файл {filename} успешно загружен. Всего записано: {bytes_written} байт")
            return file_service_pb2.UploadResponse(message=f"File {filename} uploaded successfully.")
            
        except StopAsyncIteration:
            error_msg = "No data received"
            logger.error(error_msg)
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return file_service_pb2.UploadResponse(message="Upload failed: no data received")
        except Exception as e:
            error_msg = f"Ошибка при загрузке файла: {str(e)}"
            logger.error(error_msg, exc_info=True)
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.INTERNAL)
            return file_service_pb2.UploadResponse(message=f"Upload failed: {str(e)}")

    async def DownloadFile(self, request, context):
        filename = request.filename
        file_path = os.path.join("../storage", filename)
        
        logger.info(f"Запрос на скачивание файла: {filename}")
        
        if not os.path.exists(file_path):
            error_msg = f"File not found: {filename}"
            logger.error(error_msg)
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return

        try:
            async with aiofiles.open(file_path, 'rb') as file:
                bytes_sent = 0
                while True:
                    chunk = await file.read(1024 * 1024)  # 1MB
                    if not chunk:
                        break
                    bytes_sent += len(chunk)
                    logger.debug(f"Отправлен чанк: {len(chunk)} байт")
                    yield file_service_pb2.FileChunk(filename=filename, content=chunk)
                
                logger.info(f"Файл {filename} успешно отправлен. Всего отправлено: {bytes_sent} байт")
        except Exception as e:
            error_msg = f"Ошибка при чтении файла {filename}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.INTERNAL)
            return


async def serve():
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
        ]
    )
    file_service_pb2_grpc.add_FileServiceServicer_to_server(FileService(), server)
    server.add_insecure_port('[::]:50051')
    
    logger.info("Запуск gRPC сервера на порту 50051")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    import asyncio
    logger.info("Инициализация gRPC сервера")
    asyncio.run(serve())
