"""Google OAuth foundation — authorization URL and token exchange."""

from urllib.parse import urlencode

import httpx
from google_auth_oauthlib.flow import Flow

from kip_core.config import get_settings


class GoogleOAuthService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def _client_config(self) -> dict:
        return {
            "web": {
                "client_id": self._settings.google_client_id,
                "client_secret": self._settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self._settings.google_redirect_uri],
            }
        }

    def authorization_url(self, *, state: str) -> str:
        flow = Flow.from_client_config(
            self._client_config(),
            scopes=self._settings.google_scopes_list,
            redirect_uri=self._settings.google_redirect_uri,
        )
        url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )
        return url

    async def exchange_code(self, code: str) -> dict:
        flow = Flow.from_client_config(
            self._client_config(),
            scopes=self._settings.google_scopes_list,
            redirect_uri=self._settings.google_redirect_uri,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "id_token": credentials.id_token,
            "scopes": credentials.scopes,
        }

    async def fetch_userinfo(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()
