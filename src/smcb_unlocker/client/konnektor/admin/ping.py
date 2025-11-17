from httpx import AsyncClient, ConnectError, ConnectTimeout


async def ping(client: AsyncClient, konnektor_base_url: str, auth: str, timeout=3.0) -> bool:
    try:
        response = await client.get(f"{konnektor_base_url}/rest/mgmt/ak/dienste/status/ping", headers={"Authorization": auth}, timeout=timeout)
        response.raise_for_status()
        
        return response.status_code == 200
    # The Konnektor will be down during a reboot so don't raise an error here
    except (ConnectError, ConnectTimeout):
        return False
