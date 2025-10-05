# Instrukcja Budowania Aplikacji (.exe)

Aby zbudować plik wykonywalny `.exe` z dostarczonego kodu źródłowego, postępuj zgodnie z poniższymi krokami. Proces ten został w pełni zautomatyzowany za pomocą PyInstallera i wymaga jedynie wykonania kilku komend.

## Wymagania wstępne

Upewnij się, że na Twoim komputerze z systemem Windows jest zainstalowany:
1.  **Python 3.x**: Możesz go pobrać z [oficjalnej strony Python.org](https://www.python.org/downloads/). Podczas instalacji **zaznacz opcję "Add Python to PATH"**.
2.  **pip**: Zazwyczaj instaluje się automatycznie razem z Pythonem.

## Kroki do wykonania

### 1. Przygotuj środowisko

Otwórz wiersz poleceń (Command Prompt lub PowerShell) w folderze głównym projektu (tam, gdzie znajdują się pliki `main.py`, `requirements.txt` itp.).

### 2. Zainstaluj zależności

W wierszu poleceń wpisz następującą komendę, aby zainstalować wszystkie wymagane biblioteki:

```bash
pip install -r requirements.txt
```

Poczekaj, aż wszystkie pakiety zostaną pobrane i zainstalowane.

### 3. Zbuduj plik .exe

Gdy zależności są już zainstalowane, użyj poniższej komendy, aby uruchomić proces budowania za pomocą PyInstallera. Konfiguracja (`main.spec`) jest już w pełni przygotowana.

```bash
pyinstaller main.spec
```

PyInstaller przeanalizuje kod, zbierze wszystkie potrzebne pliki i spakuje je w jeden plik wykonywalny.

### 4. Znajdź gotową aplikację

Po zakończeniu procesu budowania (może to potrwać kilka minut), w folderze projektu pojawi się nowy katalog o nazwie `dist`.

Przejdź do folderu `dist`. W środku znajdziesz gotową do uruchomienia aplikację: **`PortfolioManager.exe`**.

Możesz skopiować ten plik w dowolne miejsce na swoim komputerze i uruchomić go. Aplikacja jest w pełni samodzielna i nie wymaga żadnych dodatkowych instalacji.