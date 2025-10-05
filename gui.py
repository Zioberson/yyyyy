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

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Menedżer Portfela Inwestycyjnego")
        self.geometry("1200x800")

        # Ustawienie nowoczesnego motywu
        sv_ttk.set_theme("dark")

        # Inicjalizacja bazy danych
        database.init_db()

        self.assets_map = {} # Słownik do mapowania symbol -> (nazwa, typ)

        self.create_widgets()

        self.update_symbol_combobox() # Początkowe wypełnienie listy symboli

    def create_widgets(self):
        # Główny kontener
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Kontener na podsumowanie i wykres (lewa strona)
        left_pane = ttk.Frame(main_frame)
        left_pane.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Kontener na formularz i listę transakcji (prawa strona)
        right_pane = ttk.Frame(main_frame)
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Podsumowanie portfela (Dashboard) ---
        summary_frame = ttk.LabelFrame(left_pane, text="Podsumowanie", padding="10")
        summary_frame.pack(fill=tk.X, pady=5)

        self.total_value_label = ttk.Label(summary_frame, text="Całkowita wartość: $0.00", font=("Helvetica", 12, "bold"))
        self.total_value_label.pack(anchor=tk.W)
        self.pnl_label = ttk.Label(summary_frame, text="Zysk/Strata (Niezrealiz.): $0.00 (0.00%)")
        self.pnl_label.pack(anchor=tk.W)
        self.realized_pnl_label = ttk.Label(summary_frame, text="Zysk/Strata (Zrealiz.): $0.00")
        self.realized_pnl_label.pack(anchor=tk.W)

        # --- Wykres alokacji ---
        chart_frame = ttk.LabelFrame(left_pane, text="Alokacja aktywów", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Lista rozwijana do filtrowania wykresu
        self.chart_filter_var = tk.StringVar(value="wg aktywów")
        chart_filter_options = ["wg aktywów", "wg typu"]
        chart_filter_combobox = ttk.Combobox(
            chart_frame,
            textvariable=self.chart_filter_var,
            values=chart_filter_options,
            state="readonly"
        )
        chart_filter_combobox.pack(pady=(0, 10), fill=tk.X)
        chart_filter_combobox.bind("<<ComboboxSelected>>", lambda e: self.refresh_transactions_view())

        # Konfiguracja wykresu dla ciemnego motywu
        self.fig = Figure(figsize=(5, 4), dpi=100, facecolor="#2B2B2B")
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Formularz dodawania transakcji ---
        form_frame = ttk.LabelFrame(right_pane, text="Dodaj nową transakcję", padding="10")
        form_frame.pack(fill=tk.X, pady=5)

        # Pola formularza
        self.symbol_var = tk.StringVar()
        ttk.Label(form_frame, text="Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.symbol_combobox = ttk.Combobox(form_frame, textvariable=self.symbol_var)
        self.symbol_combobox.grid(row=0, column=1, padx=5, pady=5)
        # Powiązanie zdarzeń z funkcją autouzupełniania
        self.symbol_combobox.bind('<<ComboboxSelected>>', self.on_symbol_change)
        self.symbol_combobox.bind('<KeyRelease>', self.on_symbol_change)

        self.name_var = tk.StringVar()
        ttk.Label(form_frame, text="Nazwa:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var)
        self.name_entry.grid(row=0, column=3, padx=5, pady=5)

        self.asset_type_var = tk.StringVar()
        self.asset_types = ['kryptowaluta', 'akcja', 'etf', 'waluta', 'surowiec', 'nieruchomosc']
        ttk.Label(form_frame, text="Typ aktywa:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.asset_type_combobox = ttk.Combobox(form_frame, textvariable=self.asset_type_var, values=self.asset_types, state="readonly")
        self.asset_type_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.asset_type_var.set(self.asset_types[0])

        self.transaction_type_var = tk.StringVar()
        transaction_types = ['buy', 'sell']
        ttk.Label(form_frame, text="Typ transakcji:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Combobox(form_frame, textvariable=self.transaction_type_var, values=transaction_types, state="readonly").grid(row=1, column=3, padx=5, pady=5)
        self.transaction_type_var.set(transaction_types[0])

        self.quantity_var = tk.DoubleVar()
        ttk.Label(form_frame, text="Ilość:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(form_frame, textvariable=self.quantity_var).grid(row=2, column=1, padx=5, pady=5)

        self.price_var = tk.DoubleVar()
        ttk.Label(form_frame, text="Cena za jedn.:").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(form_frame, textvariable=self.price_var).grid(row=2, column=3, padx=5, pady=5)

        # Przycisk dodawania
        add_button = ttk.Button(form_frame, text="Dodaj transakcję", command=self.add_new_transaction)
        add_button.grid(row=3, column=3, padx=5, pady=10, sticky=tk.E)

        # --- Widok listy transakcji ---
        transactions_frame = ttk.LabelFrame(right_pane, text="Historia transakcji", padding="10")
        transactions_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Przycisk odświeżania
        refresh_button = ttk.Button(transactions_frame, text="Odśwież ceny", command=self.refresh_transactions_view)
        refresh_button.pack(anchor=tk.E, pady=5)

        self.tree = ttk.Treeview(
            transactions_frame,
            columns=('ID', 'Symbol', 'Typ', 'Rodzaj', 'Ilość', 'Cena', 'Wartość', 'Zrealizowany Z/S', 'Data'),
            show='headings'
        )
        self.tree.heading('ID', text='ID')
        self.tree.heading('Symbol', text='Symbol')
        self.tree.heading('Typ', text='Typ aktywa')
        self.tree.heading('Rodzaj', text='Rodzaj')
        self.tree.heading('Ilość', text='Ilość')
        self.tree.heading('Cena', text='Cena jedn.')
        self.tree.heading('Wartość', text='Wartość trans.')
        self.tree.heading('Zrealizowany Z/S', text='Zrealiz. Z/S')
        self.tree.heading('Data', text='Data')

        # Ustawienie szerokości kolumn
        for col in self.tree['columns']:
            self.tree.column(col, width=110, anchor=tk.CENTER)
        self.tree.column('ID', width=40)
        self.tree.column('Symbol', anchor=tk.W)
        self.tree.column('Ilość', anchor=tk.E)
        self.tree.column('Cena zakupu', anchor=tk.E)
        self.tree.column('Aktualna cena', anchor=tk.E)
        self.tree.column('Wartość', anchor=tk.E)
        self.tree.column('Data', width=150)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Wypełnienie danymi przy starcie
        self.refresh_transactions_view()

    def update_symbol_combobox(self):
        """Pobiera wszystkie aktywa z bazy i aktualizuje listę w comboboxie."""
        assets = database.get_all_assets()
        self.assets_map = {asset[0]: (asset[1], asset[2]) for asset in assets}
        self.symbol_combobox['values'] = sorted(list(self.assets_map.keys()))

    def on_symbol_change(self, event=None):
        """
        Wywoływana, gdy użytkownik wybierze lub wpisze symbol.
        Automatycznie uzupełnia nazwę i typ aktywa, jeśli symbol jest znany.
        """
        symbol = self.symbol_var.get().upper()
        if symbol in self.assets_map:
            name, asset_type = self.assets_map[symbol]
            self.name_var.set(name)
            self.asset_type_var.set(asset_type)
            self.name_entry.config(state='readonly')
            self.asset_type_combobox.config(state='readonly')
        else:
            self.name_entry.config(state='normal')
            self.asset_type_combobox.config(state='normal')

    def refresh_transactions_view(self):
        # 1. Czyszczenie widoku
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 2. Pobieranie danych
        transactions = database.get_all_transactions()
        crypto_symbols = set(t[1] for t in transactions if t[2] == 'kryptowaluta')

        prices = {}
        if crypto_symbols:
            prices = api_handler.get_crypto_prices(list(crypto_symbols))
            if not prices and any(t[2] == 'kryptowaluta' for t in transactions):
                 messagebox.showwarning("Błąd API", "Nie udało się pobrać aktualnych cen. Wyświetlane wartości mogą być nieaktualne.")

        # 3. Obliczenia
        summary = calculator.calculate_portfolio_summary(transactions, prices)

        # 4. Aktualizacja dashboardu
        self.total_value_label.config(text=f"Całkowita wartość: ${summary['total_value']:.2f}")

        unrealized_pnl = summary['unrealized_pnl_amount']
        unrealized_pnl_percent = summary['unrealized_pnl_percent']
        self.pnl_label.config(
            text=f"Zysk/Strata (Niezrealiz.): ${unrealized_pnl:.2f} ({unrealized_pnl_percent:.2f}%)",
            foreground="green" if unrealized_pnl >= 0 else "red"
        )

        realized_pnl = summary['total_realized_pnl']
        self.realized_pnl_label.config(
            text=f"Zysk/Strata (Zrealiz.): ${realized_pnl:.2f}",
            foreground="green" if realized_pnl >= 0 else "red"
        )

        # 5. Aktualizacja tabeli transakcji
        for t in transactions:
            t_id, symbol, asset_type, trans_type, quantity, price, date = t

            transaction_value = quantity * price
            realized_pnl_str = ""

            if trans_type == 'sell':
                pnl = summary['realized_pnl_per_sale'].get(t_id, 0)
                realized_pnl_str = f"${pnl:.2f}"

            self.tree.insert('', tk.END, values=(
                t_id, symbol, asset_type, trans_type, f"{quantity:.6f}", f"{price:.2f}",
                f"${transaction_value:.2f}", realized_pnl_str, date
            ))

        # 6. Aktualizacja wykresu alokacji
        chart_mode = self.chart_filter_var.get()
        if chart_mode == "wg aktywów":
            data_to_display = summary['allocation_by_asset']
            legend_title = "Aktywa"
        else: # "wg typu"
            data_to_display = summary['allocation_by_type']
            legend_title = "Typy Aktywów"

        self.update_pie_chart(data_to_display, legend_title)

    def update_pie_chart(self, allocation_data, title):
        """Rysuje wykres kołowy na podstawie danych o alokacji."""
        self.ax.clear()
        self.ax.set_facecolor("#2B2B2B") # Tło osi wykresu

        if allocation_data:
            labels = list(allocation_data.keys())
            sizes = list(allocation_data.values())

            # Lepsza paleta kolorów, bardziej widoczna na ciemnym tle
            colors = plt.get_cmap('viridis')(np.linspace(0, 1, len(labels)))

            wedges, texts, autotexts = self.ax.pie(
                sizes,
                autopct='%1.1f%%',
                startangle=140,
                colors=colors,
                pctdistance=0.85, # Odległość procentów od środka
                wedgeprops={'edgecolor': '#2B2B2B', 'linewidth': 1} # Krawędzie kawałków
            )

            # Ustawienie koloru tekstu na biały
            for text in texts + autotexts:
                text.set_color('white')

            # Rysowanie okręgu w środku, aby stworzyć "donut chart"
            centre_circle = plt.Circle((0,0),0.70,fc='#2B2B2B')
            self.fig.gca().add_artist(centre_circle)

            # Dodanie legendy z dynamicznym tytułem
            self.ax.legend(wedges, labels,
                  title=title,
                  loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1),
                  frameon=False, # Bez ramki
                  labelcolor='white',
                  title_fontproperties={'color': 'white', 'weight': 'bold'})

        else:
            self.ax.pie([1], labels=['Brak danych'],
                        labelcolor='white',
                        colors=['#3C3F41'],
                        startangle=90)

        self.ax.axis('equal')
        self.canvas.draw()

    def add_new_transaction(self):
        # Pobranie danych z formularza
        symbol = self.symbol_var.get().upper()
        name = self.name_var.get()
        asset_type = self.asset_type_var.get()
        transaction_type = self.transaction_type_var.get()
        quantity = self.quantity_var.get()
        price = self.price_var.get()

        # Prosta walidacja
        if not all([symbol, name, asset_type, transaction_type, quantity > 0, price > 0]):
            messagebox.showerror("Błąd", "Wszystkie pola muszą być poprawnie wypełnione.")
            return

        try:
            # Dodanie transakcji do bazy danych
            database.add_transaction(
                symbol=symbol,
                name=name,
                asset_type=asset_type,
                transaction_type=transaction_type,
                quantity=quantity,
                price_per_unit=price,
                transaction_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            messagebox.showinfo("Sukces", "Transakcja została dodana pomyślnie.")
            self.clear_form()
            self.refresh_transactions_view()
            self.update_symbol_combobox()
        except Exception as e:
            messagebox.showerror("Błąd bazy danych", f"Wystąpił błąd: {e}")

    def clear_form(self):
        self.symbol_var.set("")
        self.name_var.set("")
        self.quantity_var.set(0.0)
        self.price_var.set(0.0)
        # Odblokowujemy pola na wypadek, gdyby były zablokowane
        self.name_entry.config(state='normal')
        self.asset_type_combobox.config(state='normal')
        self.symbol_combobox.focus()

if __name__ == '__main__':
    app = App()
    app.mainloop()