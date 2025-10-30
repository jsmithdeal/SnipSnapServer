from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from sqlmodel import Session, update
from sqlalchemy.exc import SQLAlchemyError
from models.db_models import User
from models.http.request_models import *
from models.http.response_models import *
from config import get_session
from utils.security import *

patch_router = APIRouter(prefix="")

#Save user info editable on the settings page
@patch_router.patch('/saveUserInfo')
async def saveUserInfo(request: Request, updateReq: UpdateUserRequest, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    try:
        csfr = request.headers.get("snipsnap_csfr")
        userid = getAuthenticatedUser(csfr, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        session.exec(update(User).where(User.userid == userid).values(email=updateReq.email, firstname=updateReq.firstname, lastname=updateReq.lastname))
        session.commit()
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")