## Opis
Zaimplementowany jest tutaj prosty moduł w Python 3 umożliwiający wysyłkę faktur do KSeF 2.0 w trybie interaktywnym oraz wsadowym. Autentykacja za pomocą tokena lub certyfikatu. Moduł może być wykorzystany jako pomocnicza biblioteka do komunikacji z systemem KSeF 2.0. 

Zaimplementowane są następujące funkcjonalności:
* Inicjalizacja, autentykacja za pomocą token i rozpoczęcie sesji uwierzytelnienia
* Inicjalizacja, autentykacja z wykorzystaniem podpisu XAdES
* Otworzenie sesji interaktywnej
* Wysłanie faktury
* Pobranie UPO
* Zamknięcie sesji interaktywnej
* Zamknięcie sesji uwierzytelniania
* Odczytanie faktury na podstawie numeru KSeF
* Odczytanie nagłówków faktur zakupowych na podstawie zakresu dat
* Wysłanie paczki faktur w trybie wsadowym (batchowym)

## Python

Testowane dla wersji: 3.10, 3.11 i 3.12

## Patrz także

https://github.com/stanislawbartkowski/ksef_cli

Jest to rozszerzenie umożliwiające komunikację z systemem KSeF 2.0 z poziomu command line

## Instalacja

> pip install git+https://github.com/stanislawbartkowski/ksef_pyth.git

## Linki

https://github.com/m32/ksef

https://api-test.ksef.mf.gov.pl/docs/v2/index.html

https://github.com/kzawISPL


# Testowanie

W unit testach jest zawarty fikcyjny NIP oraz testowy token. Można wykorzystać ten token lub utworzyć własny. W wersji testowej nie ma gwarancji bezpieczeństwa danych, powinny być używane wyłącznie dane fikcyjne lub zanonimizowane. Do testowania autentykacji podpisem XAdES były wykorzystywane tylko testowe certyfikaty generowane poprzez testowe środowisko KSeF 2.0

# Utworzenie testowego tokena

https://web2te-ksef.mf.gov.pl/web/

Należy zalogować się do aplikacji testowej za pomocą fikcyjnego NIP i w zakładce "Tokeny" utworzyć token ze wszystkimi uprawnieniami.

# Testowe certyfikaty

https://web2te-ksef.mf.gov.pl/web/login

Należy zalogować się do aplikacji testowej za pomocą fikcyjnego NIP i w zakładce "Wnioskuj o certyfikat" pobrać klucz (należy zapamiętać wprowadzone hasło) i następnie w zakładce "Lista certyfikatów" pobrać utworzony certyfikat.

# Struktura kodu

