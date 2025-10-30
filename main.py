from datetime import timedelta
from fastapi import Cookie, FastAPI, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session, exists, select, update, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload
import uvicorn
from models.db_models import Contact, Shared, Snip, User
from models.http.request_models import *
from models.http.response_models import *
from config import get_session, init_db
from utils.security import *

app = FastAPI()

#for debugging
origins = [
    "http://localhost:5173" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     
    allow_credentials=True,
    allow_methods=["*"],       
    allow_headers=["*"],       
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

#Sign up form endpoint
@app.post('/create-user')
async def create_user(user: CreateUserRequest, session: Session = Depends(get_session)):
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
            raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")

#Login form endpoint
@app.post('/login')
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
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")

#Log the user out by expiring tokens
@app.post("/logout")
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
        raise HTTPException(500, "There was an error processing your request")

#Get list of snips for user
@app.get("/getSnips", response_model=List[SnipsResponse])
async def getSnips(request: Request, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> List[SnipsResponse]:
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (not isAuthenticated(csfr, snipsnap_jwt)):
            raise HTTPException(401, "Unauthorized")
        
        userid = getUserIdFromJwt(snipsnap_jwt)
        
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

#Get the object to populate the settings page
@app.get('/getSettings', response_model=SettingsResponse)
async def getSettings(request: Request, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> SettingsResponse:
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (not isAuthenticated(csfr, snipsnap_jwt)):
            raise HTTPException(401, "Unauthorized")
        
        userid = getUserIdFromJwt(snipsnap_jwt)
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

#Get details about a snip
@app.get('/getSnipDetails/{snipId}', response_model=SnipDetailsResponse)
async def getSnipDetails(request: Request, snipId: int, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> SnipDetailsResponse:
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (not isAuthenticated(csfr, snipsnap_jwt)):
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

#Check the validity of the jwt token and ensure the csfr token matches what is encoded in the jwt
@app.post('/checkAuth')
async def checkAuth(request: Request, snipsnap_jwt: str = Cookie(None)):
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (not isAuthenticated(csfr, snipsnap_jwt)):
            raise HTTPException(401, "Unauthorized")
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")

#Save user info editable on the settings page
@app.patch('/saveUserInfo')
async def saveUserInfo(request: Request, updateReq: UpdateUserRequest, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (not isAuthenticated(csfr, snipsnap_jwt)):
            raise HTTPException(401, "Unauthorized")
        
        userid = getUserIdFromJwt(snipsnap_jwt)
        session.exec(update(User).where(User.userid == userid).values(email=updateReq.email, firstname=updateReq.firstname, lastname=updateReq.lastname))
        session.commit()
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")

#Delete the account. Unvalidates tokens to ensure logout on delete
@app.delete('/deleteAccount')
async def deleteAccount(response: Response, request: Request, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (not isAuthenticated(csfr, snipsnap_jwt)):
            raise HTTPException(401, "Unauthorized")
        
        userid = getUserIdFromJwt(snipsnap_jwt)
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
            key="snipsnap_csfr",
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
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")
    
#Delete a contact
@app.delete('/deleteContact/{contactId}')
async def deleteContact(request: Request, contactId: int, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)):
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (not isAuthenticated(csfr, snipsnap_jwt)):
            raise HTTPException(401, "Unauthorized")
        
        userid = getUserIdFromJwt(snipsnap_jwt)
        session.exec(delete(Contact).where(Contact.userid == userid and Contact.contactid == contactId))
        session.commit()
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")

#Create a new contact
@app.post('/createContact')
async def createContact(request: Request, contactReq: CreateContactRequest, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> int:
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (not isAuthenticated(csfr, snipsnap_jwt)):
            raise HTTPException(401, "Unauthorized")
        
        userid = getUserIdFromJwt(snipsnap_jwt)
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
            raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")

#for debugging
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)