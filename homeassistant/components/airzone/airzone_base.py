"""Lib for Airzone Webserver."""
import json
import logging

import aiohttp
import requests

_LOGGER = logging.getLogger(__name__)

API_URL = "/api/v1/hvac"


class Airozne:
    """
    Interface to communicate with the Airzone Webserver over http / JSON.

    Timeouts are to be set in the given AIO session
    Attributes:
        session     The AIO session
        url         The url for reaching of the Airzone machine
                    (i.e. http://192.168.0.10:3000)
    """

    def __init__(self, session, host):
        """Initialize the request module."""
        self._aio_session = session
        self.host = host
        self.headers = {"content-type": "application/json"}

    async def _post_request(self, url, data):
        """Request with params."""
        try:
            async with self._aio_session.request(
                "post", self.host + url, data=json.dumps(data), headers=self.headers
            ) as res:
                if res.status == 200:
                    text = await res.text()
                    text = json.loads(text)
                else:
                    _LOGGER.error("Airzone request error " + str(res.status))
        except aiohttp.ServerTimeoutError:
            raise ConnectionError(f"Connection to Airzone device timed out at {url}.")
        except aiohttp.ClientError:
            raise ConnectionError(f"Connection to Airzone device failed at {url}.")
        except json.JSONDecodeError:
            raise ValueError(f"Host returned a non-JSON reply at {url}.")
        return text

    def _put_request(self, url, data):
        """Request with params."""
        try:
            res = requests.put(self.host + url, json=data)
            if res.status_code == 200:
                text = res.json()
                return text
            else:
                _LOGGER.error("Airzone request error " + str(res.status_code))
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            raise SystemExit(e)

    async def get_all_machine_data(self):
        """Get data of all zones."""
        url = API_URL
        data = {"systemid": 1, "zoneid": 0}

        res = await self._post_request(url, data)
        return res["data"]

    async def get_zone_data(self, zone):
        """Get data of one zone."""
        url = API_URL
        data = {"systemid": 1, "zoneid": zone}

        res = await self._post_request(url, data)
        return res["data"]

    def put_zone_data(self, zone, key, value):
        """Get data of one zone."""
        url = API_URL
        if key == "setpoint":
            if not isinstance(value, float):
                return
        elif key == "on":
            if not isinstance(value, int):
                return
        elif key == "mode":
            if not isinstance(value, int):
                return
            else:
                if value not in [1, 2, 3, 4]:
                    return
        else:
            return

        data = {"systemid": 1, "zoneid": zone, key: value}

        res = self._put_request(url, data)
        print(res)
        return res
