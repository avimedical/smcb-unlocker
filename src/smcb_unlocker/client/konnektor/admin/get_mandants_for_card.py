from httpx import AsyncClient
from pydantic import TypeAdapter

from .model import Mandant


async def get_mandants_for_card(client: AsyncClient, konnektor_base_url: str, auth: str, cardhandle: str) -> list[Mandant]:
    response = await client.get(f"{konnektor_base_url}/rest/mgmt/ak/dienste/karten/{cardhandle}/mandanten", headers={"Authorization": auth})
    response.raise_for_status()
    
    ta = TypeAdapter(list[Mandant])
    mandants = ta.validate_json(response.text)
    
    return mandants
