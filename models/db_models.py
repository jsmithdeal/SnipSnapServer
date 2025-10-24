from typing import List
from sqlmodel import Field, ForeignKeyConstraint, PrimaryKeyConstraint, Relationship, SQLModel
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

    #Non-column ORM relationships
    contacts: List["Contact"] = Relationship(back_populates="user", sa_relationship_kwargs={"foreign_keys": "Contact.userid"})
    collections: List["Collection"] = Relationship(back_populates="user", sa_relationship_kwargs={"foreign_keys": "Collection.userid"})
    snips: List["Snip"] = Relationship(back_populates="user", sa_relationship_kwargs={"foreign_keys": "Snip.userid"})

class Collection(SQLModel, table=True):
    __tablename__ = "collections"
    collectionid: int = Field(default=None, primary_key=True)
    userid: int = Field(foreign_key="users.userid")
    collectionname: str
    createdon: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    lastmodified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    #Non-column ORM relationships
    user: User = Relationship(back_populates="collections", sa_relationship_kwargs={"foreign_keys": "Collection.userid"})

class Snip(SQLModel, table=True):
    __tablename__ = "snips"
    snipid: int = Field(default=None, primary_key=True)
    userid: int = Field(foreign_key="users.userid")
    collectionid: int = Field(foreign_key="collections.collectionid")
    snipname: str
    sniplanguage: str
    snipdescription: str
    snipcontent: str
    createdon: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) 
    lastmodified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    #Non-column ORM relationships
    user: User = Relationship(back_populates="snips", sa_relationship_kwargs={"foreign_keys": "Snip.userid"})
    sharedwith: List["Shared"] = Relationship(back_populates="snip", sa_relationship_kwargs={"foreign_keys": "Shared.snipid"})

class Contact(SQLModel, table=True):
    __tablename__ = "contacts"
    __table_args__ = (
        PrimaryKeyConstraint("userid", "contactid"), #must have primary key defined. Trailing comma necessary to indicate tuple type
    )
    userid: int = Field(foreign_key="users.userid")
    contactid: int = Field(foreign_key="users.userid")
    displayname: str

    #Non-column ORM relationships
    user: User = Relationship(back_populates="contacts", sa_relationship_kwargs={"foreign_keys": "Contact.userid"})

class Shared(SQLModel, table=True):
    __tablename__ = "shared"
    __table_args__ = (
        PrimaryKeyConstraint("snipid", "userid", "contactid"),
        ForeignKeyConstraint(
            ["userid", "contactid"],
            ["contacts.userid", "contacts.contactid"]
        ),
    )
    snipid: int = Field(foreign_key="snips.snipid")
    userid: int
    contactid: int

    #Non-column ORM relationships
    snip: Snip = Relationship(back_populates="sharedwith", sa_relationship_kwargs={"foreign_keys": "Shared.snipid"})