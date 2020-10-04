"""Tests for the Cloudflare integration."""
from pycfdns import CFRecord

from homeassistant.components.cloudflare.const import CONF_RECORDS, DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_EMAIL, CONF_ZONE

from tests.async_mock import AsyncMock, patch
from tests.common import MockConfigEntry

ENTRY_CONFIG = {
    CONF_EMAIL: "email@mock.com",
    CONF_API_KEY: "mock-api-key",
    CONF_ZONE: "mock.com",
}

ENTRY_OPTIONS = {}

USER_INPUT = {
    CONF_EMAIL: "email@mock.com",
    CONF_API_KEY: "mock-api-key",
    CONF_ZONE: "mock.com",
}

YAML_CONFIG = {
    CONF_EMAIL: "email@mock.com",
    CONF_API_KEY: "mock-api-key",
    CONF_ZONE: "mock.com",
    CONF_RECORDS: ["ha", "homeassistant"],
}

MOCK_ZONE = "mock.com"
MOCK_ZONE_ID = "mock-zone-id"


async def init_integration(
    hass,
    *,
    data: dict = ENTRY_CONFIG,
    options: dict = ENTRY_OPTIONS,
) -> MockConfigEntry:
    """Set up the Cloudflare integration in Home Assistant."""
    entry = MockConfigEntry(domain=DOMAIN, data=data, options=options)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    return entry


def _get_mock_cfupdate():
    client = AsyncMock()

    zone_records = ["ha.mock.com", "homeassistant.mock.com"]
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

    client.get_zones = AsyncMock(return_value=[str(MOCK_ZONE)])
    client.get_zone_records = AsyncMock(return_value=zone_records)
    client.get_record_info = AsyncMock(return_value=cf_records)
    client.get_zone_id = AsyncMock(return_value=str(MOCK_ZONE_ID))
    client.update_records = AsyncMock(return_value=None)

    return client


def _patch_async_setup(return_value=True):
    return patch(
        "homeassistant.components.cloudflare.async_setup",
        return_value=return_value,
    )


def _patch_async_setup_entry(return_value=True):
    return patch(
        "homeassistant.components.cloudflare.async_setup_entry",
        return_value=return_value,
    )


def _patch_get_zone_id(return_value=MOCK_ZONE_ID):
    return patch(
        "homeassistant.components.cloudflare.CloudflareUpdater.get_zone_id",
        return_value=return_value,
    )
