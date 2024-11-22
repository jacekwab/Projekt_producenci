import requests
from dotenv import load_dotenv
import os

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


#Sandbox:
# AUTH_URL = "https://allegro.pl.allegrosandbox.pl/auth/oauth/token"
# SEARCH_URL = "https://api.allegro.pl.allegrosandbox.pl/offers/listing"


def get_access_token(client_id, client_secret):
    global token
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
    print(token)
    with open(f"{file_token_path}", "w") as file_token:
        file_token.write(token)
    return token


# Jeżeli plik token.txt istnieje. Pobiera się token z pliku.
if os.path.exists(file_token_path) == False:
    file_token = open(f"{file_token_path}", "w")
    file_token.close()
    token = ""
else:
    with open(f"{file_token_path}", "r") as file_token:
        token = file_token.readline()


def get_products(phrase, CLIENT_ID, CLIENT_SECRET):
    PRODUCTS_URL = "https://api.allegro.pl/sale/products"
    # Parametry zapytania i nagłówki
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
    }
    params = {
        'phrase': phrase,
        'limit': 100  # Liczba produktów na stronę
    }

    # Pobieranie produktów
    response = requests.get(PRODUCTS_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    # Przetwarzanie wyników
    products = data.get('products', [])

    # Wyświetlenie wyników
    print(f"Liczba produktów dla frazy '{phrase}':", len(products))
    for product in products:

        print("Produkt ID:", product.get('id', 'Brak danych'))
        print("Nazwa:", product.get('name', 'Brak nazwy'))

        # Pobieramy nazwę producenta, jeśli jest dostępna
        try:
            brand = product['parameters'][0]['valuesLabels'][0]
            print(f"Marka: {brand}")
        except:
            #if brand:
            #print("Producent:", brand.get('name', 'Brak danych'))
            #else:
            print("Producent: Brak danych")

        # Pobieramy inne szczegóły, takie jak EAN, jeśli są dostępne
        print("EAN:", product.get('ean', 'Brak danych'))
        print("Kategoria:", product.get('category', {}).get('name', 'Brak danych'))

        # Separator dla czytelności
        print("-" * 40)


# Użycie funkcji (podaj poprawne client_id i client_secret dla środowiska produkcyjnego)
phrase = "rower"  # Przykładowa fraza wyszukiwania
try:
    get_products(phrase, CLIENT_ID, CLIENT_SECRET)
except:
    token = get_access_token(CLIENT_ID,
                             CLIENT_SECRET)  # Uzyskaj token działa przez 0,5 h. Nie powinno się go co chwila odnawiać
    get_products(phrase, CLIENT_ID, CLIENT_SECRET)
