import secrets
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from kip_api.dependencies import CurrentUserId, DbSession
from kip_core.auth.google_oauth import GoogleOAuthService
from kip_core.auth.jwt import create_access_token
from kip_core.repositories.user import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])

_oauth_states: dict[str, bool] = {}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.get("/google")
async def google_auth_start() -> dict[str, str]:
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = True
    oauth = GoogleOAuthService()
    if not oauth._settings.google_client_id:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    return {"authorization_url": oauth.authorization_url(state=state)}


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(
    code: str,
    state: str,
    db: DbSession,
) -> TokenResponse:
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    del _oauth_states[state]

    oauth = GoogleOAuthService()
    tokens = await oauth.exchange_code(code)
    userinfo = await oauth.fetch_userinfo(tokens["access_token"])
    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not returned from Google")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)
    if user is None:
        user = await user_repo.create(email=email, role="viewer")
    await db.commit()

    token = create_access_token(str(user.id), extra={"email": email})
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(db: DbSession, user_id: CurrentUserId) -> dict[str, str]:
    user = await UserRepository(db).get_by_id(UUID(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user.id), "email": user.email, "role": user.role}
