# api_handler.py
# Pobieranie danych z API
import requests
import time

# Prosty cache, aby unikać wielokrotnego pobierania listy monet
COIN_LIST_CACHE = None
CACHE_TIMESTAMP = 0
CACHE_DURATION = 3600  # 1 godzina w sekundach

def get_symbol_id_map():
    """
    Pobiera listę wszystkich monet z CoinGecko i tworzy mapowanie symbol -> id.
    Wynik jest cachowany, aby unikać zbędnych zapytań.
    """
    global COIN_LIST_CACHE, CACHE_TIMESTAMP
    current_time = time.time()

    if COIN_LIST_CACHE and (current_time - CACHE_TIMESTAMP < CACHE_DURATION):
        return COIN_LIST_CACHE

    print("Pobieranie nowej listy monet z CoinGecko...")
    try:
        response = requests.get("https://api.coingecko.com/api/v3/coins/list")
        response.raise_for_status()
        coins = response.json()

        # Tworzymy mapowanie: symbol (małymi literami) -> id
        # Np. {'btc': 'bitcoin', 'eth': 'ethereum'}
        symbol_map = {coin['symbol'].lower(): coin['id'] for coin in coins}

        COIN_LIST_CACHE = symbol_map
        CACHE_TIMESTAMP = current_time
        print("Pobrano i zcachowano listę monet.")
        return COIN_LIST_CACHE
    except requests.RequestException as e:
        print(f"Błąd podczas pobierania listy monet: {e}")
        return None

def get_crypto_prices(symbols):
    """
    Pobiera aktualne ceny dla listy symboli kryptowalut.
    """
    if not symbols:
        return {}

    symbol_map = get_symbol_id_map()
    if not symbol_map:
        return {}

    # Konwertujemy symbole (np. 'BTC') na ID (np. 'bitcoin')
    ids_to_fetch = []
    for symbol in symbols:
        coin_id = symbol_map.get(symbol.lower())
        if coin_id:
            ids_to_fetch.append(coin_id)
        else:
            print(f"Ostrzeżenie: Nie znaleziono ID dla symbolu '{symbol}'")

    if not ids_to_fetch:
        return {}

    ids_string = ",".join(ids_to_fetch)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd"

    try:
        print(f"Pobieranie cen dla: {ids_string}")
        response = requests.get(url)
        response.raise_for_status()
        prices_data = response.json()

        # Przetwarzamy odpowiedź, aby zmapować cenę z powrotem do oryginalnego symbolu
        # API zwraca {'bitcoin': {'usd': 50000}}, my chcemy {'BTC': 50000}
        result = {}
        # Musimy stworzyć odwróconą mapę id -> symbol
        id_to_symbol_map = {v: k.upper() for k, v in symbol_map.items()}

        for coin_id, price_info in prices_data.items():
            if 'usd' in price_info:
                symbol = id_to_symbol_map.get(coin_id)
                if symbol:
                    result[symbol] = price_info['usd']
        return result
    except requests.RequestException as e:
        print(f"Błąd podczas pobierania cen: {e}")
        return {}

if __name__ == '__main__':
    # Testowanie funkcji
    print("--- Testowanie API Handlera ---")
    test_symbols = ['BTC', 'ETH', 'nonexistent']
    prices = get_crypto_prices(test_symbols)

    if prices:
        print("\nOtrzymane ceny (USD):")
        for symbol, price in prices.items():
            print(f"{symbol}: {price}")
    else:
        print("\nNie udało się pobrać cen.")