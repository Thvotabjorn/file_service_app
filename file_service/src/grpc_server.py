import os
from concurrent import futures
import grpc
import file_service_pb2_grpc, file_service_pb2

class FileService(file_service_pb2_grpc.FileServiceServicer):
    def UploadFile(self, request_iterator, context):
        filename = "uploaded_file"  # You can modify this to accept filename from client
        with open(filename, 'wb') as f:
            for chunk in request_iterator:
                f.write(chunk.content)
        return file_service_pb2.UploadResponse(message="File uploaded successfully.")

    def DownloadFile(self, request, context):
        filename = request.filename
        if not os.path.exists(filename):
            context.set_details("File not found.")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return

        with open(filename, 'rb') as f:
            while True:
                chunk = f.read(1024)  # Read in chunks of 1024 bytes
                if not chunk:
                    break
                yield file_service_pb2.FileChunk(content=chunk)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_service_pb2_grpc.add_FileServiceServicer_to_server(FileService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()