import os
from concurrent import futures

import aiofiles
import grpc
import file_service_pb2_grpc, file_service_pb2

class FileService(file_service_pb2_grpc.FileServiceServicer):
    async def UploadFile(self, request_iterator, context):
        filename = "uploaded_file"  #TODO передать имя файла, полученное от клиента
        async with aiofiles.open(filename, 'wb') as file:
            for chunk in request_iterator:
                file.write(chunk.content)
        return file_service_pb2.UploadResponse(message="File uploaded successfully.")

    async def DownloadFile(self, request, context):
        filename = request.filename
        if not os.path.exists(filename):
            context.set_details("File not found.")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return

        with aiofiles.open(filename, 'rb') as file:
            while True:
                chunk = file.read(1024)  # Read in chunks of 1024 bytes
                if not chunk:
                    break
                yield file_service_pb2.FileChunk(content=chunk)


def run():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_service_pb2_grpc.add_FileServiceServicer_to_server(FileService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    run()
