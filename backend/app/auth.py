from datetime import timedelta, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from backend.app.database import SessionLocal, get_db
from backend.app.models import User

from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SECRET_KEY = "ASDFGACVCX776ADSF75DASFASDF6ASDF7"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

oauth2_bearer = HTTPBearer()


class CreateUserRequest(BaseModel):
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


db_dependency = Annotated[Session, Depends(get_db)]


# user registration endpoint
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    db: db_dependency,
    create_user_request: CreateUserRequest
):
    create_user_model = User(
        email=create_user_request.email,
        password_hash=bcrypt_context.hash(
            create_user_request.password
        ),
        full_name=create_user_request.full_name,
        role_id=1
    )

    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)

    return {
        "message": "User created",
        "email": create_user_model.email
    }


# login endpoint
@router.post("/token")
async def login(
    data: LoginRequest,
    db: db_dependency
):
    user = authenticate_user(
        data.email,
        data.password,
        db
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="could not validate user"
        )

    token = create_access_token(
        user.email,
        user.id,
        user.role_id,
        timedelta(minutes=20)
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# authentication helper
def authenticate_user(
    email: str,
    password: str,
    db
):
    user = db.query(User).filter(
        User.email == email
    ).first()

    # user does not exist
    if not user:
        return False

    # verify password against hashed password
    if not bcrypt_context.verify(
        password,
        user.password_hash
    ):
        return False

    return user


# JWT creation
def create_access_token(
    email: str,
    user_id: int,
    role_id: int,
    expires_delta: timedelta
):
    # payload stored inside token
    encode = {
        "sub": email,
        "user_id": user_id,
        "role_id": role_id
    }

    expires = datetime.utcnow() + expires_delta

    encode.update({
        "exp": expires
    })

    # Encode and return JWT
    return jwt.encode(
        encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# JWT validation dependency
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_bearer)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")
        user_id = payload.get("user_id")
        role_id = payload.get("role_id")

        # validate payload
        if email is None or user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate user, invalid token"
            )

        # return authenticated user context
        return {
            "email": email,
            "user_id": user_id,
            "role_id": role_id
        }

    except JWTError as e:
        # token invalid/expired/tampered
        print("JWT ERROR:", str(e))

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


# admin role verification
def require_admin(
    user=Depends(get_current_user)
):
    if user["role_id"] != 2:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return user


def require_analyst_or_admin(
    user=Depends(get_current_user)
):
    if user["role_id"] not in [2, 3]:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    return user