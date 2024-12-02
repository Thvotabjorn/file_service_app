import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import sys

from fastapi import UploadFile
from functools import partial
import grpc

import file_service_pb2_grpc as grpc_service
import file_service_pb2 as grpc_messages

from core.settings import settings

thread_pool = ThreadPoolExecutor(max_workers=5)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

async def run_sync_in_async(sync_func, *args, **kwargs):
    """Обертка для запуска синхронных функций в асинхронном контексте"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, partial(sync_func, *args, **kwargs))


async def file_chunk_iterator(file):
    bytes_sent = 0
    try:
        # Отправляем имя файла в первом чанке
        first_chunk = grpc_messages.FileChunk(
            filename=file.filename,
            content=await file.read(settings.CHUNK_SIZE)
        )
        bytes_sent += len(first_chunk.content)
        logger.debug(f"Подготовлен первый чанк: {len(first_chunk.content)} байт")
        yield first_chunk

        # Отправляем остальные чанки
        while True:
            chunk_data = await file.read(settings.CHUNK_SIZE)
            if not chunk_data:
                break
            bytes_sent += len(chunk_data)
            logger.debug(f"Подготовлен чанк: {len(chunk_data)} байт")
            yield grpc_messages.FileChunk(content=chunk_data)

        logger.info(f"Файл {file.filename} подготовлен к отправке. Всего: {bytes_sent} байт")
    except Exception as e:
        logger.error(f"Ошибка при подготовке файла {file.filename}: {str(e)}", exc_info=True)
        raise


async def send_file_to_file_service(file: UploadFile):
    try:
        logger.info(f"Начало отправки файла: {file.filename}")
        async with grpc.aio.insecure_channel(
            f'{settings.grpc_host}:{settings.grpc_port}',
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
            ]
        ) as channel:
            stub = grpc_service.FileServiceStub(channel)
            response = await stub.UploadFile(file_chunk_iterator(file))
            logger.info(f"Файл {file.filename} успешно отправлен")
            return response
    except grpc.RpcError as e:
        error_msg = f"gRPC ошибка при подготовке файла {file.filename}: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Ошибка при отправке файла {file.filename}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise


async def get_file_from_service(filename: str):
    try:
        logger.info(f"Запрос на получение файла: {filename}")
        async with grpc.aio.insecure_channel(
            f'{settings.grpc_host}:{settings.grpc_port}',
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
            ]
        ) as channel:
            stub = grpc_service.FileServiceStub(channel)
            response = await run_sync_in_async(
                stub.DownloadFile,
                grpc_messages.DownloadRequest(filename=filename)
            )
            
            chunks = []
            bytes_received = 0
            async for chunk in response:
                chunks.append(chunk.content)
                bytes_received += len(chunk.content)
                logger.debug(f"Получен чанк: {len(chunk.content)} байт")
            
            logger.info(f"Файл {filename} успешно получен. Всего: {bytes_received} байт")
            return b''.join(chunks)
    except grpc.RpcError as e:
        error_msg = f"gRPC ошибка при подготовке файла {filename}: {e.details()}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Ошибка при получении файла {filename}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise


async def main():
    file = await get_file_from_service('test.txt')
    print(type(file))
    print(file)


if __name__ == '__main__':
    asyncio.run(main())
