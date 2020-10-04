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
    YAML_CONFIG,
    _get_mock_cfupdate,
    _patch_async_setup,
    _patch_async_setup_entry,
)

from tests.async_mock import patch
from tests.common import MockConfigEntry


async def test_form_import(hass, cfupdate_flow):
    """Test we get the form with import source."""
    await async_setup_component(hass, "persistent_notification", {})

    mock_cfupdate = _get_mock_cfupdate()

    with _patch_async_setup() as mock_setup, _patch_async_entry_setup() as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_IMPORT},
            data=YAML_CONFIG,
        )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == YAML_CONFIG[CONF_ZONE]

    assert result["data"]
    assert result["data"][CONF_EMAIL] == YAML_CONFIG[CONF_EMAIL]
    assert result["data"][CONF_API_KEY] == YAML_CONFIG[CONF_API_KEY]
    assert result["data"][CONF_ZONE] == YAML_CONFIG[CONF_ZONE]
    assert result["data"][CONF_RECORDS] == ["ha.mock.com", "homeassistant.mock.com"]

    assert result["result"]
    assert result["result"].unique_id == YAML_CONFIG[CONF_ZONE]

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_form(hass, cfupdate_flow):
    """Test we get the user initiated form."""
    await async_setup_component(hass, "persistent_notification", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    mock_cfupdate = _get_mock_cfupdate()

    with _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
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


async def test_user_form_cannot_connect(hass, cfupdate_flow):
    """Test we handle cannot connect error."""
    instance = cfupdate_flow.return_value

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    instance.get_zones.side_effect = CloudflareConnectionException()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_form_invalid_auth(hass, cfupdate_flow):
    """Test we handle invalid auth error."""
    instance = cfupdate_flow.return_value

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    instance.get_zones.side_effect = CloudflareAuthenticationException()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_form_invalid_zone(hass, cfupdate_flow):
    """Test we handle invalid zone error."""
    instance = cfupdate_flow.return_value
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    instance.get_zones.side_effect = CloudflareZoneException()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_zone"}


async def test_user_form_unexpected_exception(hass, cfupdate_flow):
    """Test we handle unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    with patch(
        "homeassistant.components.cloudflare.config_flow.CloudflareUpdater.get_zone_id",
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
