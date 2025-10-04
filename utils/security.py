import bcrypt
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from config import JWT_SECRET

#Create password hash for storing in the DB
def hashPassword(password: str) -> bytes:
    hashedPassword = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashedPassword.decode('utf-8')

#Check entered password matches the hashed password in the DB
def checkPassword(password: str, hashedPassword: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashedPassword.encode('utf-8'))

#Issue cross site forgery request token
def issueCSFR() -> str:
    return str(uuid.uuid4())

#Issue the JWT
def issueJWT(csfrToken: str, userId: int, email: str) -> str:
    payload = {
        "userId": userId,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=4),
        "csfr": csfrToken
    }

    return jwt.encode(payload, JWT_SECRET, "HS256")

#Authenticate user with JWT and claims
def isAuthenticated(csfrToken: str, jwtToken: str) -> bool:
    #jwt.decode automatically throws exception if token expired. Wrap this code in try catch
    #so we can return false for easier handling rather than reading exception types
    try:
        decodedJwt = jwt.decode(jwtToken, JWT_SECRET, "HS256")
        jCsfr = decodedJwt["csfr"]
        
        if (jCsfr == csfrToken):
            return True
        else:
            return False
    except Exception as e:
        return False