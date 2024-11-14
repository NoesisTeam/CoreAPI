import uuid

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
    def upload_resource(self, info: ResourceToUpload, id_club:int, file: UploadFile = File(...)):
        if file.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        file_uuid = str(uuid.uuid4())  # Esto generará un identificador único para el archivo
        filename = file_uuid + ".pdf"
        bucket_name = get_settings().AWS_BUCKET_NAME
        key = f"readings/{filename}"
        self.get_s3_client().upload_fileobj(file.file, bucket_name, key)
        url = self.get_s3_client().generate_presigned_url('get_object',
                                                Params={'Bucket': bucket_name, 'Key': key},
                                                ExpiresIn=2592000)
        return self.repository.create_resource(info, id_club, url)

    def get_resource_url(self, resource_id: int):
        return self.repository.get_resource_url(resource_id)

    def get_all_resources_by_club(self, club_id: int):
        return self.repository.get_all_resources_by_club(club_id)

    def get_ranking_by_resource(self, resource_id: int, club_id: int):
        return self.repository.get_ranking_by_resource(resource_id, club_id)

    def delete_resource(self, resource_id: int):
        return self.repository.delete_resource(resource_id)

    def get_s3_client(self):
        return boto3.client('s3',
                            aws_access_key_id=get_settings().AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=get_settings().AWS_SECRET_ACCESS_KEY)
