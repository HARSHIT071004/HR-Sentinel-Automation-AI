import sys
sys.path.insert(0, '.')
import asyncio
from app.database import async_session_factory
from app.services.auth_service import AuthService

async def test():
    async with async_session_factory() as db:
        try:
            svc = AuthService(db)
            result = await svc.login('hr@aegis.com', 'hr123')
            print('LOGIN OK')
            print('Keys:', list(result.keys()))
            print('User:', result.get('user'))
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(test())
