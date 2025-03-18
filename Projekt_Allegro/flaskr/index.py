import requests
from dotenv import load_dotenv
import os
import time
from flask import render_template, request, redirect, url_for, flash, jsonify
from db import log_error, add_process_time



# stała delay wskazuje ile sekund jest przerwy między kolejnymi połączeniami
DELAY = 0
# stała max_products wskazuje ile produktów chcemy pokazać w wynikach
# 2024-12-16 20:48:56 do stałej max_products musi zostać przypisana wartość wielokrotności 30
# inaczej rzeczywista liczba wyników przekroczy wartość max_products
MAX_PRODUCTS = 210
UNEXPECTED_ERROR_MSG = "Wystąpił nieoczekiwany, nieznany błąd naszej aplikacji webowej." + \
                       "Możesz spróbować ponownie."

def get_auth_data():
    load_dotenv()
    # Dane do uwierzytelnienia
    # zmienne lokalne znajdują się w pliku .env
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    return client_id, client_secret

def get_access_token(client_id, client_secret):
    """
    Funkcja uzyskuje token dostępu do API Allegro.
    """
    # Endpointy Allegro API
    AUTH_URL = "https://allegro.pl/auth/oauth/token"
    FILE_TOKEN_PATH = "./token.txt"

    response = requests.post(
        AUTH_URL,
        auth=(client_id, client_secret),
        data={'grant_type': 'client_credentials'}
    )
    response.raise_for_status()
    token = response.json()['access_token']

    with open(f"{FILE_TOKEN_PATH}", "w") as file_token:
        file_token.write(token)

    return token


