"""Tests for the Cloudflare integration."""
from homeassistant.components.cloudflare.const import CONF_RECORDS, DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_EMAIL, CONF_ZONE

from tests.async_mock import patch
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
