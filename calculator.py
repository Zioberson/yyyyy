# calculator.py
# Obliczenia finansowe
import pandas as pd

def calculate_portfolio_summary(transactions, prices):
    """
    Oblicza podsumowanie portfela: całkowita wartość, zysk/strata, alokacja.

    Args:
        transactions (list): Lista transakcji z bazy danych w formacie (id, symbol, asset_type, ...).
        prices (dict): Słownik z aktualnymi cenami {'SYMBOL': price}.

    Returns:
        dict: Słownik zawierający kompleksowe podsumowanie portfela.
    """
    if not transactions:
        return {
            'total_value': 0.0,
            'total_cost': 0.0,
            'unrealized_pnl_amount': 0.0,
            'unrealized_pnl_percent': 0.0,
            'holdings': {},
            'allocation_by_asset': {},
            'allocation_by_type': {}
        }

    # Konwersja na DataFrame dla łatwiejszych obliczeń
    df = pd.DataFrame(transactions, columns=['id', 'symbol', 'asset_type', 'transaction_type', 'quantity', 'price_per_unit', 'date'])
    df['cost'] = df['quantity'] * df['price_per_unit']

    holdings = {}
    for symbol, group in df.groupby('symbol'):
        buys = group[group['transaction_type'] == 'buy']
        sells = group[group['transaction_type'] == 'sell']

        total_quantity_bought = buys['quantity'].sum()
        total_cost_of_buys = buys['cost'].sum()
        total_quantity_sold = sells['quantity'].sum()

        current_quantity = total_quantity_bought - total_quantity_sold

        if current_quantity > 0.000001: # Unikanie problemów z precyzją float
            # Średnia cena zakupu dla posiadanych aktywów
            avg_buy_price = total_cost_of_buys / total_quantity_bought if total_quantity_bought > 0 else 0
            cost_basis = current_quantity * avg_buy_price

            # Pobieranie aktualnej ceny
            current_price = prices.get(symbol, 0)
            # Wartość rynkowa tylko dla aktywów z aktualną ceną
            market_value = current_quantity * current_price if current_price else 0.0

            holdings[symbol] = {
                'quantity': current_quantity,
                'cost_basis': cost_basis,
                'market_value': market_value,
                'asset_type': group['asset_type'].iloc[0]
            }

    # Obliczanie sumarycznych wartości
    total_value = sum(h['market_value'] for h in holdings.values() if h['market_value'] > 0)
    total_cost = sum(h['cost_basis'] for h in holdings.values())

    unrealized_pnl_amount = total_value - total_cost if total_value > 0 else 0.0
    unrealized_pnl_percent = (unrealized_pnl_amount / total_cost * 100) if total_cost > 0 else 0.0

    # Obliczanie alokacji procentowej (dla aktywów i typów aktywów)
    allocation_by_asset = {}
    allocation_by_type = {}
    if total_value > 0:
        # Alokacja wg aktywów
        for symbol, data in holdings.items():
            if data['market_value'] > 0:
                allocation_by_asset[symbol] = (data['market_value'] / total_value) * 100

        # Alokacja wg typu
        type_values = {}
        for symbol, data in holdings.items():
            if data['market_value'] > 0:
                asset_type = data['asset_type']
                type_values[asset_type] = type_values.get(asset_type, 0) + data['market_value']

        for asset_type, value in type_values.items():
            allocation_by_type[asset_type] = (value / total_value) * 100

    return {
        'total_value': total_value,
        'total_cost': total_cost,
        'unrealized_pnl_amount': unrealized_pnl_amount,
        'unrealized_pnl_percent': unrealized_pnl_percent,
        'holdings': holdings,
        'allocation_by_asset': allocation_by_asset,
        'allocation_by_type': allocation_by_type
    }