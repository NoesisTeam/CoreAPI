from fastapi import Depends, HTTPException, status, UploadFile, File

from models.responses import Resource
from repositories.resource_repository import ResourceRepository


class ResourceService:
    def __init__(self):
        self.repository = ResourceRepository()

    def get_resource(self, resource_id: int):
        # TODO consultar url y traer el recurso
        url = self.repository.get_resource(resource_id)
        return url

    def upload_resource(self, info: Resource,file: UploadFile = File(...)):
        #TODO subir archivo a s3 y obtener la url
        return self.repository.create_resource(info.id, file.filename)

    def delete_resource(self, resource_id: int):
        return self.repository.delete_resource(resource_id)
