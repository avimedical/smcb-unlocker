from httpx import AsyncClient
from pydantic import TypeAdapter


from .model import Card


async def get_cards(client: AsyncClient, konnektor_base_url: str, auth: str) -> list[Card]:
    response = await client.get(f"{konnektor_base_url}/rest/mgmt/ak/dienste/karten", headers={"Authorization": auth})
    response.raise_for_status()
    
    ta = TypeAdapter(list[Card])
    cards = ta.validate_json(response.text)
    
    return cards
