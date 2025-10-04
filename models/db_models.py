from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime, timezone

class User(SQLModel, table=True):
    __tablename__ = 'users'
    userid: int = Field(default=None, primary_key=True)
    email: str
    password: str
    firstname: str
    lastname: str
    createdon: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) #since args need to be passed to datetime.now(), lamba delays execution to prevent the funtion being called immediately at runtime
    lastmodified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))