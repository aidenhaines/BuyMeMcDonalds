from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_beanie
from app.database.models import Account

from app.utils import load_config, mcclient
from app.utils.mcdonalds import McDonalds

mcclient: McDonalds
config = load_config()


async def handle_account():
    account = await Account.find_one()

    if not account:
        print("No existing account found")
        await handle_missing_account()
    else:
        print("Found existing account")
        await update_existing_account(account)


async def handle_missing_account():
    await mcclient.login()
    account = Account(
        access_token=mcclient.access_token,
        refresh_token=mcclient.refresh_token,
    )
    await account.insert()


async def update_existing_account(account: Account):
    mcclient.access_token = account.access_token
    mcclient.refresh_token = account.refresh_token

    try:
        await mcclient.refresh()
    except Exception as e:
        print("Failed to refresh token", e)
        await mcclient.login()

    account.access_token = mcclient.access_token
    account.refresh_token = mcclient.refresh_token
    await account.save()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_beanie(
        host=config.mongodb.host,
        database=config.mongodb.database,
        user=config.mongodb.username,
        password=config.mongodb.password,
    )

    await handle_account()

    yield
    print("Shutting down app")


api = FastAPI(title="BuyMeMcDonalds", lifespan=lifespan)
