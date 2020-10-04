"""Test the Cloudflare integration."""
from homeassistant.components.couldflare.const import CONF_RECORDS, DOMAIN
from homeassistant.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from homeassistant.const import CONF_API_KEY, CONF_EMAIL, CONF_ZONE
from homeassistant.setup import async_setup_component

from . import (
    ENTRY_CONFIG,
    YAML_CONFIG,
    _patch_async_setup_entry,
    _patch_get_zone_id,
    init_integration,
)

from tests.async_mock import patch
from tests.common import MockConfigEntry


async def test_import_from_yaml(hass) -> None:
    """Test import from YAML."""
    with _patch_get_zone_id(), _patch_async_setup_entry():
        assert await async_setup_component(hass, DOMAIN, {DOMAIN: YAML_CONFIG})
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    assert entries[0].data[CONF_API_KEY] == "mock-api-key"
    assert entries[0].data[CONF_EMAIL] == "email@mock.com"
    assert entries[0].data[CONF_ZONE] == "mock.com"
    assert entries[0].data[CONF_RECORDS] == ["ha", "homrassistant"]


async def test_unload_entry(hass, cfupdate):
    """Test successful unload of entry."""
    entry = await init_integration(hass)

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state == ENTRY_STATE_NOT_LOADED
    assert not hass.data.get(DOMAIN)


async def test_async_setup_raises_entry_not_ready(hass):
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.cloudflare.CloudflareUpdater.get_zone_id",
        side_effect=Exception(),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)

    assert config_entry.state == ENTRY_STATE_SETUP_RETRY
