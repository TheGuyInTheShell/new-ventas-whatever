from datetime import datetime
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, EmailStr


class Roles(Enum):
    SUPERADMIN = "SUPERADMIN"


class CreateUser(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str


# PYDANTIC
class User(BaseModel):
    uid: Union[int, str]
    id: Union[int, str]
    username: str
    full_name: str | None = None
    email: EmailStr
    role: int | str
    otp_enabled: bool = False

    def email_is_empty(self):
        return self.email is None


class UserTokenData(BaseModel):
    uid: Union[int, str]
    id: Union[int, str]
    username: str
    role: int | str
    full_name: str | None = None
    email: EmailStr
    otp_enabled: bool = False


class INUser(User):
    password: str


class UserSignIn(BaseModel):
    username: str
    password: str


class OTPEnableRequest(BaseModel):
    otp_code: str
    secret: str
