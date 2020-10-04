"""Test the Cloudflare config flow."""
from pycfdns.exceptions import (
    CloudflareAuthenticationException,
    CloudflareConnectionException,
    CloudflareZoneException,
)

from homeassistant.components.cloudflare.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_SOURCE
from homeassistant.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)
from homeassistant.setup import async_setup_component

from . import (
    ENTRY_CONFIG,
    USER_INPUT,
    _patch_async_setup,
    _patch_async_setup_entry,
    _patch_get_zone_id,
)

from tests.async_mock import patch
from tests.common import MockConfigEntry


async def test_user_form(hass):
    """Test we get the user initiated form."""
    await async_setup_component(hass, "persistent_notification", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with _patch_get_zone_id(), _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "mock.com"
    assert result["data"] == {**USER_INPUT}

    assert result["result"]
    assert result["result"].unique_id == "mock.com"

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_form_cannot(hass):
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    with patch(
        "homeassistant.components.cloudflare.CloudflareUpdater.get_zone_id",
        side_effect=CloudflareConnectionException(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_form_invalid auth(hass):
    """Test we handle invalid auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    with patch(
        "homeassistant.components.cloudflare.CloudflareUpdater.get_zone_id",
        side_effect=CloudflareAuthenticationException(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_form_invalid zone(hass):
    """Test we handle invalid zone error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    with patch(
        "homeassistant.components.cloudflare.CloudflareUpdater.get_zone_id",
        side_effect=CloudflareZoneException(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_zone"}


async def test_user_form_unexpected_exception(hass):
    """Test we handle unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    with patch(
        "homeassistant.components.cloudflare.CloudflareUpdater",
        side_effect=Exception(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "unknown"


async def test_user_form_single_instance_allowed(hass):
    """Test that configuring more than one instance is rejected."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=USER_INPUT,
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"
