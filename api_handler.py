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
        response = requests.get("https://api.coingecko.com/api/v3/coins/list")
        response.raise_for_status()
        COIN_LIST_CACHE = {coin['symbol'].lower(): coin['id'] for coin in response.json()}
        CACHE_TIMESTAMP = time.time()
        return COIN_LIST_CACHE
    except requests.RequestException:
        return None

def get_crypto_prices_usd(symbols):
    if not symbols: return {}
    symbol_map = get_coingecko_symbol_map()
    if not symbol_map: return {}
    ids = [symbol_map[s.lower()] for s in symbols if s.lower() in symbol_map]
    if not ids: return {}
    try:
        response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ids)}&vs_currencies=usd")
        prices = response.json()
        id_map = {v: k.upper() for k, v in symbol_map.items()}
        return {id_map[id]: data['usd'] for id, data in prices.items()}
    except requests.RequestException:
        return {}

# --- API dla Akcji i Walut (Yahoo Finance) ---

def get_yahoo_prices_usd(symbols):
    if not symbols: return {}
    formatted_map = {(f"{s.upper()}=X" if len(s) == 6 and s.isalpha() else s.upper()): s for s in symbols}
    try:
        data = yf.download(tickers=list(formatted_map.keys()), period="1d", progress=False)
        if data.empty: return {}
        last_prices = data['Close'].iloc[-1]
        return {formatted_map[k]: v for k, v in last_prices.items() if not pd.isna(v)}
    except Exception:
        return {}

# --- Główny Handler ---

def get_prices_for_transactions(transactions, base_currency="USD"):
    if not transactions: return {}

    # 1. Rozdziel symbole według typu
    asset_types = {'kryptowaluta': set(), 'akcja': set(), 'waluta': set()}
    for t in transactions:
        if t[2] in asset_types:
            asset_types[t[2]].add(t[1])

    # 2. Pobierz wszystkie ceny w USD
    prices_in_usd = {}
    if asset_types['kryptowaluta']:
        prices_in_usd.update(get_crypto_prices_usd(list(asset_types['kryptowaluta'])))

    yahoo_symbols = list(asset_types['akcja']) + list(asset_types['waluta'])
    if yahoo_symbols:
        prices_in_usd.update(get_yahoo_prices_usd(yahoo_symbols))

    # 3. Jeśli waluta bazowa to USD, zwróć ceny
    if base_currency == "USD":
        return prices_in_usd

    # 4. Jeśli inna waluta, pobierz kurs wymiany USD -> Twoja Waluta
    exchange_rate_symbol = f"USD{base_currency.upper()}=X"
    try:
        rate_data = yf.download(exchange_rate_symbol, period="1d", progress=False)
        exchange_rate = rate_data['Close'].iloc[-1] if not rate_data.empty else None

        if not exchange_rate or pd.isna(exchange_rate):
            print(f"Ostrzeżenie: Nie udało się pobrać kursu wymiany dla {base_currency}")
            return prices_in_usd # Zwróć USD jako fallback

        # 5. Przelicz wszystkie ceny
        prices_in_base_currency = {symbol: price * exchange_rate for symbol, price in prices_in_usd.items()}
        return prices_in_base_currency
    except Exception:
        print(f"Błąd podczas pobierania kursu wymiany dla {base_currency}")
        return prices_in_usd

if __name__ == '__main__':
    test_transactions = [
        (1, 'BTC', 'kryptowaluta', 'buy', 1, 0, ''), (2, 'AAPL', 'akcja', 'buy', 5, 0, ''),
        (3, 'EURPLN', 'waluta', 'buy', 100, 0, ''),
    ]
    for currency in ["USD", "EUR", "PLN"]:
        print(f"\n--- Testowanie dla waluty bazowej: {currency} ---")
        final_prices = get_prices_for_transactions(test_transactions, currency)
        if final_prices:
            for symbol, price in final_prices.items():
                print(f"{symbol}: {price:.2f} {currency}")
        else:
            print("Nie udało się pobrać cen.")