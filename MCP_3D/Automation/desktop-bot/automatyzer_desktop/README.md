# AutomationBot

Bot do automatyzacji zadań poprzez Remote Desktop z możliwością sterowania głosowego i skryptowego.

## Funkcjonalności

* Automatyzacja akcji myszy i klawiatury na zdalnym lub lokalnym komputerze
* Wykrywanie elementów i obrazów na ekranie
* Obsługa różnych systemów operacyjnych (Windows, Linux, macOS)
* Własny język skryptowy DSL (Domain Specific Language)
* Sterowanie głosowe poprzez rozpoznawanie mowy
* Integracja z pocztą elektroniczną (pobieranie i analiza wiadomości)
* Elastyczna architektura pipeline'ów do automatyzacji złożonych zadań
* Konwersja poleceń w języku naturalnym na akcje automatyzacji

## Wymagania

* Python 3.7+
* Zależności wymienione w `requirements.txt`
* System operacyjny: Windows, Linux lub macOS

## Instalacja

### Z użyciem pip

```bash
# Instalacja podstawowej wersji
pip install automation-bot

# Instalacja z obsługą NLP i rozpoznawania mowy
pip install automation-bot[nlp]

# Instalacja pełnej wersji ze wszystkimi zależnościami
pip install automation-bot[all]
```

### Z kodu źródłowego

```bash
# Klonowanie repozytorium
git clone https://github.com/username/automation-bot.git
cd automation-bot

# Instalacja zależności
pip install -e .
```

## Konfiguracja

Utwórz plik `.env` w katalogu projektu z wymaganymi zmiennymi środowiskowymi:

```
# Konfiguracja połączenia RDP
RDP_HOST=komputer.example.com
RDP_USERNAME=twoj_login
RDP_PASSWORD=twoje_haslo
RDP_PORT=3389
RDP_RESOLUTION=1920x1080

# Konfiguracja email
EMAIL_IMAP_SERVER=imap.example.com
EMAIL_SMTP_SERVER=smtp.example.com
EMAIL_PORT=993
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=twoj_login@example.com
EMAIL_PASSWORD=twoje_haslo_email

# Dane logowania do portali
LINKEDIN_USERNAME=twoj_login_linkedin
LINKEDIN_PASSWORD=twoje_haslo_linkedin

# Konfiguracja aplikacji
DELAY_BETWEEN_ACTIONS=0.5
SCREENSHOT_FOLDER=screenshots
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
STOP_ON_ERROR=False
```

## Użycie

### Linia komend

```bash
# Wykonanie pojedynczego zadania
automatyzer_desktop task "otwórz aplikację firefox i zaloguj się do portalu linkedin"

# Wykonanie skryptu DSL
automatyzer_desktop script moj_skrypt.abot

# Wykonanie pojedynczej komendy DSL
automatyzer_desktop command "open_application(name='firefox');"

# Nasłuchiwanie komend głosowych
automatyzer_desktop listen --keyword "bot" --continuous

# Tryb interaktywny
automatyzer_desktop interactive

# Połączenie RDP
automatyzer_desktop rdp --host komputer.example.com --user login --pass haslo
```

### Skrypty DSL

Skrypty DSL (.abot) pozwalają na definiowanie sekwencji akcji:

```
# Otwarcie przeglądarki
open_application(name="firefox");

# Nawigacja do strony
wait(seconds=2);
navigate_to(url="linkedin.com");

# Logowanie
type_text(selector="#username", text=env.LINKEDIN_USERNAME);
type_text(selector="#password", text=env.LINKEDIN_PASSWORD);
click(selector="#login-button");

# Czekanie na zalogowanie
wait(seconds=3);

# Pobranie kodu uwierzytelniającego z emaila, jeśli potrzebny
if screen_contains(image="auth_code_input.png") {
    emails = get_emails(from="linkedin@notifications.com", max_count=1);
    auth_code = extract_code(text=emails[0].body, regex="\\b\\d{6}\\b");
    type_text(text=auth_code);
    click(selector="#verify-button");
}
```

### Python API

```python
from automatyzer_desktop.core.bot import AutomationBot

# Inicjalizacja bota
bot = AutomationBot(config_path='.env')

# Wykonanie zadania w języku naturalnym
bot.execute_natural_language("otwórz aplikację firefox i zaloguj się do portalu linkedin")

# Wykonanie komendy DSL
bot.execute_command("open_application(name='firefox');")

# Tworzenie i wykonanie pipeline'u
pipeline = bot.create_pipeline() \
    .set_name("Logowanie do LinkedIn") \
    .add_step("open_application", name="firefox") \
    .add_step("wait", seconds=2) \
    .add_step("type_text", selector="#username", text=bot.config.get("LINKEDIN_USERNAME")) \
    .add_step("type_text", selector="#password", text=bot.config.get("LINKEDIN_PASSWORD")) \
    .add_step("click", selector="#login-button") \
    .build()

results = bot.execute_pipeline(pipeline)
print(results)
```

## Architektura

Bot zbudowany jest z kilku kluczowych komponentów:

