import asyncio
import uuid

from pytest_httpx import HTTPXMock

from smcb_unlocker.config import ConfigCredentials, ConfigUserCredentials
from smcb_unlocker.job import DiscoverLockedSmcbJob, SmcbVerifyJob
from smcb_unlocker.worker.discover.discover_locked_smcb_worker import DiscoverLockedSmcbWorker


MANDANTEN_MOCK = [
  {
    "internalId": "8ac7c1e9-c7d6-404b-8eff-bc7dede7ee25",
    "mandantId": "DE-M-HQ",
    "managedSmbs": [
      {
        "iccsn": "80276883110000141762",
        "telematikId": None,
        "commonName": None,
        "hsm": False,
        "autoPin": False,
        "activationCode": None,
        "autoPinVerificationEnabled": False
      }
    ],
    "assignedCardTerminalInternalIds": [
      "c7798759-0162-4537-b377-428bcbd43a51",
      "0c01fe0f-91de-4bd4-86a8-e8561e94bf3e"
    ],
    "remotePinCardTerminals": [],
    "validateTelematikId": False
  }
]

CARD_TERMINALS_MOCK = [
  {
    "internalId": "c7798759-0162-4537-b377-428bcbd43a51",
    "cardTerminalId": "c7798759-0162-4537-b377-428bcbd43a51",
    "label": "DE-M-HQ-KT-01",
    "physical": True,
    "ipAddress": "10.0.22.110",
    "port": 4742,
    "hostname": "DE-M-HQ-KT-01",
    "macAddress": "00:1B:B5:05:E4:B1",
    "adminUsername": "admin",
    "adminPassword": None,
    "pairingConnectorSubjectName": "CN=80276883110000166405,O=gematikTEST-ONLY - NOT-VALID,C=DE",
    "expirationAuthCertificate": 1897257599000,
    "authCertificate": "MIICmTCCAj+gAwIBAgIHAa1CsJH+pDAKBggqhkjOPQQDAjCBhDELMAkGA1UEBhMCREUxHzAdBgNVBAoMFmdlbWF0aWsgR21iSCBOT1QtVkFMSUQxMjAwBgNVBAsMKUtvbXBvbmVudGVuLUNBIGRlciBUZWxlbWF0aWtpbmZyYXN0cnVrdHVyMSAwHgYDVQQDDBdHRU0uS09NUC1DQTU3IFRFU1QtT05MWTAeFw0yNTAyMTQwMDAwMDBaFw0zMDAyMTMyMzU5NTlaMFMxCzAJBgNVBAYTAkRFMSUwIwYDVQQKDBxnZW1hdGlrVEVTVC1PTkxZIC0gTk9ULVZBTElEMR0wGwYDVQQDDBQ4MDI3Njg4MzExMDAwMDE2NjQwNTBaMBQGByqGSM49AgEGCSskAwMCCAEBBwNCAAScg1V1hrfysVXR0OCzecQqb0agWtgh2omAs8b71OB02xyFueACJtI6R8CXsn0iJxm43Ijt8ubwnyGF7+jvNidJo4HKMIHHMCAGA1UdIAQZMBcwCgYIKoIUAEwEgSMwCQYHKoIUAEwEUjATBgNVHSUEDDAKBggrBgEFBQcDATAMBgNVHRMBAf8EAjAAMDAGBSskCAMDBCcwJTAjMCEwHzAdMBAMDkthcnRlbnRlcm1pbmFsMAkGByqCFABMBGkwHQYDVR0OBBYEFJeuTjtE3LI8XKDY280zGZShorlZMA4GA1UdDwEB/wQEAwIHgDAfBgNVHSMEGDAWgBRYkjsQ0J674x68n7/+UB0Iv1eQ8DAKBggqhkjOPQQDAgNIADBFAiBQE+I3jRVKJ50DoYzM5QkQgfjWtm9HTrD5/65bJgbJEwIhAJH1Uos3jg0qCjPOx0PJwKdU4Mrp3akjNVT81vnYCfdM",
    "slotCount": 4,
    "slotInfos": [
      {
        "cardhandle": "EGK-62",
        "cardTerminalHostname": "DE-M-HQ-KT-01",
        "cardTerminalId": "c7798759-0162-4537-b377-428bcbd43a51",
        "cardTerminalMacAddress": "00:1B:B5:05:E4:B1",
        "slotNo": 1,
        "type": "EGK",
        "insertTime": 1762938870580,
        "commonName": "Franziska Karla Freifrau HütterTEST-ONLY",
        "iccsn": "80276883110000165315",
        "telematikId": None,
        "hasEccCert": True,
        "hasRsaCert": True,
        "version": {
          "cos": "4.6.0",
          "objectSystem": "4.5.2",
          "ptPers": None,
          "dataStructure": None,
          "logging": "1.0.0",
          "atr": "2.0.0",
          "gdo": "1.0.0",
          "keyInfo": None
        },
        "expirationDate": 1897171199000
      },
      {
        "cardhandle": "SMC-KT-50",
        "cardTerminalHostname": "DE-M-HQ-KT-01",
        "cardTerminalId": "c7798759-0162-4537-b377-428bcbd43a51",
        "cardTerminalMacAddress": "00:1B:B5:05:E4:B1",
        "slotNo": 3,
        "type": "SMC_KT",
        "insertTime": 1762858675372,
        "commonName": "80276883110000166405",
        "iccsn": "80276883110000166405",
        "telematikId": None,
        "hasEccCert": True,
        "hasRsaCert": False,
        "version": {
          "cos": "4.6.0",
          "objectSystem": "4.4.1",
          "ptPers": "4.4.1",
          "dataStructure": None,
          "logging": None,
          "atr": "2.0.0",
          "gdo": "1.0.0",
          "keyInfo": "2.0.0"
        },
        "expirationDate": 1897257599000
      }
    ],
    "productinformation": {
      "informationDate": 1762858676175,
      "manufacturer": "DECHY",
      "sicctVersion": "0120 ",
      "softwareVersion": "0100 ",
      "productTypeVersion": "1.8.0",
      "model": "ST1506",
      "firmwareVersion": "4.0.47",
      "hardwareVersion": "4.0.0",
      "firmwareGroupVersion": "00179",
      "ehealthInterfaceVersion": "1.0.0"
    },
    "validSicctVersion": True,
    "correlation": "AKTIV",
    "renewPairingNeeded": False,
    "connected": True,
    "userRole": "USER",
    "autoUpdate": True,
    "protocolErrorMax": 3,
    "protocolErrorLifetime": {
      "amount": 600,
      "unit": "SECONDS"
    },
    "cardStatusSwallowedCheckEnabled": True
  },
  {
    "internalId": "0c01fe0f-91de-4bd4-86a8-e8561e94bf3e",
    "cardTerminalId": "0c01fe0f-91de-4bd4-86a8-e8561e94bf3e",
    "label": "DE-M-HQ-KT-02",
    "physical": True,
    "ipAddress": "10.0.22.111",
    "port": 4742,
    "hostname": "DE-M-HQ-KT-02",
    "macAddress": "00:1B:B5:05:DB:2D",
    "adminUsername": "admin",
    "adminPassword": None,
    "pairingConnectorSubjectName": "CN=80276883110000166406,O=gematikTEST-ONLY - NOT-VALID,C=DE",
    "expirationAuthCertificate": 1897257599000,
    "authCertificate": "MIICmDCCAj+gAwIBAgIHAb3kVBBJDTAKBggqhkjOPQQDAjCBhDELMAkGA1UEBhMCREUxHzAdBgNVBAoMFmdlbWF0aWsgR21iSCBOT1QtVkFMSUQxMjAwBgNVBAsMKUtvbXBvbmVudGVuLUNBIGRlciBUZWxlbWF0aWtpbmZyYXN0cnVrdHVyMSAwHgYDVQQDDBdHRU0uS09NUC1DQTU3IFRFU1QtT05MWTAeFw0yNTAyMTQwMDAwMDBaFw0zMDAyMTMyMzU5NTlaMFMxCzAJBgNVBAYTAkRFMSUwIwYDVQQKDBxnZW1hdGlrVEVTVC1PTkxZIC0gTk9ULVZBTElEMR0wGwYDVQQDDBQ4MDI3Njg4MzExMDAwMDE2NjQwNjBaMBQGByqGSM49AgEGCSskAwMCCAEBBwNCAARmWJyu23pqNKZx1huHf7F/cw/bMY4EycHMQHD//H0nzaVDhFxNAEE9wCvce3ZL2qUvNeHSM/kdgN+TCThM3SEko4HKMIHHMCAGA1UdIAQZMBcwCgYIKoIUAEwEgSMwCQYHKoIUAEwEUjATBgNVHSUEDDAKBggrBgEFBQcDATAMBgNVHRMBAf8EAjAAMDAGBSskCAMDBCcwJTAjMCEwHzAdMBAMDkthcnRlbnRlcm1pbmFsMAkGByqCFABMBGkwHQYDVR0OBBYEFDgjWIrdDY475HJ9kxXm7RLCy50EMA4GA1UdDwEB/wQEAwIHgDAfBgNVHSMEGDAWgBRYkjsQ0J674x68n7/+UB0Iv1eQ8DAKBggqhkjOPQQDAgNHADBEAiBeKOwQjvWo+dCoB38mMxajKTJX4LXtksZqE0rEnBQq2wIgNAos+m4EeTa183QgN8g/ut8N9XSDohsFMOyGmQ0QvYA=",
    "slotCount": 4,
    "slotInfos": [
      {
        "cardhandle": "EGK-80",
        "cardTerminalHostname": "DE-M-HQ-KT-02",
        "cardTerminalId": "0c01fe0f-91de-4bd4-86a8-e8561e94bf3e",
        "cardTerminalMacAddress": "00:1B:B5:05:DB:2D",
        "slotNo": 1,
        "type": "EGK",
        "insertTime": 1763046957866,
        "commonName": "Dr. Sophie Abigail TóboggenTEST-ONLY",
        "iccsn": "80276883110000165891",
        "telematikId": None,
        "hasEccCert": True,
        "hasRsaCert": True,
        "version": {
          "cos": "4.6.0",
          "objectSystem": "4.5.2",
          "ptPers": None,
          "dataStructure": None,
          "logging": "1.0.0",
          "atr": "2.0.0",
          "gdo": "1.0.0",
          "keyInfo": None
        },
        "expirationDate": 1897257599000
      },
      {
        "cardhandle": "HBA-81",
        "cardTerminalHostname": "DE-M-HQ-KT-02",
        "cardTerminalId": "0c01fe0f-91de-4bd4-86a8-e8561e94bf3e",
        "cardTerminalMacAddress": "00:1B:B5:05:DB:2D",
        "slotNo": 2,
        "type": "HBA",
        "insertTime": 1763046959428,
        "commonName": "Ulrica GåbrielTEST-ONLY",
        "iccsn": "80276883110000164197",
        "telematikId": "1-HBA-Testkarte-883110000164197",
        "hasEccCert": True,
        "hasRsaCert": True,
        "version": {
          "cos": "4.6.0",
          "objectSystem": "4.7.1",
          "ptPers": None,
          "dataStructure": None,
          "logging": None,
          "atr": "2.0.0",
          "gdo": "1.0.0",
          "keyInfo": None
        },
        "expirationDate": 1896652799000
      },
      {
        "cardhandle": "SMC-KT-82",
        "cardTerminalHostname": "DE-M-HQ-KT-02",
        "cardTerminalId": "0c01fe0f-91de-4bd4-86a8-e8561e94bf3e",
        "cardTerminalMacAddress": "00:1B:B5:05:DB:2D",
        "slotNo": 3,
        "type": "SMC_KT",
        "insertTime": 1763046961740,
        "commonName": "80276883110000166406",
        "iccsn": "80276883110000166406",
        "telematikId": None,
        "hasEccCert": True,
        "hasRsaCert": False,
        "version": {
          "cos": "4.6.0",
          "objectSystem": "4.4.1",
          "ptPers": "4.4.1",
          "dataStructure": None,
          "logging": None,
          "atr": "2.0.0",
          "gdo": "1.0.0",
          "keyInfo": "2.0.0"
        },
        "expirationDate": 1897257599000
      },
      {
        "cardhandle": "SMC-B-83",
        "cardTerminalHostname": "DE-M-HQ-KT-02",
        "cardTerminalId": "0c01fe0f-91de-4bd4-86a8-e8561e94bf3e",
        "cardTerminalMacAddress": "00:1B:B5:05:DB:2D",
        "slotNo": 4,
        "type": "SMC_B",
        "insertTime": 1763046962431,
        "commonName": "Praxis Regina Freifrau BäckerTEST-ONLY",
        "iccsn": "80276883110000141762",
        "telematikId": "1-SMC-B-Testkarte-883110000141762",
        "hasEccCert": True,
        "hasRsaCert": True,
        "version": {
          "cos": "4.6.0",
          "objectSystem": "4.8.0",
          "ptPers": None,
          "dataStructure": None,
          "logging": None,
          "atr": "2.0.0",
          "gdo": "1.0.0",
          "keyInfo": None
        },
        "expirationDate": 1820707199000
      }
    ],
    "productinformation": {
      "informationDate": 1762858682153,
      "manufacturer": "DECHY",
      "sicctVersion": "0120 ",
      "softwareVersion": "0100 ",
      "productTypeVersion": "1.8.0",
      "model": "ST1506",
      "firmwareVersion": "4.0.47",
      "hardwareVersion": "4.0.0",
      "firmwareGroupVersion": "00179",
      "ehealthInterfaceVersion": "1.0.0"
    },
    "validSicctVersion": True,
    "correlation": "AKTIV",
    "renewPairingNeeded": False,
    "connected": True,
    "userRole": "USER",
    "autoUpdate": True,
    "protocolErrorMax": 3,
    "protocolErrorLifetime": {
      "amount": 600,
      "unit": "SECONDS"
    },
    "cardStatusSwallowedCheckEnabled": True
  }
]

