from typing import List
from models.http.base_http_models import *

class UserResponse(UserBase):
    pass

class SnipsResponse(SnipBase):
    pass

class ContactsResponse(ContactsBase):
    pass

class SettingsResponse(UserBase):
    contacts: List[ContactsResponse]