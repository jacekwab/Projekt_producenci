import requests
from dotenv import load_dotenv
import os
import time
from flask import render_template,request

# stała delay wskazuje ile sekund jest przerwy między kolejnymi połączeniami
DELAY = 0
# stała max_products wskazuje ile produktów chcemy pokazać w wynikach
# 2024-12-16 20:48:56 do stałej max_products musi zostać przypisana wartość wielokrotności 30
# inaczej rzeczywista liczba wyników przekroczy wartość max_products
MAX_PRODUCTS = 210


def data_display():
    if request.method == "GET":
        #ładuje formularz do wpisania hasła
        return render_template('main.html')
    else:
        if 'phrase' in request.form:
            # pobiera hasło z formularza
            phrase=request.form['phrase']
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
                    next_page_id = data['nextPage']['id']
                    products = data.get('products', [])
                    all_products.extend(products)

                    number_products += len(products)

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

            #phrase = "rower"  # Przykładowa fraza wyszukiwania

            #Użycie bloku try z powodu przewidzianego błędu nieaktualnego tokenu
            #("requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url:")
            try:
                pack_data_allegro_products = get_and_process_products_data(phrase, token)
            except:
                token = get_access_token(CLIENT_ID,
                                         CLIENT_SECRET)  # Uzyskany token działa przez 0,5 h. Unikajmy odnawiania
                pack_data_allegro_products = get_and_process_products_data(phrase, token)

            return pack_data_allegro_products


        pack_data_allegro_products = data_download_and_preparation()

        return render_template('results.html', data = pack_data_allegro_products)