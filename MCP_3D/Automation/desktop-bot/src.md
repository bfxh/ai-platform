automatyzer_desktop/
│
├── .env                      # Plik z konfiguracją i danymi wrażliwymi
├── requirements.txt          # Zależności projektu
├── setup.py                  # Instalacja pakietu
├── README.md                 # Dokumentacja projektu
│
├── automatyzer_desktop/           # Główny pakiet
│   ├── __init__.py           # Inicjalizacja pakietu
│   │
│   ├── core/                 # Rdzeń bota
│   │   ├── __init__.py
│   │   ├── bot.py            # Główna klasa bota
│   │   ├── config.py         # Zarządzanie konfiguracją
│   │   └── logger.py         # Konfiguracja logowania
│   │
│   ├── actions/              # Moduły z akcjami
│   │   ├── __init__.py
│   │   ├── base.py           # Bazowa klasa akcji
│   │   ├── mouse.py          # Akcje myszy
│   │   ├── keyboard.py       # Akcje klawiatury
│   │   ├── screen.py         # Akcje związane z ekranem
│   │   ├── email.py          # Akcje związane z emailem
│   │   ├── browser.py        # Akcje związane z przeglądarką
│   │   ├── system.py         # Akcje systemowe
│   │   └── app.py            # Akcje dla konkretnych aplikacji
│   │
│   ├── connectors/           # Moduły do łączenia z różnymi systemami
│   │   ├── __init__.py
│   │   ├── rdp.py            # Łączenie przez RDP
│   │   ├── ssh.py            # Łączenie przez SSH
│   │   ├── email_connector.py # Łączenie z serwerem pocztowym
│   │   └── http.py           # Łączenie przez HTTP
│   │
│   ├── dsl/                  # Domain Specific Language
│   │   ├── __init__.py
│   │   ├── parser.py         # Parser komend DSL
│   │   ├── lexer.py          # Lekser do tokenizacji DSL
│   │   ├── grammar.py        # Definicja gramatyki DSL
│   │   └── interpreter.py    # Interpreter komend DSL
│   │
│   ├── nlp/                  # Przetwarzanie języka naturalnego
│   │   ├── __init__.py
│   │   ├── speech_to_text.py # Konwersja mowy na tekst
│   │   ├── intent_parser.py  # Rozpoznawanie intencji z tekstu
│   │   ├── entity_extractor.py # Wyodrębnianie encji z tekstu
│   │   └── command_generator.py # Generowanie komend DSL z tekstu
│   │
│   ├── pipeline/             # Pipeline automatyzacji
│   │   ├── __init__.py
│   │   ├── pipeline.py       # Klasa pipeline
│   │   ├── step.py           # Pojedynczy krok w pipeline
│   │   ├── condition.py      # Warunki w pipeline
│   │   └── builder.py        # Builder dla pipeline
│   │
│   ├── utils/                # Narzędzia pomocnicze
│   │   ├── __init__.py
│   │   ├── image_utils.py    # Narzędzia do pracy z obrazami
│   │   ├── text_utils.py     # Narzędzia do pracy z tekstem
│   │   ├── ocr.py            # Narzędzia OCR
│   │   └── validators.py     # Walidatory dla różnych danych
│   │
│   └── cli/                  # Interfejs linii komend
│       ├── __init__.py
│       ├── commands.py       # Komendy CLI
│       └── main.py           # Punkt wejściowy CLI
│
├── examples/                 # Przykłady użycia
│   ├── dsl_examples/         # Przykłady skryptów DSL
│   │   ├── linkedin_login.abot
│   │   └── email_auth.abot
│   │
│   └── pipeline_examples/    # Przykłady pipeline'ów
│       ├── data_extraction.py
│       └── web_automation.py
│
└── tests/                    # Testy
    ├── __init__.py
    ├── test_actions.py
    ├── test_dsl.py
    ├── test_nlp.py
    └── test_pipeline.py