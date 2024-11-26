from fastapi import FastAPI, UploadFile
import grpc_client as gh

app = FastAPI()

@app.get("/files/{filename}")
async def get_file(filename: str = None):
    response = await gh.get_file_from_service(filename)
    return {"file": response.content}


@app.post("/files/upload/")
async def upload_file(file: UploadFile):
    response = await gh.send_file_to_file_service(file)
    return {"message": response}