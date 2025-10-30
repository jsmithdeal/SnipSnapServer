from models.http.base_http_models import *

class UpdateUserRequest(UserBase):
    pass

class CreateUserRequest(UserBase):
    password: str

class LoginRequest(SQLModel):
    email: str
    password: str

class CreateContactRequest(SQLModel):
    email: str
    displayname: str