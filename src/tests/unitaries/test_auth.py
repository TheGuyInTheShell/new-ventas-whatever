import asyncio
from src.modules.auth.services import AuthService


async def main():
    auth = AuthService()
    try:
        res = await auth.authenticate_user("admin", "admin")
        print(f"RESULT: {res}")
        print(f"TYPE: {type(res)}")
        if isinstance(res, tuple):
            for i, x in enumerate(res):
                print(f"  [{i}]: {x} (type: {type(x)})")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
