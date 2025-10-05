# gui.py
# Interfejs użytkownika
import tkinter as tk
from tkinter import ttk, messagebox
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

class DashboardPage(ttk.Frame):
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

        # Krok 1: Wybór typu aktywa
        self.asset_type_var = tk.StringVar()
        ttk.Label(form_frame, text="1. Typ Aktywa:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.asset_type_combobox = ttk.Combobox(form_frame, textvariable=self.asset_type_var, values=['kryptowaluta', 'akcja', 'waluta'], state="readonly")
        self.asset_type_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.asset_type_combobox.bind("<<ComboboxSelected>>", self.on_asset_type_select)

        # Krok 2: Wyszukiwanie i wybór symbolu
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

        # Krok 3: Dane transakcji
        self.transaction_type_var = tk.StringVar(value='buy')
        ttk.Label(form_frame, text="4. Typ Transakcji:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Combobox(form_frame, textvariable=self.transaction_type_var, values=['buy', 'sell'], state="readonly").grid(row=3, column=1, padx=5, pady=5)

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
        asset_type = self.asset_type_var.get()
        search_term = self.name_var.get().lower()

        if not asset_type: return

        full_list = self.controller.instruments_by_type.get(asset_type, [])

        if not search_term:
            self.symbol_combobox['values'] = [item[0] for item in full_list]
        else:
            filtered_list = [item[0] for item in full_list if search_term in item[1].lower()]
            self.symbol_combobox['values'] = filtered_list

        self.symbol_var.set("")
        self.current_price_label.config(text="Aktualna cena: -")

    def on_symbol_select(self, event=None):
        symbol = self.symbol_var.get()
        asset_type = self.asset_type_var.get()

        if not symbol or not asset_type: return

        # Aktualizacja nazwy na podstawie wybranego symbolu
        full_list = self.controller.instruments_by_type.get(asset_type, [])
        for item_symbol, item_name in full_list:
            if item_symbol == symbol:
                self.name_var.set(item_name)
                break

        # Pobranie i wyświetlenie aktualnej ceny
        price_data = api_handler.get_prices_for_transactions([('', symbol, asset_type)], self.controller.base_currency.get())
        price = price_data.get(symbol)
        if price:
            self.current_price_label.config(text=f"Aktualna cena: {price:.4f} {self.controller.base_currency.get()}")
        else:
            self.current_price_label.config(text="Aktualna cena: Błąd")

    def add_new_transaction(self):
        # ... logika dodawania transakcji ...
        symbol, name, asset_type = self.symbol_var.get().upper(), self.name_var.get(), self.asset_type_var.get()
        trans_type, quantity, price = self.transaction_type_var.get(), self.quantity_var.get(), self.price_var.get()
        if not all([symbol, asset_type, trans_type, quantity > 0, price > 0]):
            messagebox.showerror("Błąd", "Wszystkie pola (oprócz nazwy) muszą być poprawnie wypełnione.")
            return
        # Używamy nazwy z mapy, jeśli istnieje, wpp. z pola
        name_to_db = self.name_var.get() if self.name_var.get() else symbol

        try:
            database.add_transaction(symbol, name_to_db, asset_type, trans_type, quantity, price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            messagebox.showinfo("Sukces", "Transakcja została dodana pomyślnie.")
            self.clear_form()
            self.controller.refresh_all_data()
        except Exception as e:
            messagebox.showerror("Błąd bazy danych", f"Wystąpił błąd: {e}")

    def clear_form(self):
        self.asset_type_var.set("")
        self.name_var.set(""); self.name_entry.config(state="disabled")
        self.symbol_var.set(""); self.symbol_combobox.config(state="disabled")
        self.quantity_var.set(0.0); self.price_var.set(0.0)
        self.current_price_label.config(text="Aktualna cena: -")

class AllocationPage(ttk.Frame):
    # ... bez zmian ...
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        chart_frame = ttk.LabelFrame(self, text="Alokacja aktywów", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chart_filter_var = tk.StringVar(value="wg aktywów")
        ttk.Combobox(chart_frame, textvariable=self.chart_filter_var, values=["wg aktywów", "wg typu"], state="readonly").pack(pady=(0, 10), fill=tk.X)
        self.chart_filter_var.trace_add("write", lambda *_: self.controller.refresh_all_data())
        self.fig = Figure(figsize=(5, 4), dpi=100)
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
            self.ax.pie([1], labels=['Brak danych'], colors=['#3C3F41' if sv_ttk.get_theme() == "dark" else "#E0E0E0"])
        self.ax.axis('equal'); self.canvas.draw()

class HistoryPage(ttk.Frame):
    # ... bez zmian ...
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        trans_frame = ttk.LabelFrame(self, text="Historia transakcji", padding="10")
        trans_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        cols = ('ID', 'Symbol', 'Typ', 'Rodzaj', 'Ilość', 'Cena', 'Wartość', 'Zrealizowany Z/S', 'Data')
        self.tree = ttk.Treeview(trans_frame, columns=cols, show='headings')
        for col in cols: self.tree.heading(col, text=col)
        self.tree.column('ID', width=40); self.tree.column('Ilość', anchor=tk.E); self.tree.column('Cena', anchor=tk.E)
        self.tree.column('Wartość', anchor=tk.E); self.tree.column('Zrealizowany Z/S', anchor=tk.E)
        self.tree.pack(fill=tk.BOTH, expand=True)
    def refresh(self, transactions, summary, currency_symbol):
        for item in self.tree.get_children(): self.tree.delete(item)
        for t in transactions:
            t_id, symbol, asset_type, trans_type, quantity, price, date = t
            pnl_str = f"{currency_symbol}{summary['realized_pnl_per_sale'].get(t_id, 0):.2f}" if trans_type == 'sell' else ""
            self.tree.insert('', tk.END, values=(t_id, symbol, asset_type, trans_type, f"{quantity:.6f}", f"{currency_symbol}{price:.2f}", f"{currency_symbol}{(quantity*price):.2f}", pnl_str, date))

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
        for name, F in {"Dashboard": DashboardPage, "Dodaj Transakcję": AddTransactionPage, "Alokacja": AllocationPage, "Historia": HistoryPage}.items():
            frame = F(page_container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            ttk.Button(nav_frame, text=name, command=lambda f=F.__name__: self.show_page(f)).pack(fill=tk.X, pady=4, padx=5)
        self.show_page("DashboardPage")

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
        self.frames["DashboardPage"].refresh(summary, currency_symbol)
        # self.frames["AddTransactionPage"].update_symbol_combobox(self.all_instruments_map)
        self.frames["AllocationPage"].refresh(summary)
        self.frames["HistoryPage"].refresh(transactions, summary, currency_symbol)

if __name__ == '__main__':
    app = App()
    app.mainloop()