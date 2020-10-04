"""Define fixtures available for all tests."""
from pycfdns import CFRecord
from pytest import fixture

from tests.async_mock import AsyncMock, patch


@fixture
def cfupdate(hass):
    """Mock the CloudflareUpdater for easier testing."""
    with patch("homeassistant.components.cloudflare.CloudflareUpdater") as mock_api:
        instance = mock_api.return_value

        cf_records = [
            CFRecord(
                {
                    "id": "zone-record-id",
                    "type": "A",
                    "name": "ha.mock.com",
                    "proxied": True,
                    "content": "127.0.0.1",
                }
            ),
            CFRecord(
                {
                    "id": "zone-record-id-2",
                    "type": "A",
                    "name": "homeassistant.mock.com",
                    "proxied": True,
                    "content": "127.0.0.1",
                }
            ),
        ]

        instance.get_record_info = AsyncMock(return_value=cf_records)
        instance.get_zone_id = AsyncMock(return_value="mock-zone-id")
        instance.update_records = AsyncMock(return_value=None)

        yield mock_api
