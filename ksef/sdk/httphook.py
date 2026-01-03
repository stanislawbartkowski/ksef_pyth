import logging
from time import sleep
from typing import Optional

import requests


def _getlogger():
    logger = logging.getLogger(__name__)
    return logger


_logger = _getlogger()


def _l(info: str):
    _logger.info(info)


class HOOKHTTP:

    _NOBEARER = 0
    _BEARERTOKEN = 1
    _BEARERACCESS = 2

    _METHODPOST = 0
    _METHODDEL = 1
    _METHODGET = 2

    _RETRY_AFTER = 'Retry-After'

    def __init__(self, base_url: str):
        self._base_url = base_url
        self._access_token: str = ''
        self._authenticationtoken: str = ''

    def set_tokes(self, access_token: str, authentication_token: str):
        self._access_token = access_token
        self._authenticationtoken = authentication_token

    def _construct_url(self, endpoint: str) -> str:
        return f'{self._base_url}/v2/{endpoint}'

    def hook_response(self,
                      endpoint: str,
                      method: int = _METHODPOST,
                      body: Optional[dict] = None,
                      bearer: int = _BEARERACCESS,
                      xml_data: Optional[bytes] = None,

                      requestmethod: Optional[str] = None,
                      data: Optional[bytes] = None,
                      requestheaders: Optional[dict] = None) -> requests.Response:

        if bearer != self._NOBEARER:
            headers = {
                'Authorization': f'Bearer {self._access_token if bearer == self._BEARERACCESS else self._authenticationtoken}'
            }
        else:
            headers = {}

        url = self._construct_url(
            endpoint=endpoint) if requestmethod is None else endpoint
        _l(url)
        no_request = 0
        while True:
            if requestmethod is not None:
                response = requests.request(
                    url=url, data=data, method=requestmethod, headers=requestheaders)
            else:
                if method == self._METHODDEL:
                    response = requests.delete(url, headers=headers)
                elif method == self._METHODPOST:
                    if xml_data is None:
                        response = requests.post(
                            url, json=body or {}, headers=headers)
                    else:
                        headers = headers | {}
                        headers |= {"Content-Type": "application/xml"}
                        response = requests.post(
                            url, data=xml_data, headers=headers)
                else:
                    response = requests.get(url, headers=headers)

            if response.status_code == 400:
                exce = response.json()['exception']['exceptionDetailList'][0]
                details = exce['details']
                errmsg = ' '.join(details)
                _logger.error(errmsg)
                raise ValueError(errmsg)

            if response.status_code == 429 and self._RETRY_AFTER in response.json():
                no_of_sec = response.json()[self._RETRY_AFTER]
                no_request += 1
                mess = f'Code: {response.status_code}, próba {no_request},  Czekam {no_of_sec} przed ponowną próbą'
                _l(mess)
                sleep(no_of_sec)
            else:
                break

        response.raise_for_status()
        return response

    def hook(self, endpoint: str, method: int = _METHODPOST, body: dict | None = None, bearer: int = _BEARERACCESS) -> dict:

        response = self.hook_response(
            endpoint=endpoint, method=method, body=body, bearer=bearer)
        return response.json() if response.status_code != 204 else {}
