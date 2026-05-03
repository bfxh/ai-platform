# Akcje klawiatury
"""
keyboard.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implementacja akcji związanych z klawiaturą.
"""

import time
import logging
from typing import Any, Dict, Optional, List, Union
import pyautogui

from automatyzer_desktop.actions.base import BaseAction


class TypeTextAction(BaseAction):
    """
    Akcja wpisywania tekstu.
    """

    ACTION_NAME = "type_text"
    ACTION_DESCRIPTION = "Wpisuje podany tekst."

    REQUIRED_PARAMS = {
        "text": str  # Tekst do wpisania
    }
    OPTIONAL_PARAMS = {
        "selector": (str, None),  # Selektor CSS elementu, w który wpisać tekst
        "interval": (float, 0.0),  # Czas oczekiwania między wpisaniem kolejnych znaków (w sekundach)
        "delay": (float, 0.1)  # Opóźnienie po wpisaniu całego tekstu (w sekundach)
    }

    def execute(self) -> bool:
        """
        Wykonuje akcję wpisywania tekstu.

        Returns:
            True jeśli wpisywanie się powiodło, False w przeciwnym razie
        """
        # Pobranie parametrów
        text = self.get_param("text")
        selector = self.get_param("selector")
        interval = self.get_param("interval")
        delay = self.get_param("delay")

        try:
            # Jeśli podano selektor, kliknij w dany element przed wpisywaniem
            if selector:
                try:
                    element = pyautogui.locateOnScreen(selector)
                    if element:
                        pyautogui.click(pyautogui.center(element))
                    else:
                        self.logger.error(f"Nie znaleziono elementu z selektorem: {selector}")
                        return False
                except Exception as e:
                    self.logger.error(f"Błąd podczas lokalizacji elementu z selektorem: {str(e)}")
                    return False

            # Wpisanie tekstu
            pyautogui.write(text, interval=interval)
            self.logger.info(f"Wpisano tekst: {text}")

            # Opóźnienie po wpisaniu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas wpisywania tekstu: {str(e)}")
            return False


class PressKeyAction(BaseAction):
    """
    Akcja naciśnięcia pojedynczego klawisza.
    """

    ACTION_NAME = "press_key"
    ACTION_DESCRIPTION = "Naciska pojedynczy klawisz."

    REQUIRED_PARAMS = {
        "key": str  # Klawisz do naciśnięcia
    }
    OPTIONAL_PARAMS = {
        "presses": (int, 1),  # Liczba naciśnięć
        "interval": (float, 0.0),  # Czas oczekiwania między naciśnięciami (w sekundach)
        "delay": (float, 0.1)  # Opóźnienie po naciśnięciu (w sekundach)
    }

    def execute(self) -> bool:
        """
        Wykonuje akcję naciśnięcia klawisza.

        Returns:
            True jeśli naciśnięcie się powiodło, False w przeciwnym razie
        """
        # Pobranie parametrów
        key = self.get_param("key")
        presses = self.get_param("presses")
        interval = self.get_param("interval")
        delay = self.get_param("delay")

        try:
            # Naciśnięcie klawisza
            pyautogui.press(key, presses=presses, interval=interval)
            self.logger.info(f"Naciśnięto klawisz: {key} (x{presses})")

            # Opóźnienie po naciśnięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas naciskania klawisza: {str(e)}")
            return False


class HotkeyAction(BaseAction):
    """
    Akcja naciśnięcia kombinacji klawiszy.
    """

    ACTION_NAME = "hotkey"
    ACTION_DESCRIPTION = "Naciska kombinację klawiszy."

    REQUIRED_PARAMS = {
        "keys": list  # Lista klawiszy do naciśnięcia jednocześnie
    }
    OPTIONAL_PARAMS = {
        "delay": (float, 0.1)  # Opóźnienie po naciśnięciu (w sekundach)
    }

    def validate(self) -> bool:
        """
        Sprawdza czy parametry akcji są poprawne.

        Returns:
            True jeśli parametry są poprawne, False w przeciwnym razie
        """
        keys = self.get_param("keys")
        return isinstance(keys, list) and len(keys) > 0

    def execute(self) -> bool:
        """
        Wykonuje akcję naciśnięcia kombinacji klawiszy.

        Returns:
            True jeśli naciśnięcie się powiodło, False w przeciwnym razie
        """
        # Sprawdzenie parametrów
        if not self.validate():
            self.logger.error("Parametr 'keys' musi być niepustą listą klawiszy.")
            return False

        # Pobranie parametrów
        keys = self.get_param("keys")
        delay = self.get_param("delay")

        try:
            # Naciśnięcie kombinacji klawiszy
            pyautogui.hotkey(*keys)
            self.logger.info(f"Naciśnięto kombinację klawiszy: {' + '.join(keys)}")

            # Opóźnienie po naciśnięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas naciskania kombinacji klawiszy: {str(e)}")
            return False


class KeyDownAction(BaseAction):
    """
    Akcja wciśnięcia i przytrzymania klawisza.
    """

    ACTION_NAME = "key_down"
    ACTION_DESCRIPTION = "Wciska i przytrzymuje klawisz."

    REQUIRED_PARAMS = {
        "key": str  # Klawisz do wciśnięcia
    }
    OPTIONAL_PARAMS = {
        "delay": (float, 0.1)  # Opóźnienie po wciśnięciu (w sekundach)
    }

    def execute(self) -> bool:
        """
        Wykonuje akcję wciśnięcia i przytrzymania klawisza.

        Returns:
            True jeśli wciśnięcie się powiodło, False w przeciwnym razie
        """
        # Pobranie parametrów
        key = self.get_param("key")
        delay = self.get_param("delay")

        try:
            # Wciśnięcie klawisza
            pyautogui.keyDown(key)
            self.logger.info(f"Wciśnięto klawisz: {key}")

            # Opóźnienie po wciśnięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas wciskania klawisza: {str(e)}")
            return False


