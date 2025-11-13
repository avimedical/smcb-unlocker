from httpx import AsyncClient

from smcb_unlocker.client.konnektor.admin.model import PinStatus


async def get_pin_status_for_card(client: AsyncClient, konnektor_base_url: str, auth: str, cardhandle: str, mandant_id: str) -> PinStatus:
    response = await client.get(f"{konnektor_base_url}/rest/mgmt/ak/dienste/karten/smb/{cardhandle}/{mandant_id}/pin", headers={"Authorization": auth})
    response.raise_for_status()
    
    pin_status = PinStatus.model_validate_json(response.text)
    return pin_status
