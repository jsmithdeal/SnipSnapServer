from typing import List
from models.http.base_http_models import *

class UpdateUserRequest(UserBase):
    pass

class UpdateCollectionRequest(CollectionBase):
    pass

class CreateUserRequest(UserBase):
    password: str

class LoginRequest(SQLModel):
    email: str
    password: str

class CreateContactRequest(SQLModel):
    email: str
    displayname: str

class SaveSnipRequest(SnipBase):
    snipcontent: str
    collectionid: int | None
    lastmodified: datetime
    sharedwith: List[int]