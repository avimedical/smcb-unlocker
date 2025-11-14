import asyncio

from pytest_httpx import HTTPXMock

from smcb_unlocker.worker.verify.konnektor_smcb_verifier import KonnektorSmcbVerifier


PIN_STATUS_MOCK = {
  "status": "VERIFIABLE",
  "retries": None
}

PIN_VERIFY_MOCK = {
  "status": "OK",
  "retries": None
}


async def test_konnektor_smcb_verifier_runs(httpx_mock: HTTPXMock):
    base_url = "https://example.com"
    httpx_mock.add_response(method="GET", url=f"{base_url}/rest/mgmt/ak/dienste/karten/smb/SMC-B-1/MANDANT-1/pin", json=PIN_STATUS_MOCK)
    httpx_mock.add_response(method="POST", url=f"{base_url}/rest/mgmt/ak/dienste/karten/smb/SMC-B-1/MANDANT-1/KT-1/pin", json=PIN_VERIFY_MOCK)

    verifier = KonnektorSmcbVerifier(base_url=base_url, auth="Bearer testtoken")
    konnektor_ready = asyncio.Event()
    kt_ready = asyncio.Event()
    verifier.connect(konnektor_ready, kt_ready)

    async with asyncio.TaskGroup() as tg:
        task = tg.create_task(verifier.run("SMC-B-1", "MANDANT-1", "KT-1"))

        await konnektor_ready.wait()
        
        # Ensure that the verifier is waiting for the KT verifier to be ready
        status_req = httpx_mock.get_request(method="GET", url=f"{base_url}/rest/mgmt/ak/dienste/karten/smb/SMC-B-1/MANDANT-1/pin")
        verify_req1 = httpx_mock.get_request(method="POST", url=f"{base_url}/rest/mgmt/ak/dienste/karten/smb/SMC-B-1/MANDANT-1/KT-1/pin")
        assert status_req is not None
        assert verify_req1 is None

        kt_ready.set()
        result = await task
        
        # Ensure that the verify request was made after KT ready
        verify_req2 = httpx_mock.get_request(method="POST", url=f"{base_url}/rest/mgmt/ak/dienste/karten/smb/SMC-B-1/MANDANT-1/KT-1/pin")
        assert verify_req2 is not None
        assert result.status == "OK"
        assert result.retries is None
