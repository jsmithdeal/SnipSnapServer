from datetime import datetime
from sqlmodel import SQLModel

class UserBase(SQLModel):
    email: str
    firstname: str
    lastname: str

class ContactsBase(SQLModel):
    userid: int
    contactid: int
    displayname: str

class CollectionBase(SQLModel):
    collectionname: str
    collectionid: int

class SnipBase(SQLModel):
    snipid: int
    snipname: str
    sniplanguage: str
    snipdescription: str
    lastmodified: datetime
    snipshared: bool

    #Need this pydantic nested Config class to allow object mapping on select
    class Config:
        orm_mode = True