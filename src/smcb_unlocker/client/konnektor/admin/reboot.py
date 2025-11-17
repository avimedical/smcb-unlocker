from httpx import AsyncClient


async def reboot(client: AsyncClient, base_url: str, auth: str) -> None:    
    response = await client.post(f"{base_url}/rest/mgmt/nk/system", headers={"Authorization": auth}, json={})
    response.raise_for_status()
