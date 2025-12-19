from datetime import datetime, timedelta, timezone
from typing import Optional

from config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    AUTH_SCHEMES,
    SECRET_KEY,
    VALID_STATIC_TOKENS,
    VALID_USER_CREDENTIALS,
)
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt
from models import AuthResponse, TokenData
from user_store import get_password

# API Key header scheme for token validation
api_key_header = APIKeyHeader(name="token", auto_error=True)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing the data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token as string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify a JWT token and return the token data.

    Args:
        token: JWT token to verify

    Returns:
        TokenData if valid, None otherwise

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return TokenData(username=username)
    except JWTError:
        raise credentials_exception


async def get_current_user(token: str = Depends(api_key_header)) -> TokenData:
    """
    FastAPI dependency to get the current user from a token.

    Args:
        token: JWT token from request header

    Returns:
        TokenData containing user information

    Raises:
        HTTPException: If token is invalid or user not found
    """

    token_data = verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def get_auth_schemes():
    """
    Get the available authentication schemes.

    Returns:
        List of authentication schemes
    """
    return AUTH_SCHEMES


def authenticate_user(token: str) -> AuthResponse:
    """
    Authenticate a user using a static token.

    Args:
        token: Static token provided by the user

    Returns:
        AuthResponse containing success status and JWT token if successful
    """
    # Check if the provided token is in the valid static tokens
    for username, valid_token in VALID_STATIC_TOKENS.items():
        if token == valid_token:
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": username}, expires_delta=access_token_expires
            )
            return AuthResponse(
                success=True, token=access_token, message="Authentication successful"
            )

    return AuthResponse(success=False, token=None, message="Invalid token")


def validate_token_header(token: str = Security(api_key_header)) -> TokenData:
    """
    Validate the token in the request header.

    Args:
        token: Token from request header

    Returns:
        TokenData if valid

    Raises:
        HTTPException: If token is invalid
    """
    try:
        token_data = verify_token(token)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token_data
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def is_static_token(token: str) -> bool:
    """
    Check if a token is a static token.

    Args:
        token: Token to check

    Returns:
        True if token is a static token, False otherwise
    """
    return token in VALID_STATIC_TOKENS.values()


def authenticate_user_password(user: str, password: str) -> AuthResponse:
    """
    Authenticate via username/password using the persistent user store.
    """
    stored_pw = get_password(user)
    if stored_pw is not None and stored_pw == password:
        expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user}, expires_delta=expires)
        return AuthResponse(
            success=True, token=access_token, message="Authentication successful"
        )

    return AuthResponse(
        success=False, token=None, message="Invalid username or password"
    )
