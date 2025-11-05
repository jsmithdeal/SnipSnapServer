from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from sqlmodel import Session, delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from models.db_models import Collection, Shared, Snip, User
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
        
        session.exec(update(User).where(User.userid == userid).values(
            email=updateReq.email, 
            firstname=updateReq.firstname, 
            lastname=updateReq.lastname, 
            lastmodified=updateReq.lastmodified
        ))
        session.commit()
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    
#Create snip endpoint
@patch_router.patch('/editSnip')
async def editSnip(request: Request, snip: SaveSnipRequest, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    try:
        csfr = request.headers.get("snipsnap_csfr")
        userid = getAuthenticatedUser(csfr, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")

        collection = session.exec(select(Collection.collectionid).where((Collection.userid == userid) & (Collection.collectionid == snip.collectionid))).first()

        if (snip.collectionid is not None and collection is None):
            raise HTTPException(500, "Unable to create snip")
        
        updateResult = session.exec(update(Snip).where((Snip.userid == userid) & (Snip.snipid == snip.snipid)).values(
            userid=userid,
            snipname=snip.snipname,
            snipdescription=snip.snipdescription,
            sniplanguage=snip.sniplanguage,
            snipcontent=snip.snipcontent,
            collectionid=snip.collectionid,
            lastmodified=snip.lastmodified
        ))

        if (updateResult.rowcount > 0):
            session.exec(delete(Shared).where((Shared.userid == userid) & (Shared.snipid == snip.snipid)))
        
            if len(snip.sharedwith) > 0:
                sharedwith: List[Shared] = [Shared(snipid=snip.snipid, userid=userid, contactid=contactid) for contactid in snip.sharedwith]
                session.add_all(sharedwith)
        else:
            raise HTTPException(500, "There was a problem updating the snip")
        
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    
#Edit collection name
@patch_router.patch('/editCollectionName')
async def editCollectionName(request: Request, updateReq: UpdateCollectionRequest, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    try:
        csfr = request.headers.get("snipsnap_csfr")
        userid = getAuthenticatedUser(csfr, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        session.exec(update(Collection).where((Collection.userid == userid) & (Collection.collectionid == updateReq.collectionid)).values(
            collectionname=updateReq.collectionname, 
            lastmodified=updateReq.lastmodified
        ))
        session.commit()
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))