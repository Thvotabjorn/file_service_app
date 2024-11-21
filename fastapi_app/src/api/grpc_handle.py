from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import grpc
import file_service_pb2_grpc as grpc_service
import file_service_pb2 as grpc_messages


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