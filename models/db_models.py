from sqlmodel import Field, PrimaryKeyConstraint, Relationship, SQLModel
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

class Snip(SQLModel, table=True):
    __tablename__ = "snips"
    snipid: int = Field(default=None, primary_key=True)
    userid: int
    collectionid: int
    snipname: str
    sniplanguage: str
    snipdescription: str
    snipcontent: str
    createdon: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) 
    lastmodified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Shared(SQLModel, table=True):
    __tablename__ = "shared"
    __table_args__ = (
        PrimaryKeyConstraint("snipid", "userid", "contactid"), #must have primary key defined. Trailing comma necessary to indicate tuple type
    )
    snipid: int
    userid: int
    contactid: int