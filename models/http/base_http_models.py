from datetime import datetime
from sqlmodel import SQLModel

class UserBase(SQLModel):
    email: str
    firstname: str
    lastname: str

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