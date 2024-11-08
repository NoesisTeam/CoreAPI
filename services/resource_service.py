from fastapi import Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse

from models.responses import ResourceToUpload
from core.app_settings import get_settings
from repositories.resource_repository import ResourceRepository
import boto3

settings = get_settings()
class ResourceService:
    def __init__(self):
        self.repository = ResourceRepository()


    # 2592000 = 30 days
    def upload_resource(self, info: ResourceToUpload, file: UploadFile = File(...)):
        if file.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        filename = info.title + ".pdf"
        bucket_name = get_settings().AWS_BUCKET_NAME
        key = f"readings/{filename}"
        self.get_s3_client().upload_fileobj(file.file, bucket_name, key)
        url = self.get_s3_client().generate_presigned_url('get_object',
                                                Params={'Bucket': bucket_name, 'Key': key},
                                                ExpiresIn=2592000)
        return self.repository.create_resource(info, url)

    def get_resource_file(self, resource_id: int):
        # Obtiene la información del recurso desde la base de datos
        resource = self.repository.get_resource_by_id(resource_id)

        if not resource or not resource.url:
            raise HTTPException(status_code=404, detail="Resource not found")

        bucket_name = get_settings().AWS_BUCKET_NAME
        key = f"readings/{resource.title}.pdf"

        s3_client = self.get_s3_client()
        file_stream = s3_client.get_object(Bucket=bucket_name, Key=key)["Body"]

        # Retorna el archivo como un StreamingResponse
        return StreamingResponse(file_stream, media_type="application/pdf")

    def get_all_resources_by_club(self, club_id: int):
        return self.repository.get_all_resources_by_club(club_id)

    def delete_resource(self, resource_id: int):
        return self.repository.delete_resource(resource_id)

    def get_s3_client(self):
        return boto3.client('s3',
                            aws_access_key_id=get_settings().AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=get_settings().AWS_SECRET_ACCESS_KEY)
