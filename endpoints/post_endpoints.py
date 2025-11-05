from datetime import timedelta
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, Request
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from models.db_models import Collection, Contact, Shared, Snip, User
from models.http.request_models import *
from models.http.response_models import *
from config import get_session
from utils.security import *

post_router = APIRouter(prefix="")

#Sign up form endpoint
@post_router.post('/createUser')
async def createUser(user: CreateUserRequest, session: Session = Depends(get_session)):
    try:
        #Dump user to model, reset password to hashed version, and insert to db
        user = User(**user.model_dump())
        user.password = hashPassword(user.password)
        session.add(user)
        session.commit()
        session.refresh(user)
    except SQLAlchemyError as e:
        session.rollback()

        if isinstance(e, IntegrityError):
            raise HTTPException(409, "This email is taken")
        else:
            raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

#Login form endpoint
@post_router.post('/login')
async def login(response: Response, login: LoginRequest, session: Session = Depends(get_session)):
    try:
        #Check user with email exists
        user = session.exec(select(User).where(User.email == login.email)).first()

        #Check password is correct for user
        if (user is None or not checkPassword(login.password, user.password)):
            raise HTTPException(401, "Invalid email or password")

        #If validated, issue tokens and return to client
        expDate = datetime.now(timezone.utc) + timedelta(hours=4)
        tokens = issueTokens(user.userid, user.email, expDate)
        csfr = tokens[0]
        jwt = tokens[1]

        if ((tokens is None or not csfr) or (jwt is None or not jwt)):
            raise HTTPException(500, "Failed to issue tokens")
        
        response.set_cookie(
            key="snipsnap_jwt",
            value=jwt,
            expires=expDate,
            path="/",
            secure=False,
            httponly=True,
            samesite="lax"
        )

        response.set_cookie(
            key="snipsnap_csfr",
            value=csfr,
            expires=expDate,
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

#Log the user out by expiring tokens
@post_router.post("/logout")
async def logout(response: Response):
    try:
        response.set_cookie(
            key="snipsnap_jwt",
            expires=0,
            path="/",
            secure=False,
            httponly=True,
            samesite="lax"
        )

        response.set_cookie(
            key="snipsnap_csfr",
            expires=0,
            path="/",
            secure=False,
            httponly=False,
            samesite="lax"
        )
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    
#Create a new contact
@post_router.post('/createContact')
async def createContact(request: Request, contactReq: CreateContactRequest, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> int:
    try:
        csfr = request.headers.get("snipsnap_csfr")
        userid = getAuthenticatedUser(csfr, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        contactId = session.exec(select(User.userid).where(User.email == contactReq.email)).first()

        #Create a new contact using the user id associated with the email in the contact request
        if (contactId is not None):
            contact = Contact(**contactReq.model_dump())
            contact.userid = userid
            contact.contactid = contactId
            session.add(contact)
            session.commit()
            session.refresh(contact)
            return contact.contactid
        else:
            raise HTTPException(404, "No users found with this email address")
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()

        if isinstance(e, IntegrityError):
            raise HTTPException(409, "This user is already one of your contacts")
        else:
            raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    
#Check the validity of the jwt token and ensure the csfr token matches what is encoded in the jwt
@post_router.post('/checkAuth')
async def checkAuth(request: Request, snipsnap_jwt: str = Cookie(None)):
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (getAuthenticatedUser(csfr, snipsnap_jwt) <= -1):
            raise HTTPException(401, "Unauthorized")
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    
#Create snip endpoint
@post_router.post('/createSnip')
async def createSnip(request: Request, snipreq: SaveSnipRequest, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    secondCommit=False

    try:
        csfr = request.headers.get("snipsnap_csfr")
        userid = getAuthenticatedUser(csfr, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        collection = session.exec(select(Collection.collectionid).where((Collection.userid == userid) & (Collection.collectionid == snipreq.collectionid))).first()

        if (snipreq.collectionid is not None and collection is None):
            raise HTTPException(500, "Unable to create snip")
        
        snip = Snip(
            userid=userid,
            snipname=snipreq.snipname,
            snipdescription=snipreq.snipdescription,
            sniplanguage=snipreq.sniplanguage,
            snipcontent=snipreq.snipcontent,
            collectionid=snipreq.collectionid
        )

        session.add(snip)
        session.commit()
        session.refresh(snip)

        if len(snipreq.sharedwith) > 0:
            secondCommit=True
            sharedwith: List[Shared] = [Shared(snipid=snip.snipid, userid=userid, contactid=contactid) for contactid in snipreq.sharedwith]
            session.add_all(sharedwith)
            session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, "Snip created, but there was a problem sharing with contacts" if secondCommit else str(e))
    except Exception as e:
        raise HTTPException(500, "Snip created, but there was a problem sharing with contacts" if secondCommit else str(e))
    
#Add collection
@post_router.post('/createCollection/{collName}')
async def createCollection(request: Request, collName: str, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> int:
    try:
        csfr = request.headers.get("snipsnap_csfr")
        userid = getAuthenticatedUser(csfr, snipsnap_jwt)

        if (userid <= -1):
            raise HTTPException(401, "Unauthorized")
        
        collection = Collection(userid=userid, collectionname=collName)
        session.add(collection)
        session.commit()
        session.refresh(collection)
        
        return collection.collectionid
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))