1. **Akcje** - pojedyncze operacje, które może wykonać bot (np. kliknięcie, wpisanie tekstu)
2. **Pipeline** - sekwencja kroków do wykonania
3. **DSL** - język skryptowy do definiowania zadań automatyzacji
4. **NLP** - przetwarzanie języka naturalnego do zamiany poleceń tekstowych na akcje
5. **Connectors** - moduły do łączenia z różnymi systemami (RDP, SSH, email)

## Dokumentacja

Pełna dokumentacja dostępna jest w katalogu `docs/` oraz online na [docs.automation-bot.example.com](https://docs.automation-bot.example.com).

## Licencja

Ten projekt jest udostępniany na licencji MIT. Szczegóły w pliku LICENSE.


Oto podsumowanie modularnej architektury bota do automatyzacji zadań, który stworzyliśmy:

### Główne komponenty

1. **Struktura modułowa**
   - Rozdzieliliśmy kod na logiczne moduły (actions, core, dsl, nlp, pipeline, utils)
   - Stworzyliśmy hierarchię akcji (podzielone na kategorie: App, Mouse, Keyboard)
   - Zastosowaliśmy wzorce projektowe (Builder, Dependency Injection, Command)

2. **Domain Specific Language (DSL)**
   - Własny język skryptowy do definiowania zadań automatyzacji
   - Lekser, parser i interpreter do przetwarzania skryptów
   - Możliwość tworzenia złożonych sekwencji z warunkami i pętlami

3. **Przetwarzanie języka naturalnego (NLP)**
   - Konwersja poleceń głosowych i tekstowych na akcje automatyzacji
   - Rozpoznawanie intencji i wyodrębnianie encji z tekstu
   - Interfejs do systemów rozpoznawania mowy

4. **System pipeline'ów**
   - Budowanie sekwencji kroków za pomocą wygodnego interfejsu buildera
   - Warunki wykonania kroków i obsługa błędów
   - Kontekst wykonania z przechowywaniem stanu

5. **Interfejs linii komend**
   - Obsługa różnych trybów uruchamiania (skrypty, zadania, komendy, tryb interaktywny)
   - Tryb nasłuchiwania komend głosowych
   - Możliwość połączenia RDP

### Kluczowe pliki i ich funkcje

1. **Core**
   - `Bot.py` - główna klasa bota zarządzająca wszystkimi komponentami
   - `Config.py` - zarządzanie konfiguracją z pliku .env i innych źródeł

2. **Actions**
   - `Base.py` - bazowa klasa dla wszystkich akcji
   - `App/*.py` - akcje związane z aplikacjami (otwieranie, zamykanie, fokusowanie)
   - `Mouse.py` - akcje myszy (klikanie, przeciąganie, scrollowanie)
   - `Keyboard.py` - akcje klawiatury (pisanie, naciskanie klawiszy)

3. **DSL**
   - `Grammar.py` - definicja gramatyki języka skryptowego
   - `Lexer.py` - lekser do tokenizacji kodu
   - `Parser.py` - parser tworzący drzewo składniowe
   - `Interpreter.py` - wykonywanie kodu DSL

4. **NLP**
   - `Intent_Parser.py` - rozpoznawanie intencji z tekstu
   - `Entity_Extractor.py` - wyodrębnianie encji (parametrów akcji)
   - `Command_Generator.py` - generowanie komend DSL z intencji
   - `Speech_to_Text.py` - rozpoznawanie mowy

5. **Pipeline**
   - `Pipeline.py` - główna klasa pipeline'u
   - `Step.py` - pojedynczy krok w pipeline
   - `Builder.py` - interfejs budowania pipeline'ów

6. **Utils**
   - `Image_Utils.py` - narzędzia do pracy z obrazami i OCR

7. **CLI**
   - `Main.py` - główny punkt wejściowy programu z interfejsem CLI

### Przykłady użycia

1. **Skrypty DSL**
   - `linkedin_login.abot` - automatyczne logowanie do LinkedIn
   - `email_auth.abot` - pobieranie kodu uwierzytelniającego z email

2. **Przykłady pipeline'ów**
   - `web_automation.py` - automatyzacja zadań w przeglądarce
   - `data_extraction.py` - ekstrakcja danych z aplikacji kalkulatora

### Zalety tej architektury

1. **Modularność i rozszerzalność**
   - Łatwe dodawanie nowych akcji bez zmian w istniejącym kodzie
   - Możliwość rozszerzania języka DSL o nowe konstrukcje
   - Łatwe dodawanie obsługi nowych platform i systemów

2. **Wielopoziomowy interfejs użytkownika**
   - Od niskiego poziomu (pojedyncze akcje) do wysokiego (polecenia głosowe)
   - Możliwość tworzenia złożonych automatyzacji różnymi metodami

3. **Łatwa konfiguracja**
   - Centralne zarządzanie ustawieniami przez plik .env i konfigurację
   - Obsługa różnych systemów operacyjnych

4. **Solidna obsługa błędów**
   - Szczegółowe logowanie na każdym poziomie
   - Mechanizmy odzyskiwania po błędach w pipeline'ach

Ta modularna architektura pozwala na łatwe dostosowanie bota do różnorodnych zastosowań automatyzacji, od prostych zadań po złożone sekwencje. Dzięki temu podejściu można również stopniowo rozbudowywać funkcjonalność, dodając nowe moduły lub rozszerzając istniejące, bez konieczności przepisywania całego kodu.