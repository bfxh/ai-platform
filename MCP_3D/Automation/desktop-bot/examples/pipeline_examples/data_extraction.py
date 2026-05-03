# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Przykład użycia API Pythona do ekstrakcji danych z aplikacji.
Demonstruje jak połączyć akcje automatyzacji z extrakcją danych za pomocą OCR.
"""

import os
import logging
import time
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Any

from automatyzer_desktop.core.bot import AutomationBot
from automatyzer_desktop.pipeline.pipeline import Pipeline
from automatyzer_desktop.utils.image_utils import take_screenshot


class DataExtractionExample:
    """
    Klasa demonstrująca ekstrakcję danych z aplikacji.
    """

    def __init__(self, bot: AutomationBot):
        """
        Inicjalizacja przykładu.

        Args:
            bot: Instancja bota
        """
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.data = []
        self.screenshots_folder = "data_extraction_screenshots"

        # Utworzenie folderu na zrzuty ekranu
        os.makedirs(self.screenshots_folder, exist_ok=True)

    def run(self):
        """
        Uruchamia demonstrację ekstrakcji danych.
        """
        self.logger.info("Rozpoczęcie demonstracji ekstrakcji danych")

        # Krok 1: Otwarcie aplikacji (w tym przykładzie używamy kalkulatora)
        self._open_application()

        # Krok 2: Wykonanie serii obliczeń i ekstrakcja wyników
        self._execute_calculations()

        # Krok 3: Analiza zebranych danych
        self._analyze_data()

        # Krok 4: Zamknięcie aplikacji
        self._close_application()

        self.logger.info("Zakończenie demonstracji ekstrakcji danych")

    def _open_application(self):
        """
        Otwiera aplikację kalkulatora.
        """
        # W zależności od systemu operacyjnego, wybierz odpowiednią aplikację kalkulatora
        system_type = self.bot.system_type

        if system_type == 'Windows':
            app_name = "calc"
        elif system_type == 'Darwin':  # macOS
            app_name = "Calculator"
        else:  # Linux
            app_name = "gnome-calculator"

        # Utworzenie pipeline'u do otwarcia aplikacji
        pipeline = self.bot.create_pipeline() \
            .set_name("Otwarcie kalkulatora") \
            .add_step("open_application", name=app_name) \
            .add_step("wait", seconds=2)  # Czekaj na pełne uruchomienie \
        .build()

    # Wykonanie pipeline'u
    result = self.bot.execute_pipeline(pipeline)

    if result["success"]:
        self.logger.info(f"Aplikacja kalkulatora otwarta pomyślnie")
    else:
        self.logger.error(f"Błąd podczas otwierania aplikacji: {result['error']}")
        raise Exception("Nie udało się otworzyć aplikacji kalkulatora")


def _execute_calculations(self):
    """
    Wykonuje serię obliczeń i ekstrahuje wyniki.
    """
    # Lista przykładowych obliczeń do wykonania
    calculations = [
        {"operation": "2+2", "expected": 4},
        {"operation": "5*10", "expected": 50},
        {"operation": "100/4", "expected": 25},
        {"operation": "15-7", "expected": 8},
        {"operation": "2^8", "expected": 256},
        {"operation": "sqrt(16)", "expected": 4}
    ]

    for i, calc in enumerate(calculations):
        self.logger.info(f"Wykonywanie obliczenia {i + 1}/{len(calculations)}: {calc['operation']}")

        try:
            # Resetowanie kalkulatora
            self._reset_calculator()

            # Wprowadzenie obliczenia
            self._enter_calculation(calc["operation"])

            # Wykonanie obliczenia (naciśnięcie =)
            self._execute_calculation()

            # Zrzut ekranu wyniku
            screenshot_path = os.path.join(
                self.screenshots_folder,
                f"calculation_{i + 1}.png"
            )
            take_screenshot(screenshot_path)

            # Ekstrakcja wyniku z ekranu
            result = self._extract_result()

            # Dodanie danych do kolekcji
            self.data.append({
                "id": i + 1,
                "operation": calc["operation"],
                "expected_result": calc["expected"],
                "actual_result": result,
                "screenshot": screenshot_path,
                "success": abs(float(result) - calc["expected"]) < 0.001 if result is not None else False
            })

            self.logger.info(f"Obliczenie {calc['operation']} = {result}")

        except Exception as e:
            self.logger.error(f"Błąd podczas obliczenia {calc['operation']}: {str(e)}")

            # Dodanie informacji o błędzie
            self.data.append({
                "id": i + 1,
                "operation": calc["operation"],
                "expected_result": calc["expected"],
                "actual_result": None,
                "screenshot": None,
                "success": False,
                "error": str(e)
            })


def _reset_calculator(self):
    """
    Resetuje kalkulator.
    """
    # W zależności od kalkulatora, może być potrzebna inna sekwencja działań
    # Tutaj używamy klawisza 'C' lub 'AC' (All Clear)

    # Próba znalezienia przycisku reset na ekranie
    if self.bot.execute_command("screen_contains(image='calculator_clear_button.png')"):
        self.bot.execute_command("click(image='calculator_clear_button.png')")
    else:
        # Alternatywnie, użyj klawiszy
        self.bot.execute_command("press_key(key='escape')")  # Często działa w kalkulatorach
        self.bot.execute_command("press_key(key='c')")  # Klawisz 'C'


def _enter_calculation(self, operation: str):
    """
    Wprowadza obliczenie do kalkulatora.

    Args:
        operation: Wyrażenie do obliczenia
    """
    # Mapowanie specjalnych operatorów na sekwencje klawiszy
    operator_map = {
        "^": ["shift", "6"],  # Potęgowanie
        "sqrt(": ["s", "q", "r", "t", "("],  # Pierwiastek kwadratowy
    }

    # Wprowadzenie wyrażenia znak po znaku
    i = 0
    while i < len(operation):
        # Sprawdź, czy to początek specjalnego operatora
        found_special = False
        for op, keys in operator_map.items():
            if operation[i:i + len(op)] == op:
                # Wprowadź specjalny operator
                for key in keys:
                    self.bot.execute_command(f"press_key(key='{key}')")
                    time.sleep(0.1)

                i += len(op)
                found_special = True
                break

        if not found_special:
            # Wprowadź pojedynczy znak
            char = operation[i]

            # Obsługa specjalnych przypadków
            if char == "*":
                self.bot.execute_command("press_key(key='*')")
            elif char == "/":
                self.bot.execute_command("press_key(key='/')")
            else:
                self.bot.execute_command(f"press_key(key='{char}')")

            time.sleep(0.1)
            i += 1


def _execute_calculation(self):
    """
    Wykonuje obliczenie (naciska klawisz =).
    """
    self.bot.execute_command("press_key(key='=')")
    time.sleep(0.5)  # Czekaj na wynik


def _extract_result(self) -> float:
    """
    Ekstrahuje wynik z ekranu kalkulatora za pomocą OCR.

    Returns:
        Wynik obliczenia jako liczba
    """
    # W zależności od kalkulatora, region ekranu z wynikiem może być różny
    # Tutaj używamy okna wynikowego dla typowego układu kalkulatora

    # Próba znalezienia regionu wyniku
    if self.bot.execute_command("screen_contains(image='calculator_result_area.png')"):
        # Jeśli znaleziono obszar wyniku, użyj go do ekstrakcji tekstu
        result_region = self.bot.execute_command("find_on_screen(image='calculator_result_area.png')")

        # Pobierz współrzędne
        x, y = result_region

        # Użyj OCR do ekstrakcji tekstu z regionu
        # Typowa szerokość i wysokość okna wynikowego to około 200x50 pikseli
        text = self.bot.execute_command(f"get_text_from_region(left={x - 100}, top={y - 25}, width=200, height=50)")

        # Przetwarzanie tekstu
        if text:
            # Usuń białe znaki i inne niepożądane znaki
            text = text.strip().replace(' ', '').replace(',', '.')

            try:
                # Konwersja na liczbę
                return float(text)
            except ValueError:
                self.logger.warning(f"Nie udało się przekonwertować tekstu na liczbę: '{text}'")
                return None

    # Jeśli nie udało się znaleźć obszaru wyniku, spróbuj skopiować wynik do schowka
    try:
        # Użyj kombinacji klawiszy Ctrl+C w kalkulatorze
        self.bot.execute_command("hotkey(keys=['ctrl', 'c'])")
        time.sleep(0.2)

        # Pobierz wartość ze schowka
        clipboard_text = self.bot.execute_command("get_clipboard_text()")

        if clipboard_text:
            # Przetwarzanie tekstu
            clipboard_text = clipboard_text.strip().replace(' ', '').replace(',', '.')

            try:
                # Konwersja na liczbę
                return float(clipboard_text)
            except ValueError:
                self.logger.warning(f"Nie udało się przekonwertować tekstu ze schowka na liczbę: '{clipboard_text}'")
    except Exception as e:
        self.logger.warning(f"Błąd podczas próby użycia schowka: {str(e)}")

    return None


def _analyze_data(self):
    """
    Analizuje zebrane dane i generuje raport.
    """
    # Konwersja zebranych danych na DataFrame
    df = pd.DataFrame(self.data)

    # Wyświetlenie statystyk
    self.logger.info(f"Zebrano {len(df)} wyników obliczeń")
    self.logger.info(f"Poprawne wyniki: {df['success'].sum()}/{len(df)}")

    # Zapisanie danych do CSV
    csv_path = "data_extraction_results.csv"
    df.to_csv(csv_path, index=False)
    self.logger.info(f"Zapisano wyniki do pliku CSV: {csv_path}")

    # Utworzenie wykresu
    if len(df) > 0:
        plt.figure(figsize=(10, 6))

        # Wykres wyników
        plt.subplot(1, 2, 1)
        success_counts = df['success'].value_counts()
        plt.pie(success_counts,
                labels=['Poprawne', 'Błędne'] if True in success_counts.index else ['Błędne', 'Poprawne'],
                autopct='%1.1f%%', colors=['green', 'red'] if True in success_counts.index else ['red', 'green'])
        plt.title('Skuteczność ekstrakcji danych')

        # Wykres operacji
        plt.subplot(1, 2, 2)
        operations = df['operation'].tolist()
        results = df['actual_result'].tolist()
        plt.bar(operations, results)
        plt.title('Wyniki operacji')
        plt.xlabel('Operacja')
        plt.ylabel('Wynik')
        plt.xticks(rotation=45)

        # Zapisanie wykresu
        plt.tight_layout()
        plt.savefig("data_extraction_chart.png")
        self.logger.info("Zapisano wykres wyników: data_extraction_chart.png")


def _close_application(self):
    """
    Zamyka aplikację kalkulatora.
    """
    # W zależności od systemu operacyjnego, używamy odpowiedniej metody zamykania
    system_type = self.bot.system_type

    if system_type == 'Windows':
        app_name = "Calculator"
    elif system_type == 'Darwin':  # macOS
        app_name = "Calculator"
    else:  # Linux
        app_name = "gnome-calculator"

    # Utworzenie pipeline'u do zamknięcia aplikacji
    pipeline = self.bot.create_pipeline() \
        .set_name("Zamknięcie kalkulatora") \
        .add_step("close_application", name=app_name) \
        .build()

    # Wykonanie pipeline'u
    result = self.bot.execute_pipeline(pipeline)

    if result["success"]:
        self.logger.info(f"Aplikacja kalkulatora zamknięta pomyślnie")
    else:
        self.logger.warning(f"Nie udało się zamknąć aplikacji: {result['error']}")


def main():
    """
    Główna funkcja demonstracyjna.
    """
    # Konfiguracja logowania
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Inicjalizacja bota
    bot = AutomationBot(config_path='.env')

    # Uruchomienie demonstracji
    print("\n===== Demonstracja ekstrakcji danych z aplikacji =====\n")

    example = DataExtractionExample(bot)
    example.run()

    print("\n===== Demonstracja zakończona =====")


if __name__ == "__main__":
    main()