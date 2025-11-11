import asyncio
import logging

import httpx

from . import kt_smcb_verifier
from ...client.konnektor.admin import get_cards, get_mandants_for_card, get_pin_status_for_card, login, verify_pin_for_card
from ...client.konnektor.admin.model import PinStatus


log = logging.getLogger(__name__)


class KonnektorSmcbVerifier:
    base_url: str
    admin_username: str
    admin_password: str

    konnektor_ready: asyncio.Event | None
    kt_ready: asyncio.Event | None

    def __init__(self, base_url: str, admin_username: str, admin_password: str):
        self.base_url = base_url
        self.admin_username = admin_username
        self.admin_password = admin_password

    def connect(self, other: 'kt_smcb_verifier.KtSmcbVerifier'):
        self.konnektor_ready = asyncio.Event()
        other.konnektor_ready = self.konnektor_ready
        self.kt_ready = asyncio.Event()
        other.kt_ready = self.kt_ready

    def ensure_connected(self):
        if not self.konnektor_ready or not self.kt_ready:
            raise RuntimeError("KonnektorSmcbVerifier and KtSmcbVerifier are not connected. Call 'connect' method first.")

    async def run(self, smcb_iccsn: str) -> PinStatus:
        self.ensure_connected()

        async with httpx.AsyncClient(verify=False) as client:
            auth = await login(client, self.base_url, self.admin_username, self.admin_password)
            
            cards = await get_cards(client, self.base_url, auth)
            smcb_card = next((card for card in cards if card.iccsn == smcb_iccsn), None)
            if not smcb_card:
                raise RuntimeError(f"SMCB card with ICCSN {smcb_iccsn} not found on Konnektor")
            
            mandants = await get_mandants_for_card(client, self.base_url, auth, smcb_card.cardhandle)
            if len(mandants) == 0:
                raise RuntimeError(f"No mandants found for SMCB card with ICCSN {smcb_iccsn}")
            mandant = mandants[0]

            pin_status = await get_pin_status_for_card(client, self.base_url, auth, smcb_card.cardhandle, mandant.mandant.mandantId)
            # TODO: Make this check active after testing
            if not pin_status.status == "VERIFIABLE" and False:
                raise RuntimeError(f"SMCB card with ICCSN {smcb_iccsn} not in VERIFIABLE state, current state: {pin_status.status}")
            
            self.konnektor_ready.set()
            await self.kt_ready.wait()
            
            log.info("SMCB WebSocket authenticated successfully")

            pin_verify_status = await verify_pin_for_card(client, self.base_url, auth, smcb_card.cardhandle, mandant.mandant.mandantId, smcb_card.cardTerminalId)
            if pin_verify_status.status != "OK":
                raise RuntimeError(f"SMCB PIN verification failed, status: {pin_verify_status.status}")
            
            return pin_verify_status
