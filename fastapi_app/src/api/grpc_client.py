import asyncio
from fastapi import UploadFile
import grpc
from starlette.responses import JSONResponse

import file_service_pb2_grpc as grpc_service
import file_service_pb2 as grpc_messages

from fastapi_app.src.settings import settings


async def grpc_file_client():
    channel = grpc.aio.insecure_channel(f'{settings.grpc_host}:{settings.grpc_port}')
    client = grpc_service.FileServiceStub(channel)
    return client


async def parse_message(message):
    parsed_message = message
    return parsed_message


async def get_file(message):
    return JSONResponse(await parse_message(message))


async def send_file_to_file_service(file: UploadFile):
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = grpc_service.FileServiceStub(channel)
        response = stub.UploadFile(grpc_messages.FileChunk(content=await file.read()))
        return response


async def get_file_from_service(filename: str):
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = grpc_service.FileServiceStub(channel)
        response = stub.DownloadFile(grpc_messages.DownloadRequest(filename=filename))
        return response


async def main():
    file = await get_file_from_service('test.txt')
    print(type(file))
    print(file)


if __name__ == '__main__':
    asyncio.run(main())