class AllegroConnCheckError(Exception):
    """Mainly to employ NoInternet_2 solution.
    To inform about a failure of solely the first Allegro connection attempt."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def allegro_api_connection_check():

    file_token_path = "./token.txt"

    if not os.path.exists(file_token_path):
        file_token = open(f"{file_token_path}", "w")
        file_token.close()
        token = ""
    else:
        with open(f"{file_token_path}", "r") as file_token:
            token = file_token.readline()

    PRODUCTS_URL = "https://api.allegro.pl/sale/products"
    PHRASE = "Nonexistent item"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
    }

    params = {
        'phrase': PHRASE
    }
    client_id, client_secret = get_auth_data()
    try:
        response = requests.get(PRODUCTS_URL, headers=headers, params=params)
        response.raise_for_status()
    except ConnectionError as e:
        print(f"allegro_api_connection_check(): Wystąpił błąd podczas pierwszego sprawdzenia połączenia z Allegro: {e}")
        get_access_token(client_id, client_secret)
        log_message = "First connection request was a failure. Token was renewed successfully."
        print(log_message)
        log_error("allegro_api_connection_check", log_message)
        raise AllegroConnCheckError(log_message)
    except requests.exceptions.HTTPError as e:
        get_access_token(client_id, client_secret)
        log_message = "HTTPError risen because of expired Token. It was renewed successfully."
        print(log_message)
        log_error("allegro_api_connection_check", log_message)
        raise AllegroConnCheckError(log_message)
    except Exception as e:
        log_message = f"allegro_api_connection_check(): Niespodziewany błąd podczas sprawdzenia połączenia z Allegro: {e}"
        print(log_message)
        log_error("allegro_api_connection_check", log_message)
        raise #2025-02-13 18:46:47 should preserve the original exception's traceback and allow it to propagate up
        # the call stack, maintaining all the information about what went wrong.

def check_connection():
    #time.sleep(10) #2025-02-10 18:10:13 Tymczasowy sposób na przetestowanie właściwego działania frontendu
    try:
        allegro_api_connection_check()
        #data_display() #2025-02-10 18:10:13 Tymczasowy sposób na przetestowanie właściwego działania frontendu
        return jsonify({'success': True}), 200
    except AllegroConnCheckError:
        err_msg = "check_connection() AllegroConnCheckError: Błąd na potrzeby testów. " + \
                  "Potwierdzeniem finalnego otrzymania odpowiedzi serwera Allegro."
        return jsonify({'success': True, 'error_message': err_msg}), 200
    except requests.exceptions.HTTPError as e:
        log_message = f"check_connection() except requests.exceptions.HTTPError : Wystąpił nieoczekiwany błąd: {e}"
        print(log_message)
        log_error("check_connection", log_message)
        return (jsonify({'success': False,
                        'error_message': 'Nie udało się połączyć z zewnętrznym serwerem Allegro, przepraszamy.'}), 500)
    except ConnectionError as e:#TODO: 2025-02-12 16:19:33: Sprawdzić, czemu dotychczasowe sposoby testowania...
        #TODO: 2025-02-12 16:19:33:... nie działają dla tego przypadku. ...
        # ... 2 połączenie nieudane - zostaje uruchomiony ten blok.
        log_message = f"check_connection() except ConnectionError : Wystąpił błąd połączenia internetowego: {e}"
        print(log_message)
        log_error("check_connection", log_message)
        return jsonify({'success': False, 'error_message': 'Brak połączenia internetowego.'}), 500
    except Exception as e:
        log_message = f"check_connection() Exception: Wystąpił nieoczekiwany błąd: {e}"
        print(log_message)
        log_error("check_connection",log_message)
        return jsonify({'success': False, 'error_message': 'Wystąpił nieprzewidziany, nieznany błąd.'}), 500


def search_form_display():
    return render_template('main.html')


def data_display():
    phrase = request.form['phrase']
    if phrase.strip() == "" or len(phrase) > 1024:  # Sprawdź, czy phrase jest pusty lub zawiera tylko białe znaki
        return redirect(url_for('search_form_display'))

    def data_download_and_preparation():

        def get_and_process_products_data(phrase, token):
            PRODUCTS_URL = "https://api.allegro.pl/sale/products"

            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.allegro.public.v1+json',
            }
            # id kolejnej strony generowany przez API, dzięki temu mamy dostęp do kolejnego zestawu 30 produktów
            next_page_id = ''
            all_products = []
            number_products = 0

            while number_products < MAX_PRODUCTS:
                params = {
                    'phrase': phrase,
                    'page.id': next_page_id
                }
                time_start=time.perf_counter()
                response = requests.get(PRODUCTS_URL, headers=headers, params=params, timeout = 180)
                response.raise_for_status()
                time_end = time.perf_counter()
                process_time = time_end-time_start
                add_process_time("get_products_data",process_time)
                time_start = time.perf_counter()
                data = response.json()
                products = data.get('products', [])
                all_products.extend(products)

                number_products += len(products)
                next_page = data.get('nextPage')
                time_end = time.perf_counter()
                process_time = time_end - time_start
                add_process_time("process_products_data", process_time)
                if not next_page:  # Brak kolejnej strony
                    break
                next_page_id = data['nextPage']['id']
                time.sleep(DELAY)

            # Porządkowanie wyników
            time_start = time.perf_counter()
            data_allegro_products = {'phrase': phrase}
            data_allegro_products['amount'] = len(all_products)
            for ordinal, product in enumerate(all_products):

                data_allegro_product = {'ID Produktu': product.get('id', 'Brak danych')}
                data_allegro_product['Nazwa'] = product.get('name', 'Brak nazwy')

                try:
                    brand = product['parameters'][0]['valuesLabels'][0]
                    data_allegro_product['Marka'] = brand
                except:
                    data_allegro_product['Marka'] = "Producent: Brak danych"

                data_allegro_products[f'Product{ordinal}'] = data_allegro_product
            time_end = time.perf_counter()
            process_time = time_end - time_start
            add_process_time("process_data_pack", process_time)
            return data_allegro_products

        pack_data_allegro_products = {}

        file_token_path = "./token.txt"
        if os.path.exists(file_token_path) == False:
            file_token = open(f"{file_token_path}", "w")
            file_token.close()
            token = ""
        else:
            with open(f"{file_token_path}", "r") as file_token:
                token = file_token.readline()

        client_id, client_secret = get_auth_data()

        #Użycie bloku try z powodu przewidzianego błędu nieaktualnego tokenu
        try:
            pack_data_allegro_products = get_and_process_products_data(phrase, token)
        except requests.exceptions.HTTPError as http_err:
            # Obsługa specyficznych kodów HTTP
            if http_err.response.status_code == 401:
                log_message = "Błąd 401: Token nieaktualny lub nieprawidłowy. Odświeżam token..."
                print(log_message)
                log_error("data_download_and_preparation", log_message)
                token = get_access_token(client_id, client_secret)
                return get_and_process_products_data(phrase, token)
            elif http_err.response.status_code == 403:
                log_message = "Błąd 403: Brak uprawnień do zasobu. Sprawdź token i endpoint."
                print(log_message)
                log_error("data_download_and_preparation", log_message)
            elif http_err.response.status_code == 429:
                retry_after = int(http_err.response.headers.get('Retry-After', 1))
                log_message = f"Błąd 429: Przekroczono limit żądań. Spróbuję ponownie za {retry_after} sekund."
                print(log_message)
                log_error("data_download_and_preparation", log_message)
                time.sleep(retry_after)
                return get_and_process_products_data(phrase, token)
            elif 500 <= http_err.response.status_code < 600:
                log_message = f"HTTPError: Wystąpił nieoczekiwany błąd HTTP ({http_err.response.status_code}): {http_err}"
                print(log_message)
                log_error("data_download_and_preparation", log_message)
            else:
                log_message = f"HTTPError: Wystąpił nieoczekiwany błąd HTTP ({http_err.response.status_code}): {http_err}"
                print(log_message)
                log_error("data_download_and_preparation", log_message)

        return pack_data_allegro_products

    try:
        pack_data_allegro_products = data_download_and_preparation()
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            log_message = "Błąd naszej aplikacji webowej. Możesz spróbować ponownie."
            print(log_message)
            log_error("data_display", log_message)
            return redirect(url_for('search_form_display'))
        elif http_err.response.status_code == 429:
            retry_after = int(http_err.response.headers.get('Retry-After', 1))
            user_retry_after = retry_after * 2
            log_message = f"Przekroczono limit żądań. Serwer odpowiada czasem oczekiwania: {retry_after} sekund."
            print(log_message)
            log_error("data_display", log_message)
            flash("Nasza aplikacja webowa przekroczyła dozwoloną liczbę połączeń z serwerem Allegro." + \
                  f"Spróbuj ponownie za {user_retry_after} sekund/y.")
            return redirect(url_for('search_form_display'))
        elif 500 <= http_err.response.status_code < 600:
            log_message = f"Błąd serwera ({http_err.response.status_code})."
            print(log_message)
            log_error("data_display", log_message)
            flash(UNEXPECTED_ERROR_MSG)
            return redirect(url_for('search_form_display'))
        else:
            log_message = f"HTTPError: {http_err}"
            print(log_message)
            flash(UNEXPECTED_ERROR_MSG)
            log_error("data_display", log_message)
            return redirect(url_for('search_form_display'))
    except requests.exceptions.ConnectionError:
        log_message = "data_display(): Błąd połączenia. Rezygnuję i wracam do strony głównej."
        print(log_message)
        time.sleep(DELAY)
        flash("Błąd połączenia. Możesz spróbować ponownie.")
        log_error("data_display", log_message)
        return redirect(url_for('search_form_display'))

    except requests.exceptions.Timeout:
        log_message = "Przekroczono limit czasu oczekiwania."
        print (log_message)
        flash("Błąd połączenia. Możesz spróbować ponownie.")
        log_error("data_display", log_message)
        return redirect(url_for('search_form_display'))
    except Exception as e:
        log_message = f"data_display() Exception: Wystąpił nieoczekiwany błąd: {e}"
        print(log_message)
        flash(UNEXPECTED_ERROR_MSG)
        log_error("data_display", log_message)
        return redirect(url_for('search_form_display'))
    return render_template('results.html', data=pack_data_allegro_products)
