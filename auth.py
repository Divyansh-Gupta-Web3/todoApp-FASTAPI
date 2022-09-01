from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import models
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta, datetime
from jose import jwt,JWTError

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGORITHM = "HS256"

class CreateUser(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    password: str


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
models.Base.metadata.create_all(bind=engine)
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def vefiy_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return bcrypt_context.hash(password)

def create_access_token(username: str,user_id: int, expire_delta: Optional[timedelta] = None):
    encode={"sub": username, "id": user_id}
    if expire_delta:
        expire = datetime.utcnow() + expire_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=400, detail="Invalid authentication credentials")
        return {"username": username, "user_id": user_id}
    except JWTError:
        raise HTTPException(status_code=404, detail="Invalid authentication credentials")


@app.post("/create/user")
async def create_new_user(create_user: CreateUser, db: Session = Depends(get_db)):
    create_user_model = models.Users()
    create_user_model.email = create_user.email
    create_user_model.username = create_user.username
    create_user_model.first_name = create_user.first_name
    create_user_model.last_name = create_user.last_name
    create_user_model.hashed_password = create_user.password
    create_user_model.is_active = True
    db.add(create_user_model)
    db.commit()

    return {"message": "User created"}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.username == form_data.username).filter(models.Users.hashed_password==form_data.password).first()
    if not user:
        raise HTTPException(status_code=404, detail="Incorrect username or password")
    #set the expire time to 20 minutes
    token_expire = timedelta(minutes=20)
    token = create_access_token(user.username, user.id, token_expire)
    return {"access_token": token}
