#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Przykład łączenia przez RDP do Windows i automatyzacji logowania w przeglądarce Firefox.
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv
from typing import Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# Importy z automatyzer_desktop
from automatyzer_desktop.core.bot import AutomationBot
from automatyzer_desktop.connectors.rdp import RDPConnector


class RDPFirefoxLoginExample:
    """
    Przykład automatyzacji logowania do serwisu przez Firefox w sesji RDP.
    """

    def __init__(self):
        """
        Inicjalizacja przykładu.
        """
        # Konfiguracja logowania
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        self.logger = logging.getLogger(__name__)

        # Załadowanie zmiennych środowiskowych
        load_dotenv()

        # Konfiguracja RDP
        self.rdp_config = {
            "host": os.getenv("RDP_HOST"),
            "username": os.getenv("RDP_USERNAME"),
            "password": os.getenv("RDP_PASSWORD"),
            "port": os.getenv("RDP_PORT", "3389"),
            "resolution": os.getenv("RDP_RESOLUTION", "1920x1080")
        }

        # Konfiguracja strony docelowej
        self.website_config = {
            "url": os.getenv("WEBSITE_URL", "https://example.com"),
            "username": os.getenv("WEBSITE_USERNAME"),
            "password": os.getenv("WEBSITE_PASSWORD")
        }

        # Inicjalizacja bota
        self.bot = AutomationBot()

        # Ścieżki do obrazów referencyjnych
        self.images_dir = "reference_images"
        self.images = {
            "desktop": f"{self.images_dir}/windows_desktop.png",
            "start_button": f"{self.images_dir}/windows_start_button.png",
            "firefox_window": f"{self.images_dir}/firefox_window.png",
            "address_bar": f"{self.images_dir}/firefox_address_bar.png",
            "login_form": f"{self.images_dir}/login_form.png",
            "username_field": f"{self.images_dir}/username_field.png",
            "password_field": f"{self.images_dir}/password_field.png",
            "login_button": f"{self.images_dir}/login_button.png",
            "login_success": f"{self.images_dir}/login_success.png",
            "login_error": f"{self.images_dir}/login_error.png"
        }

    def run(self) -> bool:
        """
        Uruchamia proces logowania przez RDP.

        Returns:
            True jeśli proces zakończył się sukcesem, False w przeciwnym razie
        """
        self.logger.info("Rozpoczęcie procesu logowania przez RDP")

        # Połączenie RDP
        if not self._connect_rdp():
            return False

        try:
            # Uruchomienie Firefox
            if not self._start_firefox():
                return False

            # Nawigacja do strony
            if not self._navigate_to_website():
                return False

            # Logowanie na stronie
            if not self._login_to_website():
                return False

            # Wykonanie akcji po zalogowaniu (opcjonalne)
            self._post_login_actions()

            # Sukces
            self.logger.info("Proces zakończony sukcesem")
            return True

        except Exception as e:
            self.logger.error(f"Wystąpił błąd podczas procesu: {str(e)}")
            return False
        finally:
            # Czekaj na zakończenie przez użytkownika
            input("Naciśnij Enter, aby zakończyć sesję RDP...")

            # Rozłączenie RDP
            self._disconnect_rdp()

    def _connect_rdp(self) -> bool:
        """
        Nawiązuje połączenie RDP.

        Returns:
            True jeśli połączenie zostało nawiązane, False w przeciwnym razie
        """
        try:
            self.logger.info(f"Łączenie z hostem RDP: {self.rdp_config['host']}")

            # Sprawdzenie czy mamy wszystkie wymagane parametry
            if not all([self.rdp_config['host'], self.rdp_config['username'], self.rdp_config['password']]):
                self.logger.error("Brak wymaganych parametrów RDP. Sprawdź plik .env")
                return False

            # Inicjalizacja konektora RDP
            self.rdp_connector = RDPConnector(self.bot)

            # Połączenie RDP
            success = self.rdp_connector.connect(
                host=self.rdp_config['host'],
                username=self.rdp_config['username'],
                password=self.rdp_config['password'],
                port=self.rdp_config['port'],
                resolution=self.rdp_config['resolution']
            )

            if not success:
                self.logger.error("Nie udało się nawiązać połączenia RDP")
                return False

            # Czekanie na załadowanie pulpitu
            self.logger.info("Oczekiwanie na załadowanie pulpitu Windows...")
            time.sleep(10)

            # Sprawdzenie czy pulpit został załadowany
            if not self._check_image("desktop"):
                self.logger.error("Nie wykryto pulpitu Windows")
                return False

            self.logger.info("Połączenie RDP nawiązane pomyślnie")
            return True

        except Exception as e:
            self.logger.error(f"Błąd podczas łączenia przez RDP: {str(e)}")
            return False

    def _start_firefox(self) -> bool:
        """
        Uruchamia przeglądarkę Firefox.

        Returns:
            True jeśli Firefox został uruchomiony, False w przeciwnym razie
        """
        try:
            self.logger.info("Uruchamianie przeglądarki Firefox")

            # Sprawdzenie czy Firefox jest już uruchomiony
            if self._check_image("firefox_window"):
                self.logger.info("Firefox jest już uruchomiony")
                return True

            # Kliknięcie przycisku Start
            if not self._click_image("start_button"):
                self.logger.warning("Nie znaleziono przycisku Start, próba alternatywna")
                # Alternatywna metoda - naciśnięcie klawisza Windows
                self.bot.execute_command("press_key(key='win')")

            time.sleep(1)

            # Wpisanie "firefox" w wyszukiwarce
            self.bot.execute_command("type_text(text='firefox')")
            time.sleep(1)

            # Naciśnięcie Enter
            self.bot.execute_command("press_key(key='enter')")

            # Czekanie na uruchomienie Firefox
            self.logger.info("Oczekiwanie na uruchomienie Firefox...")
            time.sleep(5)

            # Sprawdzenie czy Firefox uruchomił się
            if not self._check_image("firefox_window"):
                self.logger.warning("Nie wykryto okna Firefox, próba alternatywna")

                # Alternatywna metoda - przez wykonanie polecenia
                self.bot.execute_command("execute_shell_command(command='start firefox')")
                time.sleep(5)

                if not self._check_image("firefox_window"):
                    self.logger.error("Nie udało się uruchomić Firefox")
                    return False

            self.logger.info("Firefox uruchomiony pomyślnie")
            return True

        except Exception as e:
            self.logger.error(f"Błąd podczas uruchamiania Firefox: {str(e)}")
            return False

    def _navigate_to_website(self) -> bool:
        """
        Nawiguje do strony internetowej.

        Returns:
            True jeśli nawigacja się powiodła, False w przeciwnym razie
        """
        try:
            url = self.website_config['url']
            self.logger.info(f"Nawigacja do strony: {url}")

            # Kliknięcie w pasek adresu
            if not self._click_image("address_bar"):
                self.logger.warning("Nie znaleziono paska adresu, próba alternatywna")
                # Alternatywna metoda - skrót klawiaturowy
                self.bot.execute_command("hotkey(keys=['ctrl', 'l'])")

            time.sleep(0.5)

            # Czyszczenie paska adresu
            self.bot.execute_command("hotkey(keys=['ctrl', 'a'])")
            self.bot.execute_command("press_key(key='delete')")
            time.sleep(0.2)

            # Wpisanie adresu
            self.bot.execute_command(f"type_text(text='{url}')")
            self.bot.execute_command("press_key(key='enter')")

            # Czekanie na załadowanie strony
            self.logger.info("Oczekiwanie na załadowanie strony...")
            time.sleep(5)

            # Sprawdzenie czy strona załadowała się poprawnie
            if not self._check_image("login_form"):
                self.logger.error("Nie wykryto formularza logowania")
                return False

            self.logger.info("Strona załadowana pomyślnie")
            return True

        except Exception as e:
            self.logger.error(f"Błąd podczas nawigacji do strony: {str(e)}")
            return False

    def _login_to_website(self) -> bool:
        """
        Loguje się do serwisu.

        Returns:
            True jeśli logowanie się powiodło, False w przeciwnym razie
        """
        try:
            username = self.website_config['username']
            password = self.website_config['password']

            if not username or not password:
                self.logger.error("Brak nazwy użytkownika lub hasła. Sprawdź plik .env")
                return False

            self.logger.info("Wypełnianie formularza logowania")

            # Kliknięcie w pole nazwy użytkownika
            if not self._click_image("username_field"):
                self.logger.error("Nie znaleziono pola nazwy użytkownika")
                return False

            time.sleep(0.5)

            # Wpisanie nazwy użytkownika
            self.bot.execute_command(f"type_text(text='{username}')")

            # Kliknięcie w pole hasła
            if not self._click_image("password_field"):
                self.logger.error("Nie znaleziono pola hasła")
                return False

            time.sleep(0.5)

            # Wpisanie hasła
            self.bot.execute_command(f"type_text(text='{password}')")

            # Kliknięcie przycisku logowania
            if not self._click_image("login_button"):
                self.logger.error("Nie znaleziono przycisku logowania")
                return False

            # Czekanie na proces logowania
            self.logger.info("Oczekiwanie na zakończenie procesu logowania...")
            time.sleep(5)

            # Sprawdzenie czy logowanie się powiodło
            if self._check_image("login_success"):
                self.logger.info("Logowanie zakończone sukcesem")
                return True
            elif self._check_image("login_error"):
                self.logger.error("Błąd logowania - nieprawidłowe dane")
                return False
            else:
                self.logger.warning("Nie można potwierdzić statusu logowania")
                # Zakładamy że logowanie mogło się powieść
                return True

        except Exception as e:
            self.logger.error(f"Błąd podczas logowania: {str(e)}")
            return False

    def _post_login_actions(self) -> None:
        """
        Wykonuje akcje po zalogowaniu (opcjonalne).
        """
        self.logger.info("Wykonywanie akcji po zalogowaniu")

        # Tutaj można dodać dodatkowe akcje, które mają być wykonane po zalogowaniu
        # Na przykład:
        # - nawigacja do określonej podstrony
        # - pobranie danych
        # - wykonanie określonych czynności

        # Przykład - zrobienie zrzutu ekranu po zalogowaniu
        self.bot.execute_command("take_screenshot(filename='after_login.png')")
        self.logger.info("Wykonano zrzut ekranu po zalogowaniu")

    def _disconnect_rdp(self) -> None:
        """
        Rozłącza sesję RDP.
        """
        try:
            self.logger.info("Rozłączanie sesji RDP")
            self.rdp_connector.disconnect()
            self.logger.info("Sesja RDP zakończona")
        except Exception as e:
            self.logger.error(f"Błąd podczas rozłączania sesji RDP: {str(e)}")

    def _check_image(self, image_name: str, confidence: float = 0.7) -> bool:
        """
        Sprawdza czy obraz znajduje się na ekranie.

        Args:
            image_name: Nazwa obrazu (klucz ze słownika self.images)
            confidence: Poziom pewności dopasowania (0.0-1.0)

        Returns:
            True jeśli obraz został znaleziony, False w przeciwnym razie
        """
        image_path = self.images.get(image_name)
        if not image_path:
            self.logger.error(f"Nie znaleziono definicji obrazu: {image_name}")
            return False

        return self.bot.execute_command(f"screen_contains(image='{image_path}', confidence={confidence})")

    def _click_image(self, image_name: str, confidence: float = 0.7) -> bool:
        """
        Klika w obraz na ekranie.

        Args:
            image_name: Nazwa obrazu (klucz ze słownika self.images)
            confidence: Poziom pewności dopasowania (0.0-1.0)

        Returns:
            True jeśli kliknięcie się powiodło, False w przeciwnym razie
        """
        image_path = self.images.get(image_name)
        if not image_path:
            self.logger.error(f"Nie znaleziono definicji obrazu: {image_name}")
            return False

        return self.bot.execute_command(f"click(image='{image_path}', confidence={confidence})")


def main():
    """
    Główna funkcja uruchamiająca przykład.
    """
    print("\n===== Demonstracja logowania przez RDP do Firefox =====\n")

    example = RDPFirefoxLoginExample()
    success = example.run()

    if success:
        print("\nProces zakończony pomyślnie.")
    else:
        print("\nProces zakończony z błędami.")

    print("\n===== Koniec demonstracji =====")


if __name__ == "__main__":
    main()