from datetime import timedelta
from fastapi import Cookie, FastAPI, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session, exists, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload
import uvicorn
from models.db_models import Shared, Snip, User
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
        user = session.exec(select(User).where(User.email == login.email)).first()

        if (user is None or not checkPassword(login.password, user.password)):
            raise HTTPException(401, "Invalid email or password")

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

        subQ = select(exists().where(Snip.snipid == Shared.snipid and Snip.userid == Shared.userid)).scalar_subquery()
        snips = session.exec(select(
            Snip.snipid, 
            Snip.sniplanguage, 
            Snip.snipname, 
            Snip.snipdescription, 
            Snip.lastmodified,
            subQ.label("snipshared")
        ).where(Snip.userid == userid)).all()

        return snips
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")

@app.get('/getSettings', response_model=SettingsResponse)
async def getSettings(request: Request, snipsnap_jwt: str = Cookie(None), session: Session = Depends(get_session)) -> SettingsResponse:
    try:
        csfr = request.headers.get("snipsnap_csfr")

        if (not isAuthenticated(csfr, snipsnap_jwt)):
            raise HTTPException(401, "Unauthorized")
        
        userid = getUserIdFromJwt(snipsnap_jwt)
        settings = session.exec(select(User).where(User.userid == userid).options(selectinload(User.contacts))).first()

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

#for debugging
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)