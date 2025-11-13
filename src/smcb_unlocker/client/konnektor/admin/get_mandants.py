from httpx import AsyncClient
from pydantic import TypeAdapter

from smcb_unlocker.client.konnektor.admin.model import Mandant


async def get_mandants(client: AsyncClient, konnektor_base_url: str, auth: str) -> list[Mandant]:
    response = await client.get(f"{konnektor_base_url}/rest/mgmt/ak/info/mandanten", headers={"Authorization": auth})
    response.raise_for_status()
    
    ta = TypeAdapter(list[Mandant])
    mandants = ta.validate_json(response.text)
    
    return mandants
