import logging
from time import sleep
import os
from typing import Callable, Optional
import hashlib
from collections import namedtuple
from collections.abc import Iterator
import tempfile

import requests

from .encrypt import (
    encrypt_token, get_key_and_iv,
    encrypt_symmetric_key, to_base64,
    encrypt_invoice, calculate_hash, encrypt_padding
)


def _getlogger():
    logger = logging.getLogger(__name__)
    return logger


_logger = _getlogger()


def _l(info: str):
    _logger.info(info)


class KSEFSDK:

    INVOICES = namedtuple(typename='invoices_ksef', field_names=[
                          'ok', 'ordinalNumer', 'msg', 'invoiceNumber', 'ksefNumber', 'referenceNumber'])

    DEVKSEF = 0
    PREKSEF = 1
    PRODKSEF = 2

    _METHODPOST = 0
    _METHODDEL = 1
    _METHODGET = 2

    _NOBEARER = 0
    _BEARERTOKEN = 1
    _BEARERACCESS = 2

    _env_dict = {
        DEVKSEF: 'https://api-test.ksef.mf.gov.pl',
        PREKSEF: 'https://api-demo.ksef.mf.gov.pl',
        PRODKSEF: 'https://api.ksef.mf.gov.pl'
    }

    @classmethod
    def initsdk(cls, env: int, nip: str, token: str):
        if env not in KSEFSDK._env_dict:
            raise ValueError(
                'Niepoprawne środowisko, parametr env musi mieć wartość DEVKSEF, PREKSEF lub PRODKSEF')
        return cls(url=KSEFSDK._env_dict[env], nip=nip, token=token)

    _SESSIONRATELIMITER = 5
    _INVOICERATELIMITER = 10
    _RATEDELAYTIME = 2

    _RETRY_AFTER = 'Retry-After'

    def __init__(self, url: str, nip: str, token: str):
        self._base_url = url
        self._nip = nip
        self._token = token
        self._challenge, self._timestamp = self._get_challengeandtimestamp()
        self._kseftoken_certificate, self._symmetrickey_certificate = self._get_public_certificate()
        self._encrypted_token = encrypt_token(
            kseftoken=self._token,
            timestamp=self._timestamp,
            public_certificate=self._kseftoken_certificate
        )
        self._referencenumber, self._authenticationtoken = self._auth_ksef_token()
        self._session_status()
        self._access_token, self._refresh_token = self._redeem_token()
        self._symmetric_key, self._iv = get_key_and_iv()
        self._sessionreferencenumber = ''
        self._sessioninvoicereferencenumber = ''
        self._invoicereferencenumber = ''

    def _construct_url(self, endpoint: str) -> str:
        return f'{self._base_url}/v2/{endpoint}'

    def _hook_response(self,
                       endpoint: str,
                       method: int = _METHODPOST,
                       body: Optional[dict] = None,
                       bearer: int = _BEARERACCESS,

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
                    response = requests.post(
                        url, json=body or {}, headers=headers)
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

    def _hook(self, endpoint: str, method: int = _METHODPOST, body: dict | None = None, bearer: int = _BEARERACCESS) -> dict:

        response = self._hook_response(
            endpoint=endpoint, method=method, body=body, bearer=bearer)
        return response.json() if response.status_code != 204 else {}

    def _get_challengeandtimestamp(self) -> tuple[str, str]:
        response = self._hook('auth/challenge', bearer=self._NOBEARER)
        return response['challenge'], response['timestamp']

    def _get_public_certificate(self) -> tuple[str, str]:
        response = self._hook(
            'security/public-key-certificates', method=self._METHODGET, bearer=self._NOBEARER)
        kseftoken_certificate = next(
            e['certificate'] for e in response if 'KsefTokenEncryption' in e['usage'])
        symmetrickey_certificate = next(
            e['certificate'] for e in response if 'SymmetricKeyEncryption' in e['usage'])
        return kseftoken_certificate, symmetrickey_certificate

    def _auth_ksef_token(self) -> tuple[str, str]:
        context = {
            'type:': 'Nip',
            'value': self._nip
        }
        body = {
            'contextIdentifier': context,
            'challenge': self._challenge,
            'encryptedToken': self._encrypted_token
        }
        response = self._hook(
            'auth/ksef-token', body=body, bearer=self._NOBEARER)
        referenceNumber = response['referenceNumber']
        token = response['authenticationToken']['token']
        return referenceNumber, token

    def _session_status(self) -> None:
        url = f'auth/{self._referencenumber}'
        sleep_time = self._RATEDELAYTIME
        for _ in range(self._SESSIONRATELIMITER):
            response = self._hook(
                url, method=self._METHODGET, bearer=self._BEARERTOKEN)
            status = response['status']['code']
            description = response['status']['description']
            if status == 100:
                sleep(sleep_time)
                # increase by 2 seconds
                sleep_time += 2
            elif status == 200:
                return
            else:
                raise ValueError(
                    f'Session activation failed: {status} - {description}')

        raise TimeoutError('Session activation timed out.')

    def _redeem_token(self) -> tuple[str, str]:
        response = self._hook(endpoint='auth/token/redeem',
                              bearer=self._BEARERTOKEN)
        access_token = response['accessToken']['token']
        refresh_token = response['refreshToken']['token']
        return access_token, refresh_token

    def session_terminate(self) -> None:
        url = f'auth/sessions/{self._referencenumber}'
        self._hook(url, method=self._METHODDEL)

    def close_session(self) -> None:
        url = f'sessions/online/{self._sessionreferencenumber}/close'
        self._hook(url)

    def _prepare_session_data(self) -> dict:
        encrypted_symmetric_key = encrypt_symmetric_key(
            symmetricy_key=self._symmetric_key,
            public_certificate=self._symmetrickey_certificate
        )
        request_data = {
            'formCode': {
                'systemCode': 'FA (3)',
                'schemaVersion': '1-0E',
                'value': 'FA'
            },
            'encryption': {
                'encryptedSymmetricKey': to_base64(encrypted_symmetric_key),
                'initializationVector': to_base64(self._iv)
            },
        }
        return request_data

    def start_session(self) -> None:
        request_data = self._prepare_session_data()
        response = self._hook(endpoint='sessions/online', body=request_data)
        self._sessionreferencenumber = response['referenceNumber']

    @staticmethod
    def _daj_description(status: dict) -> str:
        description = status['description']
        details = status.get('details')
        if isinstance(details, list):
            description += (' ' + ' '.join(details))
        return description

    def _invoice_status(self, end_point: Optional[str] = None) -> tuple[bool, str, str]:
        # end_point not None - batch processing
        is_interactive = end_point is None
        end_point = end_point or f'sessions/{self._sessionreferencenumber}/invoices/{self._sessioninvoicereferencenumber}'
        sleep_time = self._RATEDELAYTIME
        for no in range(self._INVOICERATELIMITER):
            response = self._hook(endpoint=end_point, method=self._METHODGET)
            code = response['status']['code']
            # stworz komunikat
            description = self._daj_description(response['status'])

            # czy w trakcie przetwarzania
            if code == 100 or code == 150:
                _l(description)
                _l(f'Próba {no+1}, max {self._INVOICERATELIMITER}, czekam {sleep_time} sekund')
                sleep(sleep_time)
                sleep_time += 2
                # spróbuj jeszcze raz
                continue
            # albo jest poprawnie albo błąd
            if code == 200:
                self._invoicereferencenumber = response['referenceNumber'] if is_interactive else ''
                return True, description, response['ksefNumber'] if is_interactive else ''
            return False, description, ''

        return False, 'Przekroczona liczba prób przetwarzania', ''

    def send_invoice(self, invoice: str) -> tuple[bool, str, str]:
        invoice_len, encrypted_invoice = encrypt_invoice(
            symmetric_key=self._symmetric_key, iv=self._iv, invoice=invoice)
        invoice_hash = calculate_hash(invoice)
        encrypted_invoice_hash = calculate_hash(encrypted_invoice)
        request_data = {
            'invoiceHash': invoice_hash,
            'invoiceSize': invoice_len,
            'encryptedInvoiceHash': encrypted_invoice_hash,
            'encryptedInvoiceSize': len(encrypted_invoice),
            'encryptedInvoiceContent': to_base64(encrypted_invoice),
            'offlineMode': False,
        }
        end_point = f'sessions/online/{self._sessionreferencenumber}/invoices'
        response = self._hook(endpoint=end_point, body=request_data)
        self._sessioninvoicereferencenumber = response['referenceNumber']
        return self._invoice_status()

    def pobierz_upo(self, invoicereferencenumber: Optional[str] = None) -> str:
        invoicereferencenumber = invoicereferencenumber or self._invoicereferencenumber
        end_point = f'sessions/{self._sessionreferencenumber}/invoices/{invoicereferencenumber}/upo'
        response = self._hook_response(
            endpoint=end_point, method=self._METHODGET)
        return response.text

    def get_invoice(self, ksef_number: str) -> str:
        end_point = f'invoices/ksef/{ksef_number}'
        response = self._hook_response(
            endpoint=end_point, method=self._METHODGET)
        return response.text

    def get_invoices_zakupowe_metadata(self, date_from: str, date_to: str) -> list[dict]:
        end_point = 'invoices/query/metadata?pageSize=250'
        query = {
            'subjectType': 'Subject2',
            'dateRange': {
                'dateType': 'Issue',
                'from': date_from,
                'to': date_to
            }
        }
        response = self._hook(endpoint=end_point, body=query)
        hasMore = response['hasMore']
        if hasMore:
            raise ValueError(
                'Zbyt duża liczba faktur do pobrania (max 250), zawęź zakres dat')
        return response['invoices']

    def send_batch_session_bytes(self, payload: Iterator[bytes], wez_upo: Optional[Callable] = None) -> tuple[bool, str, list[INVOICES]]:

        request_data = self._prepare_session_data()
        fileSize = 0
        crc = hashlib.sha256()
        fileParts = []
        # przechowuje nazwę pliku tymczasowego dla poszczególnych części
        e_data: dict[int, str] = {}
        # pierwsza faza, przegląda payload, koduje i zapamiętuje cześci w plikach tymczasowych
        for partno, b in enumerate(payload):
            fileSize += len(b)
            crc.update(b)

            encrypted_data = encrypt_padding(
                symmetric_key=self._symmetric_key, iv=self._iv, b=b)
            # zapamiętaj zakodowane dane w pliku tymczasowym
            with tempfile.NamedTemporaryFile("wb", delete=False) as t:
                t.write(encrypted_data)
                e_data[partno+1] = t.name
            fileParts.append(
                {
                    'ordinalNumber': partno+1,
                    'fileSize': len(encrypted_data),
                    'fileHash': to_base64(hashlib.sha256(encrypted_data).digest())
                }
            )
        request_data.update({
            'batchFile': {
                'fileSize': fileSize,
                'fileHash': to_base64(crc.digest()),
                'fileParts': fileParts
            }
        })
        end_point = 'sessions/batch'
        response = self._hook(endpoint=end_point, body=request_data)
        self._sessionreferencenumber = response['referenceNumber']
        partUpload = response['partUploadRequests']
        # druga faza, wysyłka kolejnych części
        for p in partUpload:
            method = p['method']
            number = p['ordinalNumber']
            tname = e_data[number]
            # odczytaj zakodowane dane zapamiętane w pliku tymczasowym
            with open(tname, "rb") as t:
                encrypted_data = t.read()
            # usun tymczasowy plik, nie jest potrzebny
            os.unlink(tname)
            url = p['url']
            headers = p['headers']
            msg = f'Wysyłka części numer {number}'
            _l(msg)
            self._hook_response(
                endpoint=url, data=encrypted_data, requestmethod=method, requestheaders=headers)
        # zamknięcie
        end_point = f'sessions/batch/{self._sessionreferencenumber}/close'
        response = self._hook(endpoint=end_point)
        # teraz czekanie na zakończenie przetwarzania
        end_point = f'sessions/{self._sessionreferencenumber}'
        ok_session, msg, _ = self._invoice_status(end_point=end_point)

        # sprawdz faktury i przygotuj wynik
        end_point = f'/sessions/{self._sessionreferencenumber}/invoices'
        response = self._hook(endpoint=end_point, method=self._METHODGET)
        res_invoices = []
        invoices = response['invoices']
        for i in invoices:
            # required
            ordinalNumber = i['ordinalNumber']
            # required
            status = i['status']
            invoiceNumber = i.get('invoiceNumber')
            ksefNumber = i.get('ksefNumber')
            # required
            referenceNumber = i['referenceNumber']
            ok = status['code'] == 200
            description = self._daj_description(status)
            upo = i.get('upoDownloadUrl')
            i = self.INVOICES(ok=ok, ordinalNumer=ordinalNumber, msg=description,
                              invoiceNumber=invoiceNumber, ksefNumber=ksefNumber, referenceNumber=referenceNumber)
            res_invoices.append(i)
            # pobierz UPO
            if wez_upo is not None and upo is not None:
                response = self._hook_response(
                    endpoint=upo, requestmethod='GET')
                xml_upo = response.text
                wez_upo(i, xml_upo)

        return ok_session, msg, res_invoices
