# gui.py
# Interfejs użytkownika
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import database
import api_handler
import calculator

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Menedżer Portfela Inwestycyjnego")
        self.geometry("1200x800") # Zwiększamy rozmiar okna

        # Inicjalizacja bazy danych
        database.init_db()

        self.create_widgets()

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

        # --- Wykres alokacji ---
        chart_frame = ttk.LabelFrame(left_pane, text="Alokacja aktywów", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.fig = Figure(figsize=(4, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ax.pie([1], labels=['Brak danych'], autopct='%1.1f%%', startangle=90)
        self.ax.axis('equal') # Zapewnia, że wykres jest kołem

        # --- Formularz dodawania transakcji ---
        form_frame = ttk.LabelFrame(right_pane, text="Dodaj nową transakcję", padding="10")
        form_frame.pack(fill=tk.X, pady=5)

        # Pola formularza
        self.symbol_var = tk.StringVar()
        ttk.Label(form_frame, text="Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(form_frame, textvariable=self.symbol_var).grid(row=0, column=1, padx=5, pady=5)

        self.name_var = tk.StringVar()
        ttk.Label(form_frame, text="Nazwa:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(form_frame, textvariable=self.name_var).grid(row=0, column=3, padx=5, pady=5)

        self.asset_type_var = tk.StringVar()
        asset_types = ['kryptowaluta', 'akcja', 'etf', 'waluta', 'surowiec', 'nieruchomosc']
        ttk.Label(form_frame, text="Typ aktywa:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Combobox(form_frame, textvariable=self.asset_type_var, values=asset_types, state="readonly").grid(row=1, column=1, padx=5, pady=5)
        self.asset_type_var.set(asset_types[0])

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
            columns=('ID', 'Symbol', 'Typ', 'Ilość', 'Cena zakupu', 'Aktualna cena', 'Wartość', 'Data'),
            show='headings'
        )
        self.tree.heading('ID', text='ID')
        self.tree.heading('Symbol', text='Symbol')
        self.tree.heading('Typ', text='Typ aktywa')
        self.tree.heading('Ilość', text='Ilość')
        self.tree.heading('Cena zakupu', text='Cena zakupu')
        self.tree.heading('Aktualna cena', text='Aktualna cena')
        self.tree.heading('Wartość', text='Wartość ($)')
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
        pnl_amount = summary['unrealized_pnl_amount']
        pnl_percent = summary['unrealized_pnl_percent']
        pnl_color = "green" if pnl_amount >= 0 else "red"
        self.pnl_label.config(
            text=f"Zysk/Strata: ${pnl_amount:.2f} ({pnl_percent:.2f}%)",
            foreground=pnl_color
        )

        # 5. Aktualizacja tabeli transakcji (zostaje bez zmian, ale teraz jest częścią większego procesu)
        for t in transactions:
            asset_id, symbol, asset_type, _, quantity, price, date = t
            current_price_val = prices.get(symbol)
            current_price_str = f"{current_price_val:.2f}" if current_price_val else "N/A"
            current_value_str = f"{(quantity * current_price_val):.2f}" if current_price_val else "N/A"
            self.tree.insert('', tk.END, values=(asset_id, symbol, asset_type, f"{quantity:.6f}", f"{price:.2f}", current_price_str, current_value_str, date))

        # 6. Aktualizacja wykresu alokacji
        self.ax.clear()
        if summary['allocation_by_asset']:
            labels = summary['allocation_by_asset'].keys()
            sizes = summary['allocation_by_asset'].values()
            self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        else:
            self.ax.pie([1], labels=['Brak danych'], autopct='%1.1f%%', startangle=90)
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
            self.refresh_transactions_view() # Odśwież widok po dodaniu
        except Exception as e:
            messagebox.showerror("Błąd bazy danych", f"Wystąpił błąd: {e}")

    def clear_form(self):
        self.symbol_var.set("")
        self.name_var.set("")
        self.quantity_var.set(0.0)
        self.price_var.set(0.0)

if __name__ == '__main__':
    app = App()
    app.mainloop()