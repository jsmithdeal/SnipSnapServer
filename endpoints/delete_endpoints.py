from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, Request
from sqlmodel import Session, delete
from sqlalchemy.exc import SQLAlchemyError
from models.db_models import Collection, Contact, Snip, User
from models.http.request_models import *
from models.http.response_models import *
from config import get_session
from utils.security import *

delete_router = APIRouter(prefix="")

#Delete the account. Unvalidates tokens to ensure logout on delete
@delete_router.delete('/deleteAccount')
async def deleteAccount(response: Response, request: Request, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    try:
        csrf = request.headers.get("snipsnap_csrf")
        userid = getAuthenticatedUser(csrf, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        session.exec(delete(User).where(User.userid == userid))
        session.commit()

        response.set_cookie(
            key="snipsnap_jwt",
            expires=0,
            path="/",
            secure=False,
            httponly=True,
            samesite="lax"
        )

        response.set_cookie(
            key="snipsnap_csrf",
            expires=0,
            path="/",
            secure=False,
            httponly=False,
            samesite="lax"
        )
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    
#Delete a contact
@delete_router.delete('/deleteContact/{contactId}')
async def deleteContact(request: Request, contactId: int, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    try:
        csrf = request.headers.get("snipsnap_csrf")
        userid = getAuthenticatedUser(csrf, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        session.exec(delete(Contact).where((Contact.userid == userid) & (Contact.contactid == contactId)))
        session.commit()
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    
#Delete a snip
@delete_router.delete('/deleteSnip/{snipId}')
async def deleteSnip(request: Request, snipId: int, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    try:
        csrf = request.headers.get("snipsnap_csrf")
        userid = getAuthenticatedUser(csrf, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        session.exec(delete(Snip).where((Snip.userid == userid) & (Snip.snipid == snipId)))
        session.commit()
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    
#Delete a collection
@delete_router.delete('/deleteCollection/{collId}')
async def deleteCollection(request: Request, collId: int, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    try:
        csrf = request.headers.get("snipsnap_csrf")
        userid = getAuthenticatedUser(csrf, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        session.exec(delete(Collection).where((Collection.userid == userid) & (Collection.collectionid == collId)))
        session.commit()
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))