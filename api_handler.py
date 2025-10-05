# api_handler.py
# Pobieranie danych z zewnętrznych API
import requests
import time
import yfinance as yf
import pandas as pd

# --- API dla Kryptowalut (CoinGecko) ---

COIN_LIST_CACHE = None
CACHE_TIMESTAMP = 0
CACHE_DURATION = 3600  # 1 godzina

def get_coingecko_symbol_map():
    global COIN_LIST_CACHE, CACHE_TIMESTAMP
    if COIN_LIST_CACHE and (time.time() - CACHE_TIMESTAMP < CACHE_DURATION):
        return COIN_LIST_CACHE
    try:
        print("Pobieranie listy 1000 najpopularniejszych kryptowalut z CoinGecko...")
        all_coins = []
        for page in range(1, 5):
            url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page={page}"
            response = requests.get(url)
            response.raise_for_status()
            all_coins.extend(response.json())
        COIN_LIST_CACHE = {coin['symbol'].lower(): (coin['id'], coin['name']) for coin in all_coins}
        CACHE_TIMESTAMP = time.time()
        return COIN_LIST_CACHE
    except requests.RequestException as e:
        print(f"Błąd CoinGecko API: {e}")
        return None

def get_crypto_prices_usd(symbols):
    if not symbols: return {}
    symbol_map = get_coingecko_symbol_map()
    if not symbol_map: return {}
    ids_to_fetch = [symbol_map[s.lower()][0] for s in symbols if s.lower() in symbol_map]
    if not ids_to_fetch: return {}
    try:
        response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ids_to_fetch)}&vs_currencies=usd")
        response.raise_for_status()
        prices_data = response.json()
        id_to_symbol_map = {v[0]: k.upper() for k, v in symbol_map.items()}
        return {id_to_symbol_map[id]: data['usd'] for id, data in prices_data.items() if id in id_to_symbol_map}
    except requests.RequestException:
        return {}

# --- API dla Akcji i Walut (Yahoo Finance) ---

def get_yahoo_prices_usd(symbols):
    if not symbols: return {}
    formatted_map = {(f"{s.upper()}=X" if len(s) == 6 and s.isalpha() else s.upper()): s for s in symbols}
    try:
        data = yf.download(tickers=list(formatted_map.keys()), period="1d", progress=False, auto_adjust=True)
        if data.empty: return {}
        last_prices = data['Close'].iloc[-1]
        return {formatted_map[k]: v for k, v in last_prices.items() if not pd.isna(v)}
    except Exception as e:
        print(f"Błąd Yahoo Finance API: {e}")
        return {}

def get_exchange_rate(from_currency, to_currency):
    if from_currency == to_currency: return 1.0
    try:
        symbol = f"{from_currency}{to_currency}=X"
        ticker = yf.Ticker(symbol)
        rate = ticker.info.get('regularMarketPrice')
        if rate: return rate
        hist = ticker.history(period="2d")
        if not hist.empty: return hist['Close'].iloc[-1]
        return None
    except Exception:
        return None

# --- Główny Handler ---

def get_prices_for_transactions(transactions, base_currency="USD"):
    if not transactions: return {}
    asset_types = {'kryptowaluta': set(), 'akcja': set(), 'waluta': set()}
    for t in transactions:
        if t[2] in asset_types: asset_types[t[2]].add(t[1])

    prices_in_usd = {}
    if asset_types['kryptowaluta']: prices_in_usd.update(get_crypto_prices_usd(list(asset_types['kryptowaluta'])))
    yahoo_symbols = list(asset_types['akcja']) + list(asset_types['waluta'])
    if yahoo_symbols: prices_in_usd.update(get_yahoo_prices_usd(yahoo_symbols))

    if base_currency == "USD": return prices_in_usd

    exchange_rate = get_exchange_rate("USD", base_currency)
    if not exchange_rate: return prices_in_usd

    return {symbol: price * exchange_rate for symbol, price in prices_in_usd.items()}

# --- Funkcje do pobierania danych rynkowych (NOWA, POPRAWIONA WERSJA) ---

def get_crypto_market_data(limit=100):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={limit}&page=1"
        response = requests.get(url)
        response.raise_for_status()
        return [{'name': c.get('name'), 'symbol': c.get('symbol', '').upper(), 'price': c.get('current_price'), 'change_24h': c.get('price_change_percentage_24h'), 'market_cap': c.get('market_cap')} for c in response.json()]
    except requests.RequestException:
        return []

def get_yahoo_market_data(symbols):
    if not symbols: return []
    market_data = []
    formatted_symbols = [f"{s.upper()}=X" if len(s) == 6 and s.isalpha() else s.upper() for s in symbols]

    try:
        data = yf.download(tickers=formatted_symbols, period="2d", progress=False, auto_adjust=True)
        if data.empty: return []

        for symbol in formatted_symbols:
            hist = data['Close'][symbol] if len(formatted_symbols) > 1 else data['Close']
            if hist.isnull().all() or len(hist) < 2: continue

            last_price = hist.iloc[-1]
            prev_price = hist.iloc[-2]
            change = ((last_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0

            # Pobieranie dodatkowych informacji, jeśli to możliwe
            # Dla walut, nazwa to po prostu symbol
            name = symbol.replace('=X', '')
            market_cap = None
            if "=X" not in symbol: # To prawdopodobnie akcja
                try:
                    info = yf.Ticker(symbol).info
                    name = info.get('shortName', name)
                    market_cap = info.get('marketCap')
                except Exception:
                    pass # Ignorujemy błędy pobierania info, mamy już cenę

            market_data.append({'name': name, 'symbol': symbol.replace('=X', ''), 'price': last_price, 'change_24h': change, 'market_cap': market_cap})
    except Exception as e:
        print(f"Błąd podczas pobierania danych rynkowych z Yahoo: {e}")

    return market_data

if __name__ == '__main__':
    print("--- Testowanie Danych Rynkowych ---")
    crypto = get_crypto_market_data(5)
    print("\nKryptowaluty:", crypto)
    stocks = get_yahoo_market_data(['AAPL', 'MSFT'])
    print("\nAkcje:", stocks)
    currencies = get_yahoo_market_data(['EURUSD', 'GBPPLN'])
    print("\nWaluty:", currencies)
    assert crypto and stocks and currencies, "Test zakończony niepowodzeniem!"
    print("\n--- Wszystkie testy zakończone pomyślnie! ---")