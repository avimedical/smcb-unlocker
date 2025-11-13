from httpx import AsyncClient

from smcb_unlocker.client.konnektor.admin.model import LoginRequest


async def login(client: AsyncClient, base_url: str, username: str, password: str) -> str:
    request = LoginRequest(username=username, password=password)
    
    response = await client.post(f"{base_url}/rest/mgmt/ak/konten/login", json=request.model_dump())
    auth = response.headers.get("Authorization")
    if not auth:
        raise Exception("Authentication failed: No Authorization header in response")

    return auth
