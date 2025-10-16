from models.http.base_http_models import *

class CreateUserRequest(UserBase):
    password: str

class LoginRequest(SQLModel):
    email: str
    password: str

class UpdateUserRequest(UserBase):
    pass

class CreateContactRequest(SQLModel):
    email: str
    displayname: str