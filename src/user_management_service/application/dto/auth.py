from pydantic import BaseModel, EmailStr


class LoginDTO(BaseModel):
    login: str  # username, email or phone_number
    password: str


class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshTokenDTO(BaseModel):
    refresh_token: str


class ResetPasswordRequestDTO(BaseModel):
    email: EmailStr
