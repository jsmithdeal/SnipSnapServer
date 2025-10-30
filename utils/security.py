import bcrypt
import jwt
import uuid
from datetime import datetime, timezone
from config import JWT_SECRET

#Create password hash for storing in the DB
def hashPassword(password: str) -> bytes:
    hashedPassword = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashedPassword.decode('utf-8')

#Check entered password matches the hashed password in the DB
def checkPassword(password: str, hashedPassword: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashedPassword.encode('utf-8'))

#Issue new csfr and jwt tokens
def issueTokens(userId: int, email: str, tokenExp: datetime) -> tuple:
    csfrToken = str(uuid.uuid4())
    jwtToken = jwt.encode({
        "userId": userId,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": tokenExp,
        "csfr": csfrToken
    }, JWT_SECRET, "HS256")

    return (csfrToken, jwtToken)

#Authenticate user with JWT and claims. Return user ID if authenticated, else -1
def getAuthenticatedUser(csfrToken: str, jwtToken: str) -> bool:
    #jwt.decode automatically throws exception if token expired. Wrap this code in try catch
    #so we can return -1 for easier handling rather than reading exception types
    try:
        decodedJwt = jwt.decode(jwtToken, JWT_SECRET, "HS256")
        jCsfr = decodedJwt["csfr"]
        
        if jCsfr == csfrToken:
            return decodedJwt["userId"]
        
        return -1
    except Exception as e:
        return -1