PIN_STATUS_MOCK = {
  "status": "VERIFIABLE",
  "retries": None
}

async def test_discover_locked_smcb_worker_runs(httpx_mock: HTTPXMock):
    base_url = "https://example.com"
    httpx_mock.add_response(method="POST", url=f"{base_url}/rest/mgmt/ak/konten/login", status_code=204, headers={"Authorization": "Bearer testtoken"})
    httpx_mock.add_response(method="GET", url=f"{base_url}/rest/mgmt/ak/info/mandanten", json=MANDANTEN_MOCK)
    httpx_mock.add_response(method="GET", url=f"{base_url}/rest/mgmt/ak/dienste/kartenterminals", json=CARD_TERMINALS_MOCK)
    httpx_mock.add_response(method="GET", url=f"{base_url}/rest/mgmt/ak/dienste/karten/smb/SMC-B-83/DE-M-HQ/pin", json=PIN_STATUS_MOCK)
    
    discover_queue = asyncio.Queue()
    verify_queue = asyncio.Queue()

    konnektor_creds = ConfigUserCredentials(username="testuser", password="testpass")
    worker = DiscoverLockedSmcbWorker(ConfigCredentials(konnektors={ "test": konnektor_creds }, kt={}, smcb={}))
    worker.connectInput(discover_queue)
    worker.connectOutput(verify_queue)

    async with asyncio.TaskGroup() as tg:
        task = tg.create_task(worker.run())
        
        await discover_queue.put(DiscoverLockedSmcbJob(job_id=str(uuid.uuid4()), konnektor_name="test", konnektor_base_url=base_url))
        async with asyncio.timeout(1):
            verify_job = await verify_queue.get()

        assert isinstance(verify_job, SmcbVerifyJob)
        assert verify_job.konnektor_base_url == base_url
        assert verify_job.konnektor_auth == "Bearer testtoken"
        assert verify_job.kt_id == "0c01fe0f-91de-4bd4-86a8-e8561e94bf3e"
        assert verify_job.kt_base_url == "wss://10.0.22.111"
        assert verify_job.kt_mac == "00:1B:B5:05:DB:2D"
        assert verify_job.smcb_iccsn == "80276883110000141762"
        assert verify_job.smcb_cardhandle == "SMC-B-83"
        assert verify_job.mandant_id == "DE-M-HQ"

        task.cancel()
