# Punkt wejściowy CLI
"""
main.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Główny punkt wejściowy dla interfejsu linii komend.
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Any

from automatyzer_desktop.core.bot import AutomationBot
from automatyzer_desktop.core.config import Config
from automatyzer_desktop.dsl.interpreter import DSLInterpreter
from automatyzer_desktop.nlp.speech_to_text import SpeechToText


def setup_logging(verbose: bool = False) -> None:
    """
    Konfiguruje system logowania.

    Args:
        verbose: Czy włączyć bardziej szczegółowe logi
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("automatyzer_desktop.log"),
            logging.StreamHandler()
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parsuje argumenty linii komend.

    Returns:
        Sparsowane argumenty
    """
    parser = argparse.ArgumentParser(description='Bot do automatyzacji zadań przez Remote Desktop')

    # Opcje konfiguracji
    parser.add_argument('--env', type=str, default='.env', help='Ścieżka do pliku .env')
    parser.add_argument('--config', type=str, help='Ścieżka do pliku konfiguracyjnego JSON')
    parser.add_argument('-v', '--verbose', action='store_true', help='Włącz szczegółowe logowanie')

    # Opcje wykonania
    subparsers = parser.add_subparsers(dest='command', help='Komenda do wykonania')

    # Komenda: script - wykonanie skryptu DSL
    script_parser = subparsers.add_parser('script', help='Wykonaj skrypt DSL')
    script_parser.add_argument('script_file', type=str, help='Ścieżka do pliku ze skryptem DSL')

    # Komenda: task - wykonanie pojedynczego zadania
    task_parser = subparsers.add_parser('task', help='Wykonaj pojedyncze zadanie')
    task_parser.add_argument('task_text', type=str, help='Opis zadania w języku naturalnym')

    # Komenda: command - wykonanie komendy DSL
    command_parser = subparsers.add_parser('command', help='Wykonaj komendę DSL')
    command_parser.add_argument('command_text', type=str, help='Komenda DSL do wykonania')

    # Komenda: listen - nasłuchiwanie komend głosowych
    listen_parser = subparsers.add_parser('listen', help='Nasłuchuj komend głosowych')
    listen_parser.add_argument('--keyword', type=str, default='bot', help='Słowo kluczowe aktywujące bota')
    listen_parser.add_argument('--continuous', action='store_true',
                               help='Tryb ciągłego nasłuchiwania (bez słowa kluczowego)')

    # Komenda: interactive - tryb interaktywny
    subparsers.add_parser('interactive', help='Uruchom w trybie interaktywnym')

    # Komenda: rdp - połączenie RDP
    rdp_parser = subparsers.add_parser('rdp', help='Połącz przez RDP')
    rdp_parser.add_argument('--host', type=str, help='Host do połączenia RDP')
    rdp_parser.add_argument('--user', type=str, help='Nazwa użytkownika RDP')
    rdp_parser.add_argument('--pass', type=str, help='Hasło RDP')
    rdp_parser.add_argument('--port', type=str, default='3389', help='Port RDP')

    # Komenda: server - uruchomienie serwera API
    server_parser = subparsers.add_parser('server', help='Uruchom serwer API')
    server_parser.add_argument('--host', type=str, default='localhost', help='Host dla serwera API')
    server_parser.add_argument('--port', type=int, default=8000, help='Port dla serwera API')

    return parser.parse_args()


def main() -> int:
    """
    Główna funkcja programu.

    Returns:
        Kod wyjścia (0 = sukces, inna wartość = błąd)
    """
    # Parsowanie argumentów
    args = parse_arguments()

    # Konfiguracja logowania
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Inicjalizacja bota
        bot = AutomationBot(config_path=args.env, config_file=args.config)

        # Wykonanie odpowiedniej komendy
        if args.command == 'script':
            # Wykonanie skryptu DSL
            logger.info(f"Wykonywanie skryptu DSL: {args.script_file}")
            return execute_script(bot, args.script_file)

        elif args.command == 'task':
            # Wykonanie zadania opisanego w języku naturalnym
            logger.info(f"Wykonywanie zadania: {args.task_text}")
            return execute_task(bot, args.task_text)

        elif args.command == 'command':
            # Wykonanie komendy DSL
            logger.info(f"Wykonywanie komendy DSL: {args.command_text}")
            return execute_command(bot, args.command_text)

        elif args.command == 'listen':
            # Nasłuchiwanie komend głosowych
            logger.info("Uruchamianie trybu nasłuchiwania komend głosowych")
            return listen_for_commands(bot, args.keyword, args.continuous)

        elif args.command == 'interactive':
            # Tryb interaktywny
            logger.info("Uruchamianie trybu interaktywnego")
            return run_interactive_mode(bot)

        elif args.command == 'rdp':
            # Połączenie RDP
            logger.info(f"Łączenie przez RDP do {args.host}")
            return connect_rdp(bot, args.host, args.user, getattr(args, 'pass'), args.port)

        elif args.command == 'server':
            # Uruchomienie serwera API
            logger.info(f"Uruchamianie serwera API na {args.host}:{args.port}")
            return run_api_server(bot, args.host, args.port)

        else:
            # Jeśli nie podano komendy, pokaż pomoc
            print("Podaj komendę do wykonania. Użyj flagi --help, aby zobaczyć dostępne opcje.")
            return 1

    except Exception as e:
        logger.error(f"Błąd podczas wykonywania programu: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def execute_script(bot: AutomationBot, script_file: str) -> int:
    """
    Wykonuje skrypt DSL.

    Args:
        bot: Instancja bota
        script_file: Ścieżka do pliku skryptu

    Returns:
        Kod wyjścia (0 = sukces, inna wartość = błąd)
    """
    if not os.path.exists(script_file):
        print(f"Plik skryptu nie istnieje: {script_file}")
        return 1

    try:
        results = bot.execute_script(script_file)
        print(f"Skrypt wykonany pomyślnie. Wyniki: {len(results)} operacji")
        return 0
    except Exception as e:
        print(f"Błąd podczas wykonywania skryptu: {str(e)}")
        return 1


def execute_task(bot: AutomationBot, task_text: str) -> int:
    """
    Wykonuje zadanie opisane w języku naturalnym.

    Args:
        bot: Instancja bota
        task_text: Opis zadania

    Returns:
        Kod wyjścia (0 = sukces, inna wartość = błąd)
    """
    try:
        result = bot.execute_natural_language(task_text)
        if result is not None:
            print(f"Zadanie wykonane pomyślnie. Wynik: {result}")
            return 0
        else:
            print("Nie udało się wykonać zadania.")
            return 1
    except Exception as e:
        print(f"Błąd podczas wykonywania zadania: {str(e)}")
        return 1


def execute_command(bot: AutomationBot, command_text: str) -> int:
    """
    Wykonuje komendę DSL.

    Args:
        bot: Instancja bota
        command_text: Komenda DSL

    Returns:
        Kod wyjścia (0 = sukces, inna wartość = błąd)
    """
    try:
        result = bot.execute_command(command_text)
        print(f"Komenda wykonana pomyślnie. Wynik: {result}")
        return 0
    except Exception as e:
        print(f"Błąd podczas wykonywania komendy: {str(e)}")
        return 1


def listen_for_commands(bot: AutomationBot, keyword: str, continuous: bool) -> int:
    """
    Nasłuchuje komend głosowych.

    Args:
        bot: Instancja bota
        keyword: Słowo kluczowe aktywujące bota
        continuous: Czy nasłuchiwać ciągle (bez słowa kluczowego)

    Returns:
        Kod wyjścia (0 = sukces, inna wartość = błąd)
    """
    try:
        # Konfiguracja rozpoznawania mowy
        speech_config = {
            "keyword": keyword,
            "continuous_listening": continuous,
            "timeout": 10
        }

        speech_to_text = SpeechToText(speech_config)

        def process_command(text: str) -> None:
            """Funkcja wywołana dla każdej rozpoznanej komendy"""
            print(f"Rozpoznano: {text}")

            try:
                # Wykonaj komendę
                result = bot.execute_natural_language(text)
                if result is not None:
                    print(f"Wykonano pomyślnie. Wynik: {result}")
                else:
                    print("Nie udało się wykonać komendy.")
            except Exception as e:
                print(f"Błąd podczas wykonywania komendy: {str(e)}")

        # Uruchomienie nasłuchiwania
        print(f"Nasłuchiwanie komend głosowych...")
        if continuous:
            print("Tryb ciągły. Naciśnij Ctrl+C, aby zakończyć.")
        else:
            print(f"Powiedz '{keyword}', aby aktywować bota. Naciśnij Ctrl+C, aby zakończyć.")

        speech_to_text.start_listening(process_command)

        # Czekaj na Ctrl+C
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nPrzerwano nasłuchiwanie.")
        finally:
            # Zakończ nasłuchiwanie
            speech_to_text.stop_listening_thread()

        return 0
    except Exception as e:
        print(f"Błąd podczas nasłuchiwania komend: {str(e)}")
        return 1


def run_interactive_mode(bot: AutomationBot) -> int:
    """
    Uruchamia tryb interaktywny.

    Args:
        bot: Instancja bota

    Returns:
        Kod wyjścia (0 = sukces, inna wartość = błąd)
    """
    print("Tryb interaktywny. Wpisz 'exit' lub 'quit', aby zakończyć.")
    print("Wpisz komendę DSL lub zadanie w języku naturalnym.")
    print("Dodaj przedrostek '!' przed komendą DSL.")

    dsl_interpreter = DSLInterpreter()

    while True:
        try:
            # Pobierz komendę od użytkownika
            command = input("> ")

            # Sprawdź czy to komenda wyjścia
            if command.lower() in ('exit', 'quit'):
                break

            # Sprawdź czy to komenda DSL (z przedrostkiem !)
            if command.startswith('!'):
                # Usuń przedrostek
                dsl_command = command[1:].strip()
                result = bot.execute_command(dsl_command)
                print(f"Wynik: {result}")
            else:
                # Traktuj jako zadanie w języku naturalnym
                result = bot.execute_natural_language(command)
                if result is not None:
                    print(f"Wynik: {result}")
                else:
                    print("Nie udało się wykonać zadania.")

        except KeyboardInterrupt:
            print("\nPrzerwano.")
            break
        except Exception as e:
            print(f"Błąd: {str(e)}")

    return 0


def connect_rdp(bot: AutomationBot, host: str, username: str, password: str, port: str) -> int:
    """
    Łączy się z serwerem RDP.

    Args:
        bot: Instancja bota
        host: Adres hosta RDP
        username: Nazwa użytkownika
        password: Hasło
        port: Port

    Returns:
        Kod wyjścia (0 = sukces, inna wartość = błąd)
    """
    try:
        # Pobierz domyślne wartości z konfiguracji, jeśli nie podano
        if host is None:
            host = bot.config.get('RDP_HOST')
        if username is None:
            username = bot.config.get('RDP_USERNAME')
        if password is None:
            password = bot.config.get('RDP_PASSWORD')
        if port is None:
            port = bot.config.get('RDP_PORT', '3389')

        # Sprawdź czy mamy host
        if host is None:
            print("Nie podano hosta RDP. Użyj --host lub ustaw zmienną RDP_HOST w pliku .env")
            return 1

        # Połącz przez RDP
        from automatyzer_desktop.connectors.rdp import RDPConnector
        connector = RDPConnector(bot)

        success = connector.connect(host, username, password, port)
        if success:
            print(f"Połączono z {host}:{port}")

            # Czekaj na zamknięcie połączenia
            input("Naciśnij Enter, aby zakończyć połączenie...")
            return 0
        else:
            print("Nie udało się połączyć przez RDP.")
            return 1
    except Exception as e:
        print(f"Błąd podczas łączenia przez RDP: {str(e)}")
        return 1


def run_api_server(bot: AutomationBot, host: str, port: int) -> int:
    """
    Uruchamia serwer API.

    Args:
        bot: Instancja bota
        host: Adres hosta dla serwera API
        port: Port dla serwera API

    Returns:
        Kod wyjścia (0 = sukces, inna wartość = błąd)
    """
    try:
        from automatyzer_desktop.api.server import start_server

        # Uruchom serwer
        start_server(bot, host, port)
        return 0
    except ImportError:
        print("Serwer API wymaga zainstalowania dodatkowych zależności.")
        print("Zainstaluj je za pomocą: pip install automatyzer_desktop[api]")
        return 1
    except Exception as e:
        print(f"Błąd podczas uruchamiania serwera API: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())