#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Przykład użycia API Pythona do stworzenia pipeline'u automatyzacji zadań webowych.
"""

import os
import logging
import time
from automatyzer_desktop.core.bot import AutomationBot


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
    
    # Demonstracja różnych metod tworzenia i wykonywania pipeline'ów
    print("\n===== Demonstracja automatyzacji zadań webowych =====\n")
    
    # 1. Użycie pojedynczych akcji
    print("Metoda 1: Użycie pojedynczych akcji")
    execute_single_actions(bot)
    
    # 2. Użycie buildera pipeline'u
    print("\nMetoda 2: Użycie buildera pipeline'u")
    execute_pipeline_builder(bot)
    
    # 3. Użycie komendy w języku naturalnym
    print("\nMetoda 3: Użycie komendy w języku naturalnym")
    execute_natural_language(bot)
    
    # 4. Użycie skryptu DSL
    print("\nMetoda 4: Użycie skryptu DSL")
    execute_dsl_script(bot)
    
    print("\n===== Demonstracja zakończona =====")


def execute_single_actions(bot):
    """
    Wykonuje pojedyncze akcje do otwarcia przeglądarki i wyszukania informacji.
    
    Args:
        bot: Instancja bota
    """
    try:
        # Otwarcie przeglądarki
        open_action = bot.create_action("open_application", name="firefox")
        result = open_action.execute()
        print(f"Otwarcie Firefox: {'Sukces' if result else 'Błąd'}")
        
        # Opóźnienie na uruchomienie przeglądarki
        time.sleep(3)
        
        # Nawigacja do strony
        navigate_action = bot.create_action("navigate_to", url="https://www.google.com")
        result = navigate_action.execute()
        print(f"Nawigacja do Google: {'Sukces' if result else 'Błąd'}")
        
        # Opóźnienie na załadowanie strony
        time.sleep(1)
        
        # Wpisanie zapytania w wyszukiwarce
        click_action = bot.create_action("click", selector="input[name='q']")
        click_action.execute()
        
        type_action = bot.create_action("type_text", text="Python automation")
        type_action.execute()
        
        # Naciśnięcie Enter
        press_action = bot.create_action("press_key", key="enter")
        press_action.execute()
        
        print("Wyszukano frazę 'Python automation'")
        time.sleep(2)
        
        # Zrobienie zrzutu ekranu wyników
        screenshot_action = bot.create_action(
            "take_screenshot", 
            filename="single_actions_results.png"
        )
        result = screenshot_action.execute()
        print(f"Zrzut ekranu: {'Zapisano do {result}' if result else 'Błąd'}")
        
    except Exception as e:
        print(f"Błąd podczas wykonywania pojedynczych akcji: {str(e)}")


def execute_pipeline_builder(bot):
    """
    Tworzy i wykonuje pipeline za pomocą buildera.
    
    Args:
        bot: Instancja bota
    """
    try:
        # Tworzenie pipeline'u za pomocą buildera
        pipeline = bot.create_pipeline() \
            .set_name("Wyszukiwanie w Google") \
            .set_description("Otwiera przeglądarkę i wykonuje wyszukiwanie") \
            .add_step("open_application", name="firefox") \
            .add_step("wait", seconds=3) \
            .add_step("navigate_to", url="https://www.google.com") \
            .add_step("wait", seconds=1) \
            .add_step("click", selector="input[name='q']") \
            .add_step("type_text", text="Python automation framework") \
            .add_step("press_key", key="enter") \
            .add_step("wait", seconds=2) \
            .add_step("take_screenshot", filename="pipeline_results.png") \
            .build()
        
        # Wykonanie pipeline'u
        print("Uruchamianie pipeline'u...")
        results = bot.execute_pipeline(pipeline)
        
        # Sprawdzenie wyników
        success = results["success"]
        print(f"Pipeline zakończony: {'Sukces' if success else 'Błąd'}")
        if not success and results["error"]:
            print(f"Błąd: {results['error']}")
        else:
            print(f"Wykonano {results['steps_executed']} z {results['steps_count']} kroków")
            print(f"Czas wykonania: {results['execution_time']:.2f} sekund")
        
    except Exception as e:
        print(f"Błąd podczas wykonywania pipeline'u: {str(e)}")


def execute_natural_language(bot):
    """
    Wykonuje zadanie opisane w języku naturalnym.
    
    Args:
        bot: Instancja bota
    """
    try:
        # Wykonanie zadania opisanego w języku naturalnym
        command = "otwórz firefox, przejdź na stronę youtube.com i wyszukaj 'Python tutorial'"
        print(f"Wykonywanie polecenia: '{command}'")
        
        result = bot.execute_natural_language(command)
        
        if result is not None:
            print(f"Zadanie wykonane pomyślnie")
        else:
            print("Nie udało się wykonać zadania")
        
    except Exception as e:
        print(f"Błąd podczas wykonywania zadania w języku naturalnym: {str(e)}")


def execute_dsl_script(bot):
    """
    Wykonuje skrypt w języku DSL.
    
    Args:
        bot: Instancja bota
    """
    try:
        # Tworzenie tymczasowego skryptu DSL
        script_content = """
        # Skrypt DSL do wyszukiwania w DuckDuckGo
        
        # Otwarcie przeglądarki
        open_application(name="firefox");
        
        # Czekanie na uruchomienie
        wait(seconds=3);
        
        # Nawigacja do DuckDuckGo
        navigate_to(url="https://duckduckgo.com");
        
        # Czekanie na załadowanie strony
        wait(seconds=1);
        
        # Wpisanie zapytania
        click(selector="input[name='q']");
        type_text(text="Python automation bot");
        press_key(key="enter");
        
        # Czekanie na wyniki
        wait(seconds=2);
        
        # Zrzut ekranu wyników
        take_screenshot(filename="dsl_script_results.png");
        """
        
        # Zapisanie skryptu do pliku tymczasowego
        script_path = "temp_script.abot"
        with open(script_path, "w") as f:
            f.write(script_content)
        
        # Wykonanie skryptu
        print(f"Wykonywanie skryptu DSL...")
        results = bot.execute_script(script_path)
        
        print(f"Skrypt wykonany: {len(results)} operacji")
        
        # Usunięcie pliku tymczasowego
        os.remove(script_path)
        
    except Exception as e:
        print(f"Błąd podczas wykonywania skryptu DSL: {str(e)}")
        
        # Upewnij się, że plik tymczasowy zostanie usunięty
        if os.path.exists("temp_script.abot"):
            os.remove("temp_script.abot")


if __name__ == "__main__":
    main()