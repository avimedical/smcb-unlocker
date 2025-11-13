from httpx import AsyncClient
from pydantic import TypeAdapter


from .model import CardTerminal


async def get_card_terminals(client: AsyncClient, konnektor_base_url: str, auth: str) -> list[CardTerminal]:
    response = await client.get(f"{konnektor_base_url}/rest/mgmt/ak/dienste/kartenterminals", headers={"Authorization": auth})
    response.raise_for_status()
    
    ta = TypeAdapter(list[CardTerminal])
    card_terminals = ta.validate_json(response.text)
    
    return card_terminals
