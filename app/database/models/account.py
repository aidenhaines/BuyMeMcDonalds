from beanie import Document


class Account(Document):
    access_token: str
    refresh_token: str
