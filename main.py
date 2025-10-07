from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from sqlalchemy.exc import *
import uvicorn
from models.db_models import User
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
async def login(response: Response, login: LoginRequest, session: Session = Depends(get_session)) -> UserResponse:
    try:
        userInfo = session.exec(select(User).where(User.email == login.email)).first()

        if (userInfo == None or not checkPassword(login.password, userInfo.password)):
            raise HTTPException(401, "Invalid email or password")

        expDate = datetime.now(timezone.utc) + timedelta(hours=4)
        tokens = issueTokens(userInfo.userid, userInfo.email, expDate)
        csfr = tokens[0]
        jwt = tokens[1]

        if ((tokens is None or not csfr) or (jwt is None or not jwt)):
            raise HTTPException(500, "Failed to issue tokens")
        
        response.set_cookie(
            key="snipsnap-jwt",
            value=jwt,
            expires=expDate,
            path="/",
            secure=False,
            httponly=True,
            samesite="lax"
        )

        response.set_cookie(
            key="snipsnap-csfr",
            value=csfr,
            expires=expDate,
            path="/",
            secure=False,
            httponly=False,
            samesite="lax"
        )

        return UserResponse(
                userid=userInfo.userid, 
                email=userInfo.email, 
                firstname=userInfo.firstname, 
                lastname=userInfo.lastname
            )
    except HTTPException as e:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(500, "There was an error processing your request")
    except Exception as e:
        raise HTTPException(500, "There was an error processing your request")

#for debugging
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)