class KeyUpAction(BaseAction):
    """
    Akcja zwolnienia wciśniętego klawisza.
    """

    ACTION_NAME = "key_up"
    ACTION_DESCRIPTION = "Zwalnia wciśnięty klawisz."

    REQUIRED_PARAMS = {
        "key": str  # Klawisz do zwolnienia
    }
    OPTIONAL_PARAMS = {
        "delay": (float, 0.1)  # Opóźnienie po zwolnieniu (w sekundach)
    }

    def execute(self) -> bool:
        """
        Wykonuje akcję zwolnienia klawisza.

        Returns:
            True jeśli zwolnienie się powiodło, False w przeciwnym razie
        """
        # Pobranie parametrów
        key = self.get_param("key")
        delay = self.get_param("delay")

        try:
            # Zwolnienie klawisza
            pyautogui.keyUp(key)
            self.logger.info(f"Zwolniono klawisz: {key}")

            # Opóźnienie po zwolnieniu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas zwalniania klawisza: {str(e)}")
            return False


class PasteTextAction(BaseAction):
    """
    Akcja wklejania tekstu ze schowka.
    """

    ACTION_NAME = "paste_text"
    ACTION_DESCRIPTION = "Wkleja tekst ze schowka lub ustawia tekst w schowku i wkleja."

    REQUIRED_PARAMS = {}
    OPTIONAL_PARAMS = {
        "text": (str, None),  # Tekst do ustawienia w schowku przed wklejeniem
        "selector": (str, None),  # Selektor CSS elementu, w który wkleić tekst
        "delay": (float, 0.1)  # Opóźnienie po wklejeniu (w sekundach)
    }

    def execute(self) -> bool:
        """
        Wykonuje akcję wklejania tekstu.

        Returns:
            True jeśli wklejanie się powiodło, False w przeciwnym razie
        """
        # Pobranie parametrów
        text = self.get_param("text")
        selector = self.get_param("selector")
        delay = self.get_param("delay")

        try:
            # Jeśli podano tekst, ustaw go w schowku
            if text is not None:
                import pyperclip
                pyperclip.copy(text)
                self.logger.info(f"Ustawiono tekst w schowku: {text}")

            # Jeśli podano selektor, kliknij w dany element przed wklejaniem
            if selector:
                try:
                    element = pyautogui.locateOnScreen(selector)
                    if element:
                        pyautogui.click(pyautogui.center(element))
                    else:
                        self.logger.error(f"Nie znaleziono elementu z selektorem: {selector}")
                        return False
                except Exception as e:
                    self.logger.error(f"Błąd podczas lokalizacji elementu z selektorem: {str(e)}")
                    return False

            # Wklej tekst (Ctrl+V / Command+V)
            if pyautogui.platform.system() == 'Darwin':  # macOS
                pyautogui.hotkey('command', 'v')
            else:  # Windows/Linux
                pyautogui.hotkey('ctrl', 'v')

            self.logger.info("Wklejono tekst ze schowka")

            # Opóźnienie po wklejeniu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas wklejania tekstu: {str(e)}")
            return False


class CopyTextAction(BaseAction):
    """
    Akcja kopiowania zaznaczonego tekstu do schowka.
    """

    ACTION_NAME = "copy_text"
    ACTION_DESCRIPTION = "Kopiuje zaznaczony tekst do schowka."

    REQUIRED_PARAMS = {}
    OPTIONAL_PARAMS = {
        "selector": (str, None),  # Selektor CSS elementu do zaznaczenia przed kopiowaniem
        "delay": (float, 0.1)  # Opóźnienie po kopiowaniu (w sekundach)
    }

    def execute(self) -> Union[bool, str]:
        """
        Wykonuje akcję kopiowania tekstu.

        Returns:
            Skopiowany tekst jeśli kopiowanie się powiodło, False w przeciwnym razie
        """
        # Pobranie parametrów
        selector = self.get_param("selector")
        delay = self.get_param("delay")

        try:
            # Jeśli podano selektor, kliknij w dany element przed kopiowaniem
            if selector:
                try:
                    element = pyautogui.locateOnScreen(selector)
                    if element:
                        pyautogui.click(pyautogui.center(element))
                        # Zaznacz wszystko (Ctrl+A / Command+A)
                        if pyautogui.platform.system() == 'Darwin':  # macOS
                            pyautogui.hotkey('command', 'a')
                        else:  # Windows/Linux
                            pyautogui.hotkey('ctrl', 'a')
                    else:
                        self.logger.error(f"Nie znaleziono elementu z selektorem: {selector}")
                        return False
                except Exception as e:
                    self.logger.error(f"Błąd podczas lokalizacji elementu z selektorem: {str(e)}")
                    return False

            # Kopiuj zaznaczony tekst (Ctrl+C / Command+C)
            if pyautogui.platform.system() == 'Darwin':  # macOS
                pyautogui.hotkey('command', 'c')
            else:  # Windows/Linux
                pyautogui.hotkey('ctrl', 'c')

            # Opóźnienie po kopiowaniu
            if delay > 0:
                time.sleep(delay)

            # Pobierz tekst ze schowka
            import pyperclip
            copied_text = pyperclip.paste()
            self.logger.info(f"Skopiowano tekst do schowka: {copied_text}")

            return copied_text
        except Exception as e:
            self.logger.error(f"Błąd podczas kopiowania tekstu: {str(e)}")
            return False