import logging
from time import sleep
import os
from typing import Callable, Optional
import hashlib
from collections import namedtuple
from collections.abc import Iterator
import tempfile

from .httphook import HOOKHTTP
from .encrypt import (
    decrypt_aes_cbc,
    get_key_and_iv,
    encrypt_symmetric_key, to_base64,
    encrypt_invoice, calculate_hash, encrypt_padding
)

from .authksef import ABSTRACTTOKEN, AUTHTOKEN, AUTHCERT


def _getlogger():
    logger = logging.getLogger(__name__)
    return logger


_logger = _getlogger()


def _l(info: str):
    _logger.info(info)


class KSEFSDK(HOOKHTTP):

    INVOICES = namedtuple(typename='invoices_ksef', field_names=[
                          'ok', 'ordinalNumer', 'msg', 'invoiceNumber', 'ksefNumber', 'referenceNumber'])

    DEVKSEF = 0
    PREKSEF = 1
    PRODKSEF = 2

    SUBJECT1 = 'Subject1'  # sprzedawca
    SUBJECT2 = 'Subject2'  # nabywca
    SUBJECT3 = 'Subject3'  # Podmiot 3
    SUBJECTAUTHORIZED = "SubjectAuthorized"  # Podmiot upoważniony
    _PAGE_SIZE = 250

    _env_dict = {
        DEVKSEF: 'https://api-test.ksef.mf.gov.pl',
        PREKSEF: 'https://api-demo.ksef.mf.gov.pl',
        PRODKSEF: 'https://api.ksef.mf.gov.pl'
    }

    @staticmethod
    def rate_limiter(max_retries: int):
        def decorator(func):
            def wrapper():
                sleep_time = KSEFSDK._RATEDELAYTIME
                for attempt in range(max_retries):
                    res = func()
                    if res is not None:
                        return res
                    _l(f'Próba {attempt + 1} nie powiodła się, ponawiam po {sleep_time} sekundach...')
                    sleep(sleep_time)
                    sleep_time += 2
                raise TimeoutError(
                    f'Przekroczono maksymalną liczbę prób: {max_retries}')
            return wrapper
        return decorator

    @staticmethod
    def _reference_number(ref: dict) -> str:
        return ref['referenceNumber']

    @staticmethod
    def _verify_environment(env: int):
        if env not in KSEFSDK._env_dict:
            raise ValueError(
                'Niepoprawne środowisko, parametr env musi mieć wartość DEVKSEF, PREKSEF lub PRODKSEF')

    @classmethod
    def initsdk(cls, env: int, nip: str, token: str):
        KSEFSDK._verify_environment(env)
        A = AUTHTOKEN(token=token)
        return cls(url=KSEFSDK._env_dict[env], nip=nip, A=A)

    @classmethod
    def initsdkcert(cls, env: int, nip: str, p12pk: bytes, p12pc: bytes):
        KSEFSDK._verify_environment(env)
        A = AUTHCERT(p12pk=p12pk, p12pc=p12pc)
        return cls(url=KSEFSDK._env_dict[env], nip=nip, A=A)

    _SESSIONRATELIMITER = 5
    _INVOICERATELIMITER = 10
    _INVOICEGETRATELIMITER = 15
    _RATEDELAYTIME = 2

    def __init__(self, url: str, nip: str, A: ABSTRACTTOKEN):
        super(KSEFSDK, self).__init__(base_url=url)
        challenge, timestamp = self._get_challengeandtimestamp()
        kseftoken_certificate, self._symmetrickey_certificate = self._get_public_certificate()
        A.set_params(timestamp=timestamp,
                     kseftoken_certificate=kseftoken_certificate)
        self._referencenumber, self._authenticationtoken = A.auth_ksef(
            H=self, nip=nip, challenge=challenge)
        self._session_status()
        o_tokens = self._redeem_token()
        self.set_tokes(*o_tokens)
        self._symmetric_key, self._iv = get_key_and_iv()
        self._sessionreferencenumber = ''
        self._sessioninvoicereferencenumber = ''
        self._invoicereferencenumber = ''

    def _get_challengeandtimestamp(self) -> tuple[str, str]:
        response = self.hook('auth/challenge', bearer=self._NOBEARER)
        return response['challenge'], response['timestamp']

    def _get_public_certificate(self) -> tuple[str, str]:
        response = self.hook(
            'security/public-key-certificates', method=self._METHODGET, bearer=self._NOBEARER)
        kseftoken_certificate = next(
            e['certificate'] for e in response if 'KsefTokenEncryption' in e['usage'])
        symmetrickey_certificate = next(
            e['certificate'] for e in response if 'SymmetricKeyEncryption' in e['usage'])
        return kseftoken_certificate, symmetrickey_certificate

    def _session_status(self) -> None:
        url = f'auth/{self._referencenumber}'

        @self.rate_limiter(self._SESSIONRATELIMITER)
        def _status():
            response = self.hook(
                url, method=self._METHODGET, bearer=self._BEARERTOKEN)
            status = response['status']['code']
            description = response['status']['description']
            if status == 100:
                return None
            elif status == 200:
                return True
            else:
                raise ValueError(
                    f'Session activation failed: {status} - {description}')
        _status()

    def _redeem_token(self) -> tuple[str, str]:
        response = self.hook(endpoint='auth/token/redeem',
                             bearer=self._BEARERTOKEN)
        access_token = response['accessToken']['token']
        refresh_token = response['refreshToken']['token']
        return access_token, refresh_token

    def session_terminate(self) -> None:
        url = f'auth/sessions/{self._referencenumber}'
        self.hook(url, method=self._METHODDEL)

    def close_session(self) -> None:
        url = f'sessions/online/{self._sessionreferencenumber}/close'
        self.hook(url)

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

    def _prepare_query(self, subject: str, date_from: str, date_to: str) -> dict:
        query = {
            'subjectType': subject,
            'dateRange': {
                'dateType': 'PermanentStorage',
                'from': date_from,
                'to': date_to
            }
        }
        return query

    def start_session(self) -> None:
        request_data = self._prepare_session_data()
        response = self.hook(endpoint='sessions/online', body=request_data)
        self._sessionreferencenumber = self._reference_number(response)

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

        @self.rate_limiter(self._INVOICERATELIMITER)
        def _status() -> tuple[bool, str, str]:
            response = self.hook(endpoint=end_point, method=self._METHODGET)
            code = response['status']['code']
            # stworz komunikat
            description = self._daj_description(response['status'])

            # czy w trakcie przetwarzania
            if code == 100 or code == 150:
                _l(description)
                return None
            if code == 200:
                self._invoicereferencenumber = self._reference_number(
                    response) if is_interactive else ''
                return True, description, response['ksefNumber'] if is_interactive else ''
            return False, description, ''
        return _status()

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
        response = self.hook(endpoint=end_point, body=request_data)
        self._sessioninvoicereferencenumber = self._reference_number(response)
        return self._invoice_status()

    def pobierz_upo(self, invoicereferencenumber: Optional[str] = None) -> str:
        invoicereferencenumber = invoicereferencenumber or self._invoicereferencenumber
        end_point = f'sessions/{self._sessionreferencenumber}/invoices/{invoicereferencenumber}/upo'
        response = self.hook_response(
            endpoint=end_point, method=self._METHODGET)
        return response.text

    def get_invoice(self, ksef_number: str) -> str:
        end_point = f'invoices/ksef/{ksef_number}'
        response = self.hook_response(
            endpoint=end_point, method=self._METHODGET)
        return response.text

    def get_invoices_metadata(self, date_from: str, date_to: str, subject: str) -> list[dict]:
        invoices = []
        pageOffset = 0
        while True:
            end_point = f'invoices/query/metadata?pageSize={self._PAGE_SIZE}&pageOffset={pageOffset}'
            query = {
                'subjectType': subject,
                'dateRange': {
                    'dateType': 'PermanentStorage',
                    'from': date_from,
                    'to': date_to
                }
            }
            response = self.hook(endpoint=end_point, body=query)
            invoices.extend(response['invoices'])
            mess = f'Odczytana strona {pageOffset+1}, liczba faktur łącznie: {len(invoices)}'
            hasMore = response['hasMore']
            isTruncated = response['isTruncated']
            if hasMore and isTruncated:
                err_mess = 'Ostrzeżenie: Odczytane dane są niepełne (isTruncated=True), zawęć zapytanie.'
                raise ValueError(err_mess)

            mess = f'Odczytana strona {pageOffset+1}, liczba faktur łącznie: {len(invoices)}'
            _l(mess)
            if not hasMore:
                break
            pageOffset += 1

        return invoices

    def get_invoices_zakupowe_metadata(self, date_from: str, date_to: str) -> list[dict]:
        return self.get_invoices_metadata(date_from, date_to, subject=self.SUBJECT2)

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
        response = self.hook(endpoint=end_point, body=request_data)
        self._sessionreferencenumber = self._reference_number(response)
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
            self.hook_response(
                endpoint=url, data=encrypted_data, requestmethod=method, requestheaders=headers)
        # zamknięcie
        end_point = f'sessions/batch/{self._sessionreferencenumber}/close'
        response = self.hook(endpoint=end_point)
        # teraz czekanie na zakończenie przetwarzania
        end_point = f'sessions/{self._sessionreferencenumber}'
        ok_session, msg, _ = self._invoice_status(end_point=end_point)

        # sprawdz faktury i przygotuj wynik
        end_point = f'/sessions/{self._sessionreferencenumber}/invoices'
        response = self.hook(endpoint=end_point, method=self._METHODGET)
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
            referenceNumber = self._reference_number(i)
            ok = status['code'] == 200
            description = self._daj_description(status)
            upo = i.get('upoDownloadUrl')
            i = self.INVOICES(ok=ok, ordinalNumer=ordinalNumber, msg=description,
                              invoiceNumber=invoiceNumber, ksefNumber=ksefNumber, referenceNumber=referenceNumber)
            res_invoices.append(i)
            # pobierz UPO
            if wez_upo is not None and upo is not None:
                response = self.hook_response(
                    endpoint=upo, requestmethod='GET')
                xml_upo = response.text
                wez_upo(i, xml_upo)

        return ok_session, msg, res_invoices

    def get_batch_invoices(self, date_from: str, date_to: str, subject: str) -> tuple[int, bytes]:
        request_data = self._prepare_session_data()
        query = self._prepare_query(
            subject=subject, date_from=date_from, date_to=date_to)
        metadata = request_data | {'filters':  query}
        end_point = 'invoices/exports'
        response = self.hook(endpoint=end_point, body=metadata)
        reference_number = self._reference_number(response)
        _l(f'Zainicjowano eksport batchowy, numer referencyjny: {reference_number}')
        # teraz czekamy na zakończenie przetwarzania
        end_point = f'invoices/exports/{reference_number}'

        @self.rate_limiter(self._INVOICEGETRATELIMITER)
        def _get_exported_invoices() -> dict:
            response = self.hook(endpoint=end_point, method=self._METHODGET)
            code = response['status']['code']
            description = response['status']['description']
            if code == 100:
                _l('Eksport w trakcie przetwarzania, czekam...')
                return None
            if code == 200:
                _l('Eksport zakończony, pobieram dane...')
                return response['package']
            else:
                raise ValueError(
                    f'Błąd podczas eksportu: {code} - {description}')

        packages = _get_exported_invoices()
        isTruncated = packages['isTruncated']
        if isTruncated:
            err_mess = 'Ostrzeżenie: Odczytane dane są niepełne (isTruncated=True), zawęź zapytanie.'
            raise ValueError(err_mess)
        # zdekoduj dane

        print(packages)
        invoiceCount = packages['invoiceCount']
        parts = packages['parts']
        zipped_data = bytearray()
        for part in parts:
            url = part['url']
            response = self.hook_response(endpoint=url, requestmethod='GET')
            encrypted_data = response.content
            decrypted_data = decrypt_aes_cbc(
                key=self._symmetric_key, iv=self._iv, b=encrypted_data)
            zipped_data.extend(decrypted_data)
        _l(f'Pobrano i zdekodowano dane, liczba faktur: {invoiceCount}')
        return invoiceCount, zipped_data
