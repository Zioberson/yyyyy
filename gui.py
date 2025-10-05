# gui.py
# Interfejs użytkownika
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from datetime import datetime
import database
import api_handler
import calculator
import sv_ttk
import numpy as np
import matplotlib.pyplot as plt
import instruments

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Strony Aplikacji ---

class MainPage(ttk.Frame):
    """Strona główna z nowym, zaawansowanym dashboardem opartym na zakładkach."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        summary_frame = ttk.LabelFrame(self, text="Podsumowanie Całego Portfela", padding="10")
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        self.total_value_label = ttk.Label(summary_frame, text="Całkowita wartość: $0.00", font=("Helvetica", 14, "bold"))
        self.total_value_label.pack(anchor=tk.W)
        self.pnl_label = ttk.Label(summary_frame, text="Z/S (Niezrealiz.): $0.00 (0.00%)")
        self.pnl_label.pack(anchor=tk.W)
        self.realized_pnl_label = ttk.Label(summary_frame, text="Z/S (Zrealiz.): $0.00")
        self.realized_pnl_label.pack(anchor=tk.W)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.asset_tabs = {}
        for asset_type in ['kryptowaluta', 'akcja', 'waluta']:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=asset_type.capitalize())
            cols = ('Symbol', 'Ilość', 'Wartość', 'Koszt', 'Z/S Niezrealiz.')
            tree = ttk.Treeview(tab, columns=cols, show='headings')
            for col in cols: tree.heading(col, text=col)
            tree.column('Wartość', anchor=tk.E); tree.column('Koszt', anchor=tk.E); tree.column('Z/S Niezrealiz.', anchor=tk.E)
            tree.pack(fill=tk.BOTH, expand=True)
            self.asset_tabs[asset_type] = tree

    def refresh(self, summary, currency_symbol):
        self.total_value_label.config(text=f"Całkowita wartość: {currency_symbol}{summary['total_value']:.2f}")
        unrealized_pnl = summary['unrealized_pnl_amount']
        unrealized_pnl_percent = summary['unrealized_pnl_percent']
        self.pnl_label.config(text=f"Z/S (Niezrealiz.): {currency_symbol}{unrealized_pnl:.2f} ({unrealized_pnl_percent:.2f}%)", foreground="green" if unrealized_pnl >= 0 else "red")
        realized_pnl = summary['total_realized_pnl']
        self.realized_pnl_label.config(text=f"Z/S (Zrealiz.): {currency_symbol}{realized_pnl:.2f}", foreground="green" if realized_pnl >= 0 else "red")
        for asset_type, tree in self.asset_tabs.items():
            for item in tree.get_children(): tree.delete(item)
            for symbol, data in summary['holdings'].items():
                if data['asset_type'] == asset_type:
                    pnl = data['market_value'] - data['cost_basis'] if data['market_value'] > 0 else 0.0
                    values = (symbol, f"{data['quantity']:.6f}", f"{currency_symbol}{data['market_value']:.2f}", f"{currency_symbol}{data['cost_basis']:.2f}", f"{currency_symbol}{pnl:.2f}")
                    tree.insert('', tk.END, values=values, tags=("green" if pnl >= 0 else "red",))
            tree.tag_configure("green", foreground="green"); tree.tag_configure("red", foreground="red")

class AddTransactionPage(ttk.Frame):
    """Strona do dodawania nowych transakcji z kaskadowym wyborem."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        form_frame = ttk.LabelFrame(self, text="Dodaj nową transakcję", padding="10")
        form_frame.pack(fill=tk.X, pady=10, padx=10)

        self.asset_type_var = tk.StringVar()
        ttk.Label(form_frame, text="1. Typ Aktywa:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.asset_type_combobox = ttk.Combobox(form_frame, textvariable=self.asset_type_var, values=['Kryptowaluta', 'Akcja', 'Waluta'], state="readonly")
        self.asset_type_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.asset_type_combobox.bind("<<ComboboxSelected>>", self.on_asset_type_select)

        self.name_var = tk.StringVar()
        ttk.Label(form_frame, text="2. Wyszukaj Nazwę:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var, state="disabled")
        self.name_entry.grid(row=1, column=1, padx=5, pady=5)
        self.name_entry.bind('<KeyRelease>', self.filter_symbols)

        self.symbol_var = tk.StringVar()
        ttk.Label(form_frame, text="3. Wybierz Symbol:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.symbol_combobox = ttk.Combobox(form_frame, textvariable=self.symbol_var, state="disabled")
        self.symbol_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.symbol_combobox.bind('<<ComboboxSelected>>', self.on_symbol_select)

        self.transaction_type_var = tk.StringVar(value='Buy')
        ttk.Label(form_frame, text="4. Typ Transakcji:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Combobox(form_frame, textvariable=self.transaction_type_var, values=['Buy', 'Sell'], state="readonly").grid(row=3, column=1, padx=5, pady=5)

        self.quantity_var = tk.DoubleVar()
        ttk.Label(form_frame, text="Ilość:").grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(form_frame, textvariable=self.quantity_var).grid(row=3, column=3, padx=5, pady=5)

        self.price_var = tk.DoubleVar()
        ttk.Label(form_frame, text="Cena za jedn.:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(form_frame, textvariable=self.price_var).grid(row=4, column=1, padx=5, pady=5)
        self.current_price_label = ttk.Label(form_frame, text="Aktualna cena: -")
        self.current_price_label.grid(row=4, column=2, columnspan=2, padx=5, pady=5, sticky=tk.W)

        add_button = ttk.Button(form_frame, text="Dodaj transakcję", command=self.add_new_transaction)
        add_button.grid(row=5, column=3, padx=5, pady=10, sticky=tk.E)

    def on_asset_type_select(self, event=None):
        self.name_entry.config(state="normal")
        self.symbol_combobox.config(state="readonly")
        self.filter_symbols()

    def filter_symbols(self, event=None):
        asset_type = self.asset_type_var.get().lower()
        search_term = self.name_var.get().lower()
        if not asset_type: return
        full_list = self.controller.instruments_by_type.get(asset_type, [])
        if not search_term:
            self.symbol_combobox['values'] = [item[0] for item in full_list]
        else:
            filtered_list = [item[0] for item in full_list if search_term in item[1].lower()]
            self.symbol_combobox['values'] = filtered_list
        self.symbol_var.set(""); self.current_price_label.config(text="Aktualna cena: -")

    def on_symbol_select(self, event=None):
        symbol, asset_type = self.symbol_var.get(), self.asset_type_var.get().lower()
        if not symbol or not asset_type: return
        full_list = self.controller.instruments_by_type.get(asset_type, [])
        for item_symbol, item_name in full_list:
            if item_symbol == symbol: self.name_var.set(item_name); break
        price_data = api_handler.get_prices_for_transactions([('', symbol, asset_type)], self.controller.base_currency.get())
        price = price_data.get(symbol)
        if price: self.current_price_label.config(text=f"Aktualna cena: {price:.4f} {self.controller.base_currency.get()}")
        else: self.current_price_label.config(text="Aktualna cena: Błąd")

    def add_new_transaction(self):
        symbol, asset_type = self.symbol_var.get().upper(), self.asset_type_var.get().lower()
        trans_type, quantity, price = self.transaction_type_var.get().lower(), self.quantity_var.get(), self.price_var.get()
        if not all([symbol, asset_type, trans_type, quantity > 0, price > 0]):
            messagebox.showerror("Błąd", "Wszystkie pola muszą być poprawnie wypełnione.")
            return
        name_to_db = self.name_var.get() if self.name_var.get() else symbol
        try:
            database.add_transaction(symbol, name_to_db, asset_type, trans_type, quantity, price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.controller.show_toast("Transakcja dodana pomyślnie!")
            self.clear_form()
            self.controller.refresh_all_data()
        except Exception as e:
            messagebox.showerror("Błąd bazy danych", f"Wystąpił błąd: {e}")

    def clear_form(self):
        self.asset_type_var.set(""); self.name_var.set(""); self.name_entry.config(state="disabled")
        self.symbol_var.set(""); self.symbol_combobox.config(state="disabled")
        self.quantity_var.set(0.0); self.price_var.set(0.0)
        self.current_price_label.config(text="Aktualna cena: -")

class ChartsPage(ttk.Frame):
    """Strona z wykresem alokacji."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        chart_frame = ttk.LabelFrame(self, text="Alokacja aktywów", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chart_filter_var = tk.StringVar(value="wg aktywów")
        ttk.Combobox(chart_frame, textvariable=self.chart_filter_var, values=["wg aktywów", "wg typu"], state="readonly").pack(pady=(0, 10), fill=tk.X)
        self.chart_filter_var.trace_add("write", lambda *_: self.controller.refresh_all_data())
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.fig.subplots_adjust(right=0.7)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def refresh(self, summary):
        mode = self.chart_filter_var.get()
        data = summary['allocation_by_asset'] if mode == "wg aktywów" else summary['allocation_by_type']
        title = "Alokacja wg Aktywów" if mode == "wg aktywów" else "Alokacja wg Typu"
        self.update_pie_chart(data, title)

    def update_pie_chart(self, data, title):
        self.ax.clear()
        theme_bg = "#2B2B2B" if sv_ttk.get_theme() == "dark" else "#FFFFFF"
        theme_fg = "white" if sv_ttk.get_theme() == "dark" else "black"
        self.fig.patch.set_facecolor(theme_bg); self.ax.set_facecolor(theme_bg)
        if data:
            labels, sizes = list(data.keys()), list(data.values())
            colors = plt.get_cmap('viridis')(np.linspace(0.2, 0.8, len(labels)))
            wedges, texts, autotexts = self.ax.pie(sizes, autopct='%1.1f%%', startangle=140, colors=colors, pctdistance=0.85, wedgeprops={'edgecolor': theme_bg, 'linewidth': 1})
            for text in texts + autotexts: text.set_color(theme_fg)
            self.fig.gca().add_artist(plt.Circle((0,0),0.70,fc=theme_bg))
            legend = self.ax.legend(wedges, labels, title=title, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=False, labelcolor=theme_fg, title_fontproperties={'weight': 'bold'})
            legend.get_title().set_color(theme_fg)
        else:
            _, texts = self.ax.pie([1], labels=['Brak danych'], colors=['#3C3F41' if sv_ttk.get_theme() == "dark" else "#E0E0E0"], startangle=90)
            for text in texts: text.set_color(theme_fg)
        self.ax.axis('equal'); self.canvas.draw()

class HistoryPage(ttk.Frame):
    """Strona z historią transakcji."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.trans_frame = ttk.LabelFrame(self, text="Historia transakcji", padding="10")
        self.trans_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        cols = ('ID', 'Symbol', 'Typ', 'Rodzaj', 'Ilość', 'Cena', 'Wartość', 'Zrealizowany Z/S', 'Data')
        button_frame = ttk.Frame(self.trans_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        export_button = ttk.Button(button_frame, text="Eksportuj do CSV", command=self.export_to_csv)
        export_button.pack(side=tk.RIGHT)
        self.tree = ttk.Treeview(self.trans_frame, columns=cols, show='headings')
        for col in cols: self.tree.heading(col, text=col)
        scrollbar = ttk.Scrollbar(self.trans_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.trans_frame.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        width = event.width - 20
        self.tree.column('ID', width=int(width*0.05)); self.tree.column('Symbol', width=int(width*0.15))
        self.tree.column('Typ', width=int(width*0.15)); self.tree.column('Rodzaj', width=int(width*0.10))
        self.tree.column('Ilość', width=int(width*0.15), anchor=tk.E); self.tree.column('Cena', width=int(width*0.10), anchor=tk.E)
        self.tree.column('Wartość', width=int(width*0.10), anchor=tk.E); self.tree.column('Zrealizowany Z/S', width=int(width*0.10), anchor=tk.E)
        self.tree.column('Data', width=int(width*0.10), anchor=tk.CENTER)

    def refresh(self, transactions, summary, currency_symbol):
        for item in self.tree.get_children(): self.tree.delete(item)
        for t in transactions:
            t_id, symbol, asset_type, trans_type, quantity, price, date = t
            pnl_str = f"{currency_symbol}{summary['realized_pnl_per_sale'].get(t_id, 0):.2f}" if trans_type == 'sell' else ""
            self.tree.insert('', tk.END, values=(t_id, symbol, asset_type.capitalize(), trans_type.capitalize(), f"{quantity:.6f}", f"{currency_symbol}{price:.2f}", f"{currency_symbol}{(quantity*price):.2f}", pnl_str, date))

    def export_to_csv(self):
        transactions = database.get_all_transactions()
        if not transactions: self.controller.show_toast("Brak transakcji do wyeksportowania."); return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")], title="Zapisz historię transakcji jako...")
        if not filepath: return
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Symbol', 'Typ Aktywa', 'Typ Transakcji', 'Ilość', 'Cena za Jednostkę', 'Data Transakcji'])
                for t in transactions: writer.writerow(t)
            self.controller.show_toast(f"Pomyślnie wyeksportowano do {filepath.split('/')[-1]}")
        except Exception as e:
            messagebox.showerror("Błąd eksportu", f"Nie udało się zapisać pliku.\nBłąd: {e}")

class MarketPage(ttk.Frame):
    """Strona z aktualnymi danymi rynkowymi."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(header_frame, text="Odśwież Dane Rynkowe", command=self.refresh_market_data).pack(side=tk.RIGHT)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.market_tabs = {}
        self.market_tabs['kryptowaluta'] = self.create_market_tab('Kryptowaluty', ('Ranking', 'Nazwa', 'Symbol', 'Cena (USD)', 'Zmiana 24h', 'Kapitalizacja Rynkowa'))
        self.market_tabs['akcja'] = self.create_market_tab('Akcje', ('Nazwa', 'Symbol', 'Cena (USD)', 'Zmiana 24h', 'Kapitalizacja Rynkowa'))
        self.market_tabs['waluta'] = self.create_market_tab('Waluty', ('Nazwa', 'Symbol', 'Cena (USD)', 'Zmiana 24h'))

    def create_market_tab(self, name, columns):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=name)
        tree = ttk.Treeview(tab, columns=columns, show='headings')
        for col in columns: tree.heading(col, text=col)
        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    def refresh_market_data(self):
        self.controller.show_toast("Pobieranie danych rynkowych...")
        self.update_crypto_data()
        self.update_yahoo_data()
        self.controller.show_toast("Dane rynkowe zaktualizowane.")

    def update_crypto_data(self):
        tree = self.market_tabs['kryptowaluta']
        for item in tree.get_children(): tree.delete(item)
        data = api_handler.get_crypto_market_data(limit=100)
        for i, coin in enumerate(data, 1):
            price = f"${coin.get('price', 0):,.2f}"
            change = f"{coin.get('change_24h', 0):.2f}%"
            market_cap = f"${coin.get('market_cap', 0):,}"
            values = (i, coin.get('name'), coin.get('symbol'), price, change, market_cap)
            tree.insert('', tk.END, values=values, tags=("green" if coin.get('change_24h', 0) >= 0 else "red",))
        tree.tag_configure("green", foreground="green"); tree.tag_configure("red", foreground="red")

    def update_yahoo_data(self):
        tree_stocks = self.market_tabs['akcja']
        for item in tree_stocks.get_children(): tree_stocks.delete(item)
        stock_data = api_handler.get_yahoo_market_data(list(instruments.get_predefined_stocks().keys()))
        for stock in stock_data:
            price = f"${stock.get('price', 0):,.2f}"
            change = f"{stock.get('change_24h', 0):.2f}%"
            market_cap = f"${stock.get('market_cap', 0):,}" if stock.get('market_cap') else "N/A"
            values = (stock.get('name'), stock.get('symbol'), price, change, market_cap)
            tree_stocks.insert('', tk.END, values=values, tags=("green" if stock.get('change_24h', 0) >= 0 else "red",))
        tree_stocks.tag_configure("green", foreground="green"); tree_stocks.tag_configure("red", foreground="red")
        tree_currencies = self.market_tabs['waluta']
        for item in tree_currencies.get_children(): tree_currencies.delete(item)
        currency_data = api_handler.get_yahoo_market_data(list(instruments.get_predefined_currencies().keys()))
        for curr in currency_data:
            price = f"{curr.get('price', 0):,.4f}"
            change = f"{curr.get('change_24h', 0):.2f}%"
            values = (curr.get('name'), curr.get('symbol'), price, change)
            tree_currencies.insert('', tk.END, values=values, tags=("green" if curr.get('change_24h', 0) >= 0 else "red",))
        tree_currencies.tag_configure("green", foreground="green"); tree_currencies.tag_configure("red", foreground="red")

# --- Główna Klasa Aplikacji ---

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Menedżer Portfela Inwestycyjnego")
        self.geometry("1300x800")
        sv_ttk.set_theme("dark")
        database.init_db()
        self.instruments_by_type = {}
        self.frames = {}
        self.create_widgets()
        self.build_instrument_list()
        self.refresh_all_data()
        self.frames["MarketPage"].refresh_market_data()

    def create_widgets(self):
        header_frame = ttk.Frame(self, style='Card.TFrame')
        header_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))
        self.theme_button = ttk.Button(header_frame, text="Zmień na Jasny", command=self.toggle_theme)
        self.theme_button.pack(side=tk.RIGHT, padx=5, pady=5)
        self.base_currency = tk.StringVar(value="USD")
        currency_combobox = ttk.Combobox(header_frame, textvariable=self.base_currency, values=["USD", "EUR", "PLN"], state="readonly", width=5)
        currency_combobox.pack(side=tk.RIGHT, padx=5, pady=5)
        currency_combobox.bind("<<ComboboxSelected>>", lambda e: self.refresh_all_data())
        ttk.Label(header_frame, text="Waluta:").pack(side=tk.RIGHT, pady=5)
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        nav_frame = ttk.Frame(main_container, width=200, style='Card.TFrame')
        nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        page_container = ttk.Frame(main_container)
        page_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        page_container.grid_rowconfigure(0, weight=1); page_container.grid_columnconfigure(0, weight=1)
        for name, F in {"Strona Główna": MainPage, "Dodaj Transakcję": AddTransactionPage, "Wykresy": ChartsPage, "Rynek": MarketPage, "Historia": HistoryPage}.items():
            frame = F(page_container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            ttk.Button(nav_frame, text=name, command=lambda f=F.__name__: self.show_page(f)).pack(fill=tk.X, pady=4, padx=5)
        self.show_page("MainPage")

    def build_instrument_list(self):
        print("Budowanie listy instrumentów...")
        self.instruments_by_type = {'kryptowaluta': [], 'akcja': [], 'waluta': []}
        for symbol, name in instruments.get_predefined_stocks().items(): self.instruments_by_type['akcja'].append((symbol, name))
        for symbol, name in instruments.get_predefined_currencies().items(): self.instruments_by_type['waluta'].append((symbol, name))
        crypto_map = api_handler.get_coingecko_symbol_map()
        if crypto_map:
            for symbol, (coin_id, name) in crypto_map.items():
                self.instruments_by_type['kryptowaluta'].append((symbol.upper(), name))
        print(f"Zbudowano listy instrumentów.")

    def get_currency_symbol(self):
        return {"USD": "$", "EUR": "€", "PLN": "zł"}.get(self.base_currency.get(), "$")

    def toggle_theme(self):
        if sv_ttk.get_theme() == "dark":
            sv_ttk.set_theme("light"); self.theme_button.config(text="Zmień na Ciemny")
        else:
            sv_ttk.set_theme("dark"); self.theme_button.config(text="Zmień na Jasny")
        self.refresh_all_data()

    def show_page(self, page_name):
        self.frames[page_name].tkraise()

    def refresh_all_data(self):
        transactions = database.get_all_transactions()
        base_currency = self.base_currency.get()
        prices = api_handler.get_prices_for_transactions(transactions, base_currency)
        if not prices and transactions: messagebox.showwarning("Błąd API", "Nie udało się pobrać aktualnych cen.")
        summary = calculator.calculate_portfolio_summary(transactions, prices)
        currency_symbol = self.get_currency_symbol()
        self.frames["MainPage"].refresh(summary, currency_symbol)
        self.frames["ChartsPage"].refresh(summary)
        self.frames["HistoryPage"].refresh(transactions, summary, currency_symbol)

    def show_toast(self, message):
        toast = tk.Toplevel(self)
        toast.wm_overrideredirect(True)
        toast.wm_geometry(f"+{self.winfo_x()+self.winfo_width()//2-100}+{self.winfo_y()+self.winfo_height()-100}")
        label = ttk.Label(toast, text=message, padding=10, style="Success.TLabel")
        label.pack()
        toast.after(2000, toast.destroy)

if __name__ == '__main__':
    app = App()
    app.mainloop()