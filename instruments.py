# instruments.py
# Predefiniowane listy popularnych instrumentów finansowych

# Popularne akcje (przykładowa lista, można ją rozbudować)
STOCKS = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOG': 'Alphabet Inc.',
    'AMZN': 'Amazon.com, Inc.',
    'NVDA': 'NVIDIA Corporation',
    'TSLA': 'Tesla, Inc.',
    'META': 'Meta Platforms, Inc.',
    'JPM': 'JPMorgan Chase & Co.',
    'V': 'Visa Inc.',
    'WMT': 'Walmart Inc.',
}

# Główne pary walutowe (w formacie Yahoo Finance)
CURRENCIES = {
    'EURUSD': 'EUR/USD',
    'USDJPY': 'USD/JPY',
    'GBPUSD': 'GBP/USD',
    'USDCHF': 'USD/CHF',
    'AUDUSD': 'AUD/USD',
    'USDCAD': 'USD/CAD',
    'EURPLN': 'EUR/PLN',
    'USDPLN': 'USD/PLN',
}

def get_predefined_stocks():
    """Zwraca słownik akcji w formacie {symbol: nazwa}."""
    return STOCKS

def get_predefined_currencies():
    """Zwraca słownik walut w formacie {symbol: nazwa}."""
    return CURRENCIES