from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from models.db_models import Snip, User
from models.http.request_models import *
from models.http.response_models import *
from config import get_session
from utils.security import *

get_router = APIRouter(prefix="")

#Get list of snips for user
@get_router.get("/getSnips", response_model=List[SnipsResponse])
async def getSnips(request: Request, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> List[SnipsResponse]:
    try:
        csfr = request.headers.get("snipsnap_csfr")
        userid = getAuthenticatedUser(csfr, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        #Had to execute the query first THEN build the object. Previously had used a subquery with
        #exists() to determine if a record for the snip was in the shared table. SQL alchemy was appending
        #the snips table to the FROM clause, causing snipshared to be true for all snips for a user
        query = session.exec(select(Snip)
                    .where(Snip.userid == userid)
                    .options(selectinload(Snip.sharedwith)))
        
        snips = ({
            "snipid": snip.snipid,
            "sniplanguage": snip.sniplanguage,
            "snipname": snip.snipname,
            "snipdescription": snip.snipdescription,
            "lastmodified": snip.lastmodified,
            "snipshared": True if len(snip.sharedwith) > 0 else False
        } for snip in query)

        return snips
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")
    
#Get information needed to create a new snip
@get_router.get("/getSnipInit", response_model=SnipInitResponse)
async def getSnipInit(request: Request, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> SnipInitResponse:
    try:
        csfr = request.headers.get("snipsnap_csfr")
        userid = getAuthenticatedUser(csfr, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        userinfo = session.exec(select(User).where(User.userid == userid)).first()

        return SnipInitResponse(
            contacts=userinfo.contacts,
            collections=userinfo.collections
        )
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")
    
#Get details about a snip
@get_router.get('/getSnipDetails/{snipId}', response_model=SnipDetailsResponse)
async def getSnipDetails(request: Request, snipId: int, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> SnipDetailsResponse:
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (getAuthenticatedUser(csfr, snipsnap_jwt) <= -1):
            raise HTTPException(401, "Unauthorized")
        
        snipDetails = session.exec(select(Snip)
                                .where(Snip.snipid == snipId)
                                .options(
                                    selectinload(Snip.sharedwith),
                                    selectinload(Snip.user).selectinload(User.collections),
                                    selectinload(Snip.user).selectinload(User.contacts) #selectinload gets attributes for this snip and user as defined in db model relationships
                                )).first()

        return SnipDetailsResponse(
            snipid=snipDetails.snipid,
            snipname=snipDetails.snipname,
            snipdescription=snipDetails.snipdescription,
            sniplanguage=snipDetails.sniplanguage,
            snipcontent=snipDetails.snipcontent,
            collectionid=snipDetails.collectionid,
            lastmodified=snipDetails.lastmodified,
            snipshared=(True if len(snipDetails.sharedwith) > 0 else False),
            collections=snipDetails.user.collections,
            contacts=snipDetails.user.contacts,
            sharedwith=[c.contactid for c in snipDetails.sharedwith]
        )
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")
    
#Get the object to populate the settings page
@get_router.get('/getSettings', response_model=SettingsResponse)
async def getSettings(request: Request, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> SettingsResponse:
    try:
        csfr = request.headers.get("snipsnap_csfr")
        userid = getAuthenticatedUser(csfr, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        settings = session.exec(select(User).where(User.userid == userid).options(selectinload(User.contacts))).first() #selectinload gets the contacts for this user as defined in db model relationships

        return SettingsResponse(
            email=settings.email,
            firstname=settings.firstname,
            lastname=settings.lastname,
            contacts=settings.contacts
        )
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")