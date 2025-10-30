from typing import List
from pydantic import BaseModel
from models.http.base_http_models import *

class UserResponse(UserBase):
    pass

class SnipsResponse(SnipBase):
    pass

class ContactsResponse(ContactsBase):
    pass

class CollectionResponse(CollectionBase):
    pass

class SettingsResponse(UserBase):
    contacts: List[ContactsResponse]

class SnipDetailsResponse(SnipBase):
    snipcontent: str
    collectionid: int | None
    collections: List[CollectionResponse]
    contacts: List[ContactsResponse]
    sharedwith: List[int]

class SnipInitResponse(BaseModel):
    contacts: List[ContactsResponse]
    collections: List[CollectionResponse]