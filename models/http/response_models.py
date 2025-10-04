from models.http.base_http_models import *

class UserResponse(UserBase):
    userid: int

class AuthenticatedResponse(BaseModel):
    csfrToken: str
    jwtToken: str
    user: UserResponse