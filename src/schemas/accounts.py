from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from database import accounts_validators


class BaseEmailPasswordSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    password: str = "SecurePassword@123"

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return value.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        return accounts_validators.validate_password_strength(value)


class UserRegistrationRequestSchema(BaseEmailPasswordSchema):
    pass


class UserRegistrationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class UserActivationRequestSchema(BaseModel):
    email: EmailStr
    token: str


class MessageResponseSchema(BaseModel):
    message: str


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr


class PasswordResetCompleteRequestSchema(BaseEmailPasswordSchema):
    token: str


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserLoginRequestSchema(BaseEmailPasswordSchema):
    pass


class TokenRefreshResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: str


class ResendActivationEmailRequestSchema(BaseModel):
    email: EmailStr


class ChangePasswordRequestSchema(BaseModel):
    old_password: str = Field("SecurePassword@123", min_length=8, description="Current password")
    new_password: str = Field("SecurePassword@123", min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value):
        return accounts_validators.validate_password_strength(value)
