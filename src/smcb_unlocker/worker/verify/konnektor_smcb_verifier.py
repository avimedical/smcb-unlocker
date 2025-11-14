import asyncio
import logging

import httpx

from smcb_unlocker.client.konnektor.admin import get_pin_status_for_card, verify_pin_for_card
from smcb_unlocker.client.konnektor.admin.model import PinStatus


log = logging.getLogger(__name__)


class KonnektorSmcbVerifier:
    base_url: str
    auth: str

    konnektor_ready: asyncio.Event | None
    kt_ready: asyncio.Event | None

    def __init__(self, base_url: str, auth: str):
        self.base_url = base_url
        self.auth = auth

    @staticmethod
    def of(base_url: str, auth: str) -> KonnektorSmcbVerifier:
        return KonnektorSmcbVerifier(base_url, auth)

    def connect(self, konnektor_ready: asyncio.Event, kt_ready: asyncio.Event):
        self.konnektor_ready = konnektor_ready
        self.kt_ready = kt_ready

    def ensure_connected(self):
        if not self.konnektor_ready or not self.kt_ready:
            raise RuntimeError("KonnektorSmcbVerifier and KtSmcbVerifier are not connected. Call 'connect' method first.")

    async def run(self, smcb_cardhandle: str, mandant_id: str, card_terminal_id: str) -> PinStatus:
        self.ensure_connected()

        async with httpx.AsyncClient(verify=False) as client:
            pin_status = await get_pin_status_for_card(client, self.base_url, self.auth, smcb_cardhandle, mandant_id)
            if not pin_status.status == "VERIFIABLE":
                raise RuntimeError(f"SMCB card with handle {smcb_cardhandle} not in VERIFIABLE state, current state: {pin_status.status}")

            self.konnektor_ready.set()
            await self.kt_ready.wait()

            pin_verify_status = await verify_pin_for_card(client, self.base_url, self.auth, smcb_cardhandle, mandant_id, card_terminal_id)
            if pin_verify_status.status != "OK":
                raise RuntimeError(f"SMCB PIN verification failed, status: {pin_verify_status.status}")
            
            return pin_verify_status