* ksef/sdk
  * encrypt.py Pomocniczy moduł do szyfrowania i deszyfrowania danych. Wykorzystywany wewnętrznie przez ksefsdk.py
  * ksefsdk.py Główny moduł zawierający klasę KSEFSDK z funkcjonalnymi metodami. Klasa KSEFSDK jest jedynym obiektem dostępnym zewnętrznie.
  * httphook.py Pomocniczy moduł, rozszerzenie requests
  * authksef.py Pomocniczy moduł, dwa warianty autentykacji
  * xades_sign.py Pomocniczy moduł, podpis XAdES (contrib: https://github.com/m32/ksef/blob/v2.0/t-03-auth-02-sign.py)
* ksef/pattern/requests.xml
  * Wykorzystywany wewnętrznie, wzorzec do utworzenia AuthTokenRequestń
* tests Testy unitowe

# Zaimplementowane funkcjonalności

| Funkcjonalność | API link | Endpoint | Metoda w klasie KSEFSDK
| -- | -- | -- | -- |
| Inicjalizacja uwierzytelnienia | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Uzyskiwanie-dostepu/paths/~1auth~1challenge/post) | /api/v2/auth/challenge | Konstruktor KSEFSDK
| Pobranie certyfikatów | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Certyfikaty-klucza-publicznego/paths/~1security~1public-key-certificates/get) | api/v2/security/public-key-certificates | Konstruktor
| Uwierzytelnienie z wykorzystaniem tokena KSeF | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Uzyskiwanie-dostepu/paths/~1auth~1ksef-token/post) | /api/v2/auth/ksef-token | Konstruktor initsdkcert
| Uwierzytelnienie z wykorzystaniem podpisu XAdES | [link](https://ksef-demo.mf.gov.pl/docs/v2/index.html#tag/Uzyskiwanie-dostepu/paths/~1auth~1xades-signature/post) | /api/v2/auth/xades-signature | Konstruktor 
| Pobranie statusu uwierzytelniania | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Uzyskiwanie-dostepu/paths/~1auth~1%7BreferenceNumber%7D/get) | /api/v2/auth/{referenceNumber} | Konstruktor
| Pobranie tokenów dostępowych | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Uzyskiwanie-dostepu/paths/~1auth~1token~1redeem/post) | /api/v2/auth/token/redeem | Konstruktor
| Otwarcie sesji interaktywnej | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Wysylka-interaktywna/paths/~1sessions~1online/post) | /api/v2/sessions/online | start_session
| Wysłanie faktury | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Wysylka-interaktywna/paths/~1sessions~1online~1%7BreferenceNumber%7D~1invoices/post) | /api/v2/sessions/online/{referenceNumber}/invoices | send_invoice
| Pobranie statusu faktury z sesji | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Status-wysylki-i-UPO/paths/~1sessions~1%7BreferenceNumber%7D~1invoices~1%7BinvoiceReferenceNumber%7D/get) | /v2/sessions/{referenceNumber}/invoices/{invoiceReferenceNumber} | send_invoice
| Pobranie UPO faktury z sesji na podstawie numeru referencyjnego faktury | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Status-wysylki-i-UPO/paths/~1sessions~1%7BreferenceNumber%7D~1invoices~1%7BinvoiceReferenceNumber%7D~1upo/get) | /api/v2/sessions/{referenceNumber}/invoices/{invoiceReferenceNumber}/upo | pobierz_upo
| Zamknięcie sesji interaktywnej | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Wysylka-interaktywna/paths/~1sessions~1online~1%7BreferenceNumber%7D~1close/post) | /api/v2/auth/sessions/{referenceNumber} | close_session 
| Unieważnienie sesji uwierzytelnienia | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Aktywne-sesje/paths/~1auth~1sessions~1%7BreferenceNumber%7D/delete) | /api/v2/auth/sessions/{referenceNumber} | terminate_session
| Odczytanie faktury | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Pobieranie-faktur/paths/~1invoices~1ksef~1%7BksefNumber%7D/get) | /api/v2/invoices/ksef/{ksefNumber} | get_invoice
| Odczytanie nagłówków faktur | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Pobieranie-faktur/paths/~1invoices~1query~1metadata/post) | /api/v2/invoices/query/metadata | Odczytanie faktur (także zakupowych)
| Otwarcie sesji wsadowej | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Wysylka-wsadowa/paths/~1sessions~1batch/post) | /api/v2/sessions/batch | send_batch_session_bytes
| Zamknięcie sesji wsadowej | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Wysylka-wsadowa/paths/~1sessions~1batch~1%7BreferenceNumber%7D~1close/post) | /api/v2/sessions/batch/{referenceNumber}/close | send_batch_session_bytes
| Pobranie faktur sesji | [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Status-wysylki-i-UPO/paths/~1sessions~1%7BreferenceNumber%7D~1invoices/get) | /api/v2/sessions/{referenceNumber}/invoices | send_batch_session_bytes

# Działanie

## Ogólny opis

Jest to moduł napisany w Python 3. Scenariusze użycia

### Wysłanie fakturt do KSef i pobranie UPO
* Utworzenie klasy KSEFSDK, autentykacja token lub XAdSE
* Rozpoczęcie sesji interaktywnej (metoda open_session)
* Wysłanie jednej lub więcej faktur oraz odczytanie wygenerowanego numeru KSeF (send_invoice)
* (Opcjonalnie) Odczytanie UPO (pobierz_upo)
* Zamknięcie sesji interaktywnej (close_session)
* Zamknięcie sesji uwierzytelnienia (terminate_session)

### Odczytanie faktury na podstawie numeru KSeF
* Utworzenie klasy KSEFSDK, autentykacja token lub XAdSE
* Odczytanie faktury w formacie XML (get_ivoice)
* Zamknięcie sesji uwierzytelnienia (terminate_session)

### Odczytanie nagłówków faktur zakupowych
* Utworzenie klasy KSEFSDK, autentykacja token lub XAdSE
* Pobranie nagłówków (metadata) faktur zakupowych na podstawie daty faktury (get_invoices_zakupowe_metadata)
* (Opcjonalnie) Odczytanie treści faktury na podstawie numer KSeF (get_invoice)
* Zamknięcie sesji uwierzytelnienia (terminate_session)

Błędy (także z konstruktora klasy) są wyrzucane jako HTTPError lub ValueError. 


## Inicjalizacja, konstruktor KSEFSDK. autentykacja tokenem KSeF

*KSEFSDK.initsdk(env: int, nip: str, token: str)*

Parametry:
* env Może przybierać trzy wartości: KSEFSDK.DEVKSEF, KSEFSDK.PREKSEF, KSEFSDK.PRODKSEF. Uwaga: testowane tylko w środowisku KSEFSDK.DEVKSEF
* nip NIP do uwierzytelnienia
* token Token KSeF do uwierzytelnienia

