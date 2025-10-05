# instruments.py
# Predefiniowane listy popularnych instrumentów finansowych

# Popularne akcje (znacznie rozszerzona lista)
STOCKS = {
    'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corporation', 'GOOGL': 'Alphabet Inc. (Class A)', 'GOOG': 'Alphabet Inc. (Class C)',
    'AMZN': 'Amazon.com, Inc.', 'NVDA': 'NVIDIA Corporation', 'TSLA': 'Tesla, Inc.', 'META': 'Meta Platforms, Inc.',
    'BRK-B': 'Berkshire Hathaway Inc.', 'JPM': 'JPMorgan Chase & Co.', 'V': 'Visa Inc.', 'JNJ': 'Johnson & Johnson',
    'WMT': 'Walmart Inc.', 'PG': 'Procter & Gamble Co.', 'MA': 'Mastercard Incorporated', 'UNH': 'UnitedHealth Group Inc.',
    'HD': 'The Home Depot, Inc.', 'BAC': 'Bank of America Corp', 'DIS': 'The Walt Disney Company', 'PFE': 'Pfizer Inc.',
    'XOM': 'Exxon Mobil Corporation', 'KO': 'The Coca-Cola Company', 'PEP': 'PepsiCo, Inc.', 'CSCO': 'Cisco Systems, Inc.',
    'INTC': 'Intel Corporation', 'ADBE': 'Adobe Inc.', 'NFLX': 'Netflix, Inc.', 'CRM': 'Salesforce, Inc.',
    'MCD': "McDonald's Corporation", 'NKE': 'NIKE, Inc.', 'PYPL': 'PayPal Holdings, Inc.', 'T': 'AT&T Inc.',
    'ORCL': 'Oracle Corporation', 'IBM': 'IBM', 'SBUX': 'Starbucks Corporation', 'UBER': 'Uber Technologies, Inc.'
}

# Główne i drugorzędne pary walutowe
CURRENCIES = {
    'EURUSD': 'EUR/USD', 'USDJPY': 'USD/JPY', 'GBPUSD': 'GBP/USD', 'USDCHF': 'USD/CHF',
    'AUDUSD': 'AUD/USD', 'USDCAD': 'USD/CAD', 'NZDUSD': 'NZD/USD', 'EURJPY': 'EUR/JPY',
    'GBPJPY': 'GBP/JPY', 'EURGBP': 'EUR/GBP', 'AUDJPY': 'AUD/JPY', 'CHFJPY': 'CHF/JPY',
    'EURPLN': 'EUR/PLN', 'USDPLN': 'USD/PLN', 'CHFPLN': 'CHF/PLN', 'GBPPLN': 'GBP/PLN',
    'EURNOK': 'EUR/NOK', 'USDNOK': 'USD/NOK', 'EURSEK': 'EUR/SEK', 'USDSEK': 'USD/SEK'
}

def get_predefined_stocks():
    """Zwraca słownik akcji w formacie {symbol: nazwa}."""
    return STOCKS

def get_predefined_currencies():
    """Zwraca słownik walut w formacie {symbol: nazwa}."""
    return CURRENCIES