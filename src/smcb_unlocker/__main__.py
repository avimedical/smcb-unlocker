import asyncio
import logging
import ssl

import httpx
from websockets.asyncio.client import connect

from .config import Config
from .client.konnektor import admin as konnektor_admin
from .client.kt import mgmt as kt_mgmt
from .client.kt.smcb import StateMachine
from .client.kt.smcb.states import Authenticated


SUPPORTED_API_VERSIONS = ["3.2"]
WS_MGMT_PROTOCOL = "cobra"
WS_SMCB_PROTOCOL = "cobra-smcb"


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def get_smcb_key(config: Config) -> str:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with connect(config.kt_base_url, subprotocols=[WS_MGMT_PROTOCOL], ssl=ssl_context) as ws:
        api_version = await kt_mgmt.get_api_version(ws)
        if api_version not in SUPPORTED_API_VERSIONS:
            log.warning(f"API version {api_version} not supported, supported versions are: {SUPPORTED_API_VERSIONS}")

        session_id = await kt_mgmt.login(ws, config.kt_mgmt_username, config.kt_mgmt_password)
        log.info(f"Logged in with session ID: {session_id}")
        
        try:
            return await kt_mgmt.smcb_authentication(ws, session_id)
        finally:
            # Avoid "Session store full" errors by logging out
            await kt_mgmt.logout(ws, session_id)
            log.info("Logged out")


async def trigger_smcb_verify(smcb_ws_authenticated: asyncio.Event, konnektor_base_url: str, konnektor_admin_username: str, konnektor_admin_password: str, smcb_iccsn: str):
    async with httpx.AsyncClient(verify=False) as client:
        auth = await konnektor_admin.login(client, konnektor_base_url, konnektor_admin_username, konnektor_admin_password)
        
        cards = await konnektor_admin.get_cards(client, konnektor_base_url, auth)
        smcb_card = next((card for card in cards if card.iccsn == smcb_iccsn), None)
        if not smcb_card:
            raise RuntimeError(f"SMCB card with ICCSN {smcb_iccsn} not found on Konnektor")
        
        mandants = await konnektor_admin.get_mandants_for_card(client, konnektor_base_url, auth, smcb_card.cardhandle)
        if len(mandants) == 0:
            raise RuntimeError(f"No mandants found for SMCB card with ICCSN {smcb_iccsn}")
        mandant = mandants[0]

        pin_status = await konnektor_admin.get_pin_status_for_card(client, konnektor_base_url, auth, smcb_card.cardhandle, mandant.mandant.mandantId)
        # TODO: Make this check active after testing
        if not pin_status.status == "VERIFIABLE" and False:
            raise RuntimeError(f"SMCB card with ICCSN {smcb_iccsn} not in VERIFIABLE state, current state: {pin_status.status}")
        
        await smcb_ws_authenticated.wait()
        log.info("SMCB WebSocket authenticated successfully")

        pin_verify_status = await konnektor_admin.verify_pin_for_card(client, konnektor_base_url, auth, smcb_card.cardhandle, mandant.mandant.mandantId, smcb_card.cardTerminalId)
        if pin_verify_status.status != "OK":
            raise RuntimeError(f"SMCB PIN verification failed, status: {pin_verify_status.status}")


async def remote_smcb_verify(smcb_ws_authenticated: asyncio.Event, kt_base_url: str, smcb_key: str, smcb_pin: str):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async def on_state_change(old_state, new_state):
        if isinstance(new_state, Authenticated):
            smcb_ws_authenticated.set()

    async with connect(kt_base_url, subprotocols=[WS_SMCB_PROTOCOL], ssl=ssl_context) as ws:
        state_machine = StateMachine(ws, smcb_key, smcb_pin, on_state_change=on_state_change)
        await state_machine.run()


async def verify_smcb_pin(config: Config, smcb_key: str):
    async with asyncio.TaskGroup() as tg:
        smcb_ws_authenticated = asyncio.Event()
        trigger_task = tg.create_task(trigger_smcb_verify(smcb_ws_authenticated, config.konnektor_base_url, config.konnektor_admin_username, config.konnektor_admin_password, config.smcb_iccsn))
        verfiy_task = tg.create_task(remote_smcb_verify(smcb_ws_authenticated, config.kt_base_url, smcb_key, config.smcb_pin))
    return True


async def main():
    config = Config()

    smcb_key = await get_smcb_key(config)
    log.info(f"SMCB Key: {smcb_key}")

    result = await verify_smcb_pin(config, smcb_key)

if __name__ == "__main__":
    asyncio.run(main())
