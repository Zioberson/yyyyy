# Instrukcja Budowania i Debugowania Aplikacji (.exe)

Celem tej instrukcji jest nie tylko zbudowanie aplikacji, ale przede wszystkim **znalezienie przyczyny błędu**, który wystąpił wcześniej. Proszę, postępuj dokładnie według poniższych kroków.

## Wymagania wstępne

Upewnij się, że na Twoim komputerze z systemem Windows jest zainstalowany:
1.  **Python 3.x**: Możesz go pobrać z [oficjalnej strony Python.org](https://www.python.org/downloads/). Podczas instalacji **zaznacz opcję "Add Python to PATH"**.
2.  **pip**: Zazwyczaj instaluje się automatycznie razem z Pythonem.

## Kroki do wykonania

### 1. Przygotuj środowisko

Otwórz wiersz poleceń (Command Prompt lub PowerShell) w folderze głównym projektu (tam, gdzie znajdują się pliki `main.py`, `requirements.txt` itp.).

### 2. Zainstaluj zależności

Jeśli nie zrobiłeś tego wcześniej, wpisz następującą komendę, aby zainstalować wszystkie wymagane biblioteki:

```bash
pip install -r requirements.txt
```

Poczekaj, aż wszystkie pakiety zostaną pobrane i zainstalowane.

### 3. Zbuduj plik .exe w trybie debugowania

Użyj poniższej komendy, aby uruchomić proces budowania. Używamy nowej konfiguracji `main.spec`, która stworzy plik `.exe` z **aktywnym oknem konsoli do debugowania**.

```bash
pyinstaller main.spec
```

### 4. Uruchom aplikację i zdiagnozuj problem

Po zakończeniu budowania, w folderze projektu pojawi się nowy katalog o nazwie `dist`.

1.  Przejdź do folderu `dist`. Znajdziesz tam plik **`PortfolioManager_Debug.exe`**.
2.  **Uruchom ten plik.** Powinny pojawić się dwa okna: główne okno aplikacji oraz **czarne okno konsoli**.
3.  Jeśli aplikacja się zawiesi lub nie uruchomi, **skup się na oknie konsoli**.
4.  **Skopiuj całą treść, która pojawiła się w czarnym oknie konsoli** – zwłaszcza jeśli zawiera komunikaty o błędach (słowa takie jak `Error`, `Traceback`, `Failed`).
5.  **Prześlij mi skopiowany tekst.** To kluczowa informacja, która pozwoli mi zidentyfikować i naprawić problem.

Dziękuję za Twoją pomoc w tym procesie! Razem na pewno uda nam się to naprawić.