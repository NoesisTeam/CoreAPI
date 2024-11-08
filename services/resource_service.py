from fastapi import Depends, HTTPException, status, UploadFile, File
from models.responses import Resource
from core.app_settings import get_settings
from repositories.resource_repository import ResourceRepository
import boto3

class ResourceService:
    def __init__(self):
        self.repository = ResourceRepository()

    def get_resource(self, resource_id: int):
        # TODO consultar url y traer el recurso
        url = self.repository.get_resource(resource_id)
        return url

    # 2592000 = 30 days
    def upload_resource(self, info: Resource,file: UploadFile = File(...)):
        if file.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        else:
            filename = info.title + ".pdf"
            bucket_name = get_settings().AWS_BUCKET_NAME
            key = f"readings/{filename}"
            s3_client = self.get_s3_client().upload_file(file.file, bucket_name, key)
            url = s3_client.generate_presigned_url('get_object',
                                                   Params={'Bucket': bucket_name, 'Key': key},
                                                   ExpiresIn=2592000)
            return self.repository.create_resource(info, url)

    def delete_resource(self, resource_id: int):
        return self.repository.delete_resource(resource_id)

    def get_s3_client(self):
        return boto3.client('s3',
                            aws_access_key_id=get_settings().AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=get_settings().AWS_SECRET_ACCESS_KEY)
