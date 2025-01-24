import requests
from dotenv import load_dotenv
import os
import time
from flask import render_template, request, redirect, url_for, flash

# stała delay wskazuje ile sekund jest przerwy między kolejnymi połączeniami
DELAY = 0
# stała max_products wskazuje ile produktów chcemy pokazać w wynikach
# 2024-12-16 20:48:56 do stałej max_products musi zostać przypisana wartość wielokrotności 30
# inaczej rzeczywista liczba wyników przekroczy wartość max_products
MAX_PRODUCTS = 210

def search_form_display():
    return render_template('main.html')

def data_display():
    phrase = request.form['phrase']
    if phrase.strip() == "" or len(phrase) > 1024: # Sprawdź, czy phrase jest pusty lub zawiera tylko białe znaki
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
                response = requests.get(PRODUCTS_URL, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                products = data.get('products', [])
                all_products.extend(products)

                number_products += len(products)
                next_page = data.get('nextPage')
                if not next_page: # Brak kolejnej strony
                    break
                next_page_id = data['nextPage']['id']
                time.sleep(DELAY)


            # Porządkowanie wyników
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

            return data_allegro_products

        def get_access_token(client_id, client_secret):
            """
            Funkcja uzyskuje token dostępu do API Allegro.
            """
            response = requests.post(
                AUTH_URL,
                auth=(client_id, client_secret),
                data={'grant_type': 'client_credentials'}
            )
            response.raise_for_status()
            token = response.json()['access_token']

            with open(f"{file_token_path}", "w") as file_token:
                file_token.write(token)

            return token

        load_dotenv()
        # Dane do uwierzytelnienia
        #zmienne lokalne znajdują się w pliku .env
        CLIENT_ID = os.getenv("CLIENT_ID")
        CLIENT_SECRET = os.getenv("CLIENT_SECRET")

        # Endpointy Allegro API
        AUTH_URL = "https://allegro.pl/auth/oauth/token"
        SEARCH_URL = "https://api.allegro.pl/offers/listing"
        PRODUCTS_URL = "https://api.allegro.pl/sale/products"
        file_token_path = "./token.txt"

        if os.path.exists(file_token_path) == False:
            file_token = open(f"{file_token_path}", "w")
            file_token.close()
            token = ""
        else:
            with open(f"{file_token_path}", "r") as file_token:
                token = file_token.readline()

        #Użycie bloku try z powodu przewidzianego błędu nieaktualnego tokenu
        #("requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url:")
        try:
            pack_data_allegro_products = get_and_process_products_data(phrase, token)
        except requests.exceptions.HTTPError as http_err:
            # Obsługa specyficznych kodów HTTP
            if http_err.response.status_code == 401:
                print("Błąd 401: Token nieaktualny lub nieprawidłowy. Odświeżam token...")
                token = get_access_token(CLIENT_ID, CLIENT_SECRET)
                return get_and_process_products_data(phrase, token)
            elif http_err.response.status_code == 403:
                print("Błąd 403: Brak uprawnień do zasobu. Sprawdź token i endpoint.")
                raise
            elif http_err.response.status_code == 429:
                retry_after = int(http_err.response.headers.get('Retry-After', 1))
                print(f"Błąd 429: Przekroczono limit żądań. Spróbuję ponownie za {retry_after} sekund.")
                time.sleep(retry_after)
                return get_and_process_products_data(phrase, token)
            elif 500 <= http_err.response.status_code < 600:
                print(
                    f"Błąd serwera ({http_err.response.status_code}): Problem po stronie Allegro. Spróbuję ponownie...")
                time.sleep(2)  # Czekanie przed ponownym zapytaniem
                return get_and_process_products_data(phrase, token)
            else:
                print(f"HTTPError: Wystąpił nieoczekiwany błąd HTTP ({http_err.response.status_code}): {http_err}")
                raise
        return pack_data_allegro_products
    try:
        pack_data_allegro_products = data_download_and_preparation()
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            flash("Przepraszamy. Napotkaliśmy na problem po stronie serwera Allegro")
            #raise Exception("Błąd 401: Token nieaktualny lub nieprawidłowy.")
            return redirect(url_for('search_form_display'))
        elif http_err.response.status_code == 429:
            retry_after = int(http_err.response.headers.get('Retry-After', 1))
            print(f"Przekroczono limit żądań. Czekanie {retry_after} sekund...")
            time.sleep(retry_after)
        elif 500 <= http_err.response.status_code < 600:
            print(f"Błąd serwera ({http_err.response.status_code}). Ponawianie...")
        else:
            print(f"HTTPError: {http_err}")
            raise
    except requests.exceptions.ConnectionError:
        print("Błąd połączenia. Sprawdzam połączenie i ponawiam...")
        time.sleep(DELAY)
    except requests.exceptions.Timeout:
        print("Przekroczono limit czasu oczekiwania. Ponawianie...")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")
        raise
    return render_template('results.html', data=pack_data_allegro_products)