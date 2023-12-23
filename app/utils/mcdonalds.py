import base64
import os
from types import NoneType
from typing import Optional
from uuid import uuid4

from app.utils.config import load_config, get_session
from app.utils.email import fetch_magic_link
from base64 import b64encode


class McDonalds:
    def __init__(
        self, mc_email: str, access_token: str = None, refresh_token: str = None
    ):
        self.mc_email: str = mc_email
        self.access_token: str = (
            access_token  # NOTE: JWT made from verifying the magic link
        )
        self.refresh_token: str = refresh_token  # NOTE: Refresh token for the JWT
        self.client_id = "8cGckR5wPgQnFBc9deVhJ2vT94WhMBRL"
        self.client_secret = "Ym4rVyqpqNpCpmrdPGJatRrBMHhJgr26"
        self.device_id = "8c84f39447878d18"

    async def request(self, method: str, path: str, **kwargs) -> Optional[dict]:
        api = "https://us-prod.api.mcd.com"

        session = await get_session()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "mcd-clientsecret": self.client_secret,
            "mcd-clientid": self.client_id,
            "mcd-sourceapp": "GMA",
            "accept-language": "en-US",
            "mcd-marketid": "US",
            "mcd-uuid": str(uuid4()),
        }
        more_headers = kwargs.pop("headers", {})
        headers.update(more_headers)

        url = f"{api}{path}"
        async with session.request(method, url, headers=headers, **kwargs) as response:
            return await response.json()

    async def get_mcbasic_token(self) -> NoneType:
        """Fetches a guest token for the McDonalds API."""
        path = "/v1/security/auth/token"
        token: str = b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {token}",
        }

        body = "grantType=client_credentials"

        data = await self.request("POST", path, headers=headers, data=body)
        token = data.get("response", {}).get("token")

        if token:
            self.access_token = token

    # https://us-prod.api.mcd.com/exp/v1/customer/identity/email
    async def get_identity_email(self) -> NoneType:
        """Send an email to the account we are trying to login to."""
        path = "/exp/v1/customer/identity/email"

        req_data = {
            "customerIdentifier": self.mc_email,
            "deviceId": self.device_id,
            "registrationType": "traditional",
        }

        data = await self.request("POST", path, json=req_data)

        if data.get("status", {}).get("code") == 20000:
            return
        else:
            raise Exception("Failed to send email", data)

    # https://us-prod.api.mcd.com/exp/v1/customer/activateandsignin
    async def activate_and_signin(self, magic_token: str) -> NoneType:
        """Activates and signs into the McDonalds API."""
        path = "/exp/v1/customer/activateandsignin"

        data = {
            "activationLink": magic_token,
            "clientInfo": {
                "device": {
                    "deviceUniqueId": self.device_id,
                    "os": "android",
                    "osVersion": "12",
                }
            },
        }

        data = await self.request("PUT", path, json=data)

        if data.get("status", {}).get("code") == 20000:
            self.refresh_token = data.get("response", {}).get("refreshToken")
            self.access_token = data.get("response", {}).get("accessToken")
            return
        else:
            raise Exception("Failed to activate and sign in", data)

    async def refresh(self) -> NoneType:
        """Refreshes the access token."""
        path = "/exp/v1/customer/login/refresh"

        data = {
            "refreshToken": self.refresh_token,
        }

        data = await self.request("POST", path, json=data)

        if data.get("status", {}).get("code") == 20000:
            self.access_token = data.get("response", {}).get("accessToken")
            self.refresh_token = data.get("response", {}).get("refreshToken")
            return
        else:
            raise Exception("Failed to refresh token", data)

    async def login(self):
        """Must be called before any other methods."""
        if all([self.access_token, self.refresh_token]):
            await self.refresh()
            return

        await self.get_mcbasic_token()
        await self.get_identity_email()

        magic_link = fetch_magic_link()

        if magic_link is None:
            raise Exception(
                "Failed to get magic link from email. Make sure you have the correct email and Inbox."
            )

        await self.activate_and_signin(magic_link)


global mcclient

config = load_config()

mcclient = McDonalds(config.mcd.email)
