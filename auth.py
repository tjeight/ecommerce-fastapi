from datetime import datetime, timedelta, timezone
from jose import jwt
from dotenv import load_dotenv
import os
from admin_schemas import User
from database import get_db
from models import Users
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

o_auth_schemes = OAuth2PasswordBearer(tokenUrl="/login")


def create_access_token(data: dict, expire_time: timedelta | None = None):
    to_encode = data.copy()
    if expire_time:
        exp_time = datetime.now(timezone.utc) + expire_time
    else:
        exp_time = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp_time": exp_time.isoformat()})
    return jwt.encode(to_encode, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))


def get_current_user(
    token: str = Depends(o_auth_schemes), db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
        username = payload.get("sub")
        found_user = db.query(Users).filter(Users.email == username).first()
        if not found_user:
            return {"messsage": "Expired token"}
        return User(
            email=found_user.email, role=found_user.role, user_id=found_user.user_id
        )
    except Exception as e:
        raise e


def admin_required(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return current_user


def user_required(current_user: User = Depends(get_current_user)):
    if current_user.role != "user":
        raise HTTPException(status_code=403, detail="Users only")
    return current_user
