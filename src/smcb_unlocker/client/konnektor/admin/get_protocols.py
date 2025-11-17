from datetime import datetime

from httpx import AsyncClient
from pydantic import TypeAdapter

from smcb_unlocker.client.konnektor.admin.model import ProtocolEntry


async def get_protocols(client: AsyncClient, konnektor_base_url: str, auth: str, from_datetime: datetime, to_datetime: datetime) -> list[ProtocolEntry]:
    from_timestamp = int(from_datetime.timestamp())
    to_timestamp = int(to_datetime.timestamp())
    response = await client.post(
        f"{konnektor_base_url}/rest/mgmt/ak/dienste/protokoll/datei/system/OP/{from_timestamp}/{to_timestamp}",
        headers={"Authorization": auth},
        params={
            "severities": "IWEF",
            "exactMatch": False,
            "ascending": True,
            "limit": 1000,
            "offset": 0,
            "timezone": "GMT+0000"
        },
    )
    # Konnektors return 404 if there are no loglines in the given range
    if response.status_code == 404:
        return []

    response.raise_for_status()
    
    ta = TypeAdapter(list[ProtocolEntry])
    protocols = ta.validate_json(response.text)
    
    return protocols
