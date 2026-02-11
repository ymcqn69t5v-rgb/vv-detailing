# Firemní vyhledávač (UI + CLI)

Aplikace vyhledá firmy podle města, zkusí najít veřejná telefonní čísla a vypíše jen záznamy mimo O2 filtr.


## 0) Kde to je (tvůj počítač vs GitHub)

- **V tomhle chatu to běželo v pracovním prostředí** (ne přímo na tvém PC).
- Pokud to chceš mít u sebe, buď si stáhni repozitář z GitHubu, nebo si vytvoř stejné soubory ručně.

## Nejjednodušší spuštění na tvém PC (dvojklik)

### Windows
- Dvojklik na soubor **`run_app.bat`**.
- Otevře se terminál, spustí se server a otevře se adresa `http://127.0.0.1:8765`.

### Linux / macOS
- Spusť jednou v terminálu:
  ```bash
  chmod +x run_app.sh
  ```
- Pak můžeš spustit:
  ```bash
  ./run_app.sh
  ```

> Poznámka: Nestačí dvojkliknout jen `index.html`, protože aplikace potřebuje běžící Python server.


### Windows hláška „Python was not found"

Pokud vidíš v PowerShellu hlášku typu:

```text
Python was not found; run without arguments to install from the Microsoft Store...
```

znamená to, že Python není nainstalovaný (nebo není v PATH).

Postup:
1. Otevři: https://www.python.org/downloads/windows/
2. Stáhni a nainstaluj poslední Python 3.
3. **Důležité:** při instalaci zaškrtni **"Add python.exe to PATH"**.
4. Zavři a znovu otevři PowerShell.
5. Ověř instalaci:
   ```powershell
   py -3 --version
   ```
6. Potom spusť aplikaci:
   ```powershell
   .\run_app.bat
   ```

Tip: Na Windows často funguje `py -3 ...` lépe než `python3 ...`.

## 1) Spuštění webové aplikace (doporučeno)

1. Otevři terminál v této složce.
2. Spusť:

```bash
py -3 ui_app.py
```

3. V prohlížeči otevři:

```text
http://127.0.0.1:8765
```

4. Vyplň město a klikni na **Spustit hledání**.

> Pokud ti nefunguje internet/API, zapni v UI **Demo režim**.


## Co když vidíš jen „server is running"?

To je **správně**. Server čeká na požadavky.
Pak otevři prohlížeč ručně na:

```text
http://127.0.0.1:8765
```

Pokud se otevřel jiný web (např. EDB), v adresním řádku přepiš adresu přesně na `http://127.0.0.1:8765`.

## 2) Spuštění přes příkazovou řádku (CLI)

### Demo bez internetu

```bash
py -3 company_lookup.py Brno --demo
```

### Ostré hledání

```bash
py -3 company_lookup.py Brno --limit 20 --max-source-pages 4
```


### Důležité k EDB / placeným katalogům

Aplikace **funguje i bez placených služeb**.
Výchozí režim používá pouze ARES (zdarma).

- Pokud nechceš paywall, **nezaškrtávej** v UI volbu „Použít externí katalogy“.
- Tím pádem není potřeba žádné přihlášení ani platba do EDB.

## Poznámka

V některých firemních/cloud prostředích může být blokovaný přístup na externí weby (ARES/O2). Pak je potřeba aplikaci spustit v síti, kde jsou tyto služby dostupné.


### Vidím stránku "EDB POSTGRES / Server is up and running"

To **není tato aplikace**. Znamená to, že na portu 8080 běží jiná služba v počítači.

Používej naši appku na adrese:

```text
http://127.0.0.1:8765
```

Pokud je i 8765 obsazený, spusť třeba:

```bash
py -3 ui_app.py --port 8877
```
a otevři `http://127.0.0.1:8877`.