Działanie:
* Inicjalizacja uwierzytelnienia
* Pobranie publicznych certyfikatów z kluczem do szyfrowania
* Autentykacja poprzez token KSeF

Zwraca:

Zainicjalizowana klasa KSEFSDK jeśli autentykacja przebiegła pomyślnie. Jeśli wystąpił błąd, to wyrzucany jest wyjątek.

## Inicjalizacja, konstruktor KSEFSDK, autentykacja podpisem XAdES

*KSEFSDK.initsdkcert(env: int, nip: str, p12pk: bytes, p12pc: bytes)*

Parametry:
* env Może przybierać trzy wartości: KSEFSDK.DEVKSEF, KSEFSDK.PREKSEF, KSEFSDK.PRODKSEF. Uwaga: testowane tylko w środowisku KSEFSDK.DEVKSEF
* nip NIP do uwierzytelnienia
* p12pk Odczytany klucz prywatny
* p12pc Odczytany certyfikat

Działanie:
* Inicjalizacja uwierzytelnienia
* Pobranie publicznych certyfikatów z kluczem do szyfrowania
* Autentykacja podpisem XAdES z użyciem wprowadzonych certyfikatów

UWAGA:
Klucz i certyfikat do podpisu XAdES musi być odczytany zewnętrznie. 

Zwraca:

Zainicjalizowana klasa KSEFSDK jeśli autentykacja przebiegła pomyślnie. Jeśli wystąpił błąd, to wyrzucany jest wyjątek.

## Otworzenie sesji interaktywnej

*start_session*

Działanie:

Rozpoczęcie sesji interaktywnej

## Wysłanie faktury

*send_invoice(invoice:str)*

Parametry:
* invoice Faktura do wysłania

Działanie:

Szyfruje i wysyła fakturę do KSeF.

Zwraca:

tuple[ok, error_mess, numer_ksef]
* ok True/False, wysyłka udana lub nieudana
* err_mess Jeśli wysyłka nieudana, to komunikat o przyczynie błędu (np. Niepoprawny format faktury)
* numer_ksef Jeśli wysyłka udana, to numer KSeF wysłanej faktury

Dodatkowa uwaga:

W tej metodzie błąd jest zwracany na dwa sposoby. Wartość *ok* jako False oraz *err_mess* z bardziej szczegółowym komunikatem o błędzie oraz jako wyjątek HTTPError lub ValueError

## Odczytanie UPO

*pobierz_upo(invoicereferencenumnber)*

Parametry
* invoicereferencenumnber Dla sesji interaktywnej powinno być pominięte. Dla sesji wsadowej musi być ustawiony *invoicereferencenumber* odczytany z wyniku metody *send_batch_session_bytes*

Działanie:

Pobiera UPO ostatnio przesłanej faktury jeśli faktura została wysłana z sukcesem. Musi być wywołana bezpośrednio po send_invoice. Dla sesji wsadowej wymaga podania parametru. Dla sesji wsadowej jest alternatywna metoda pobierania pliku UPO.

Zwraca:

UPO w postaci stringu w formacie XML

## Zamknięcie sesji interaktywnej

*close_session*

Działanie:

Zamyka sesję interaktywną rozpoczętą wywołaniem start_session.

## Zamknięcie sesji uwierzytelniania

*terminate_session*

Działanie:

Zamyka sesję uwierzytelnienia rozpoczętą w konstruktorze KSEFSDK.

## Odczytanie faktury według numeru KSef

*get_invoice(ksef_number:str)->str*

Parametry:
* ksef_number Numer KSeF faktury.

Zwraca:

Faktury jako plik XML

Działanie:

Odczytuje fakturę na podstawie numeru KSeF. Jest to numer nadawany przez KSeF po pomyślnym wysłaniu faktury. Numer jest zwracay przez metodę *send_invoice*. Jeśli faktura o podanym numerze nie istnieje, to jest rzucany wyjątek ValueError

## Odczytanie nagłówków faktur na podstawie dat
*get_invoices_metadata(self, date_from: str, date_to: str,subject:str) -> list[dict]:*

Parametry:
* date_from Data w formacie YYYY-MM-DD. Data początkowa zakresu daty wystawienia faktury
* date_to Data w formacie YYYY-MM-DD. Data końcowa zakresu daty wystawienia faktury
* subject Rodzaj faktury do odczytania. Możliwe są wartości:
  * KSEFSDK.SUBJECT1 = 'Subject1'  Faktury sprzedaży
  * KSEFSDK.SUBJECT2 = 'Subject2'  Faktury zakupowe
  * KSEFSDK.SUBJECT3 = 'Subject3'  Faktury sprzedaży
  * KSEFSDK.SUBJECTAUTHORIZED = "SubjectAuthorized"

Zwraca:
Lista nagłówków (metadata) faktur zakupowych w zarejestrowych w KSeF na naszym koncie.

Działanie:

Parametr query:
```python
     query = {
            'subjectType': subject,
            'dateRange': {
                'dateType': 'PermanentStorage',
                'from': date_from,
                'to': date_to
            }
        }
```
UWAGA: Faktury są odczytywane przyrostowe z rozmiarem strony 250. Nie jest natomiast obsługiwnay przypadek isTrucated. W takiej sytuacji wyrzucany jest bład i dane nie są odczytywane.


## Odczytanie nagłówków faktur zakupowych na podstawie dat
*get_invoices_zakupowe_metadata(self, date_from: str, date_to: str) -> list[dict]:*

To samo co: 
*get_invoices_metadata(self, date_from, date_to ,subject = KSEFSDK.SUBJECT2) -> list[dict]:*

## Wysłanie paczki faktur w trybie wsadowym

Tryb wsadowy ma następujące zalety:
* Wysyłanie faktur z załącznikami
* Wiele faktur za pomocą jednego wywołania
* Duża liczba faktur w jednej sesji, rozmiar danych do 5GB
* UWAGA: metoda nie kompresuje danych. Dane przekazane do metody muszą już być skompresowane do postaci ZIP.
* UWAGA: w środowisku testowym istnieje limit 10 faktur w jednej wysyłce.


*send_batch_session_bytes(self, payload: Generator[bytes, None, None], wez_upo: Optional[Callable] = None) -> tuple[bool, str, list[INVOICES]]:*

Parametry:
* payload Generator zwracający kolejne porcje danych. Dane muszą być zgodne z warunkami opisanymi w metodzie [link](https://api-test.ksef.mf.gov.pl/docs/v2/index.html#tag/Wysylka-wsadowa/paths/~1sessions~1batch/post). Skomasowane dane muszą tworzyć prawidłowo skompresowany plik w formacie ZIP
* wez_upo Parametr opcjonalny. Jeśli jest zdefiniowany, to umożliwia natychmiastowe pobranie pliku UPO dla faktur zaakceptowanych w systemie KSeF 2.0

Zwracana wartość tuple[bool, str, list[INVOICES]]
* ok True/False, sesja zakończona sukcesem. "Sukces" oznacze, że dane były poprawnie skompresowane i przesłane. Natomiast nie oznacza, że wszystkie faktury w paczce zostały zaakceptowane. Jeśli część faktur została odrzucona, to sesja będzie także oznaczona jako "Sukces", zaś status poszczególnych faktur trzeba rozpoznać na podstawie wyniku wywołania.
* msg Komunikat o błędzie w razie niepowodzenia
* invoices List informacji o wysłanych i zaakceptowanych fakturach. Zawiera informacje zarówno o fakturach zaakceptowanych z sukcesem oraz także o fakturach odrzuconych. Jeden element listy zawiera informacje:
  * ok True/False Faktura zaakceptowana lub nie
  * ordinalNumber Numer sekwencyjny faktury w paczce (od 1)
  * msg Komunikat o błędzie jeśli faktura odrzucona
  * invoiceNumber Numer faktury
  * ksefNumber Jeśli faktura zaakceptowana w systemie KSeF, to nadany numer KSeF
  * referenceNumber Jesli faktura zaakceptowana, to referenceNumber który może być użyty do pobrania UPO (metoda pobierz_upo)
 
 Sekwencja działań

 * Przegląda *payload*, szyfruje poszczególne porcje danych i zapamiętuje w plikach tymczasowym.
 * Wywołuje *Otwarcie sesji wsadowej*
 * Przesyła kolejne zaszyfrowane porcje danych na podstawie wyniku z *Otwarcie sesji wsadowej*. Pliki tymczasowe są usuwane.
 * Wywołuje *Zamknięcie sesji wsadowej* co inicjalizuje przetwarzanie paczki faktur
 * Czeka na zakończenie przetwarzania, wywołanie *Pobranie statusu sesji*
 * Odczytuje listę faktur po zakończeniu sesji wywołując *Pobranie faktur sesji* i tworzy dane wynikowe. Dla faktur zaakceptowanych wywołuje metodę *wez_upo* 

# Przykłady użycia

https://github.com/stanislawbartkowski/ksef_pyth/blob/main/tests/test1.py

https://github.com/stanislawbartkowski/ksef_pyth/blob/main/sample/test.py

# Dev environment, happy coding

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
code .
```


