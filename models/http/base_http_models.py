from pydantic import BaseModel
from sqlmodel import SQLModel

class UserBase(SQLModel):
    email: str
    firstname: str
    lastname: str