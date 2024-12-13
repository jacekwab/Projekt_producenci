import requests
from dotenv import load_dotenv
import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def data_display():


    def data_downloading_and_formatting():


        def get_and_format_products(phrase, token):
            PRODUCTS_URL = "https://api.allegro.pl/sale/products"
            
            # Parametry zapytania i nagłówki
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.allegro.public.v1+json',
            }
            params = {
                'phrase': phrase,
            }

            # Pobieranie produktów
            response = requests.get(PRODUCTS_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Przetwarzanie wyników
            products = data.get('products', [])

            # Wyświetlenie wyników
            formatted_data = f"Liczba produktów dla frazy '{phrase}': {len(products)}"
            for product in products:

                formatted_data = formatted_data + "<br>" + f"Produkt ID: {product.get('id', 'Brak danych')}"
                formatted_data = formatted_data + "<br>" + f"Nazwa: {product.get('name', 'Brak nazwy')}"

                # Pobieramy nazwę producenta, jeśli jest dostępna
                try:
                    brand = product['parameters'][0]['valuesLabels'][0]
                    formatted_data = formatted_data + "<br>" + f"Marka: {brand}"
                except:
                    formatted_data = formatted_data + "<br>" + "Producent: Brak danych"

                # Pobieramy inne szczegóły, takie jak EAN, jeśli są dostępne
                formatted_data = formatted_data + "<br>" + f"EAN: {product.get('ean', 'Brak danych')}"
                # Nowa linia + separator dla czytelności
                formatted_data = formatted_data + "<br>" + "-" * 40

            formatted_data = f"<p>{formatted_data}</p>"

            return formatted_data



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



        # Jeżeli plik token.txt istnieje. Pobiera się token z pliku.
        if os.path.exists(file_token_path) == False:
            file_token = open(f"{file_token_path}", "w")
            file_token.close()
            token = ""
        else:
            with open(f"{file_token_path}", "r") as file_token:
                token = file_token.readline()

        # Użycie funkcji (podaj poprawne client_id i client_secret dla środowiska produkcyjnego)
        phrase = "rower"  # Przykładowa fraza wyszukiwania

        #Użycie bloku try z powodu przewidzianego błędu nieaktualnego tokenu
        #("requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url:")
        try:
            formatted_data = get_and_format_products(phrase, token)
        except:
            token = get_access_token(CLIENT_ID,
                                     CLIENT_SECRET)  # Uzyskaj token działa przez 0,5 h. Nie powinno się go co chwila odnawiać
            formatted_data = get_and_format_products(phrase, token)

        return formatted_data




    formatted_data = data_downloading_and_formatting()

    return formatted_data