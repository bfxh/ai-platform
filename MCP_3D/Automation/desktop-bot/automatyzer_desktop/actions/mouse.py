# Akcje myszy
"""
mouse.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implementacja akcji związanych z myszą.
"""

import time
import logging
from typing import Any, Dict, Optional, Tuple, Union
import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab, Image

from automatyzer_desktop.actions.base import BaseAction
from automatyzer_desktop.utils.image_utils import find_image_on_screen


class ClickAction(BaseAction):
    """
    Akcja kliknięcia lewym przyciskiem myszy.
    """

    ACTION_NAME = "click"
    ACTION_DESCRIPTION = "Klika lewym przyciskiem myszy w określonym miejscu lub na znalezionym obrazie."

    REQUIRED_PARAMS = {}
    OPTIONAL_PARAMS = {
        "x": (int, None),  # Współrzędna X
        "y": (int, None),  # Współrzędna Y
        "image": (str, None),  # Ścieżka do obrazu
        "selector": (str, None),  # Selektor CSS (dla aplikacji webowych)
        "confidence": (float, 0.8),  # Pewność dopasowania obrazu (0.0 - 1.0)
        "duration": (float, 0.1),  # Czas ruchu myszy (w sekundach)
        "delay": (float, 0.1)  # Opóźnienie po kliknięciu (w sekundach)
    }

    def validate(self) -> bool:
        """
        Sprawdza czy parametry akcji są poprawne.

        Returns:
            True jeśli parametry są poprawne, False w przeciwnym razie
        """
        # Musi być podane x,y LUB image LUB selector
        has_coords = self.get_param("x") is not None and self.get_param("y") is not None
        has_image = self.get_param("image") is not None
        has_selector = self.get_param("selector") is not None

        return has_coords or has_image or has_selector

    def execute(self) -> bool:
        """
        Wykonuje akcję kliknięcia.

        Returns:
            True jeśli kliknięcie się powiodło, False w przeciwnym razie
        """
        # Sprawdzenie parametrów
        if not self.validate():
            self.logger.error("Brak wymaganych parametrów. Podaj współrzędne (x, y) lub obraz lub selektor.")
            return False

        # Pobranie parametrów
        x = self.get_param("x")
        y = self.get_param("y")
        image = self.get_param("image")
        selector = self.get_param("selector")
        confidence = self.get_param("confidence")
        duration = self.get_param("duration")
        delay = self.get_param("delay")

        # Jeśli podano selektor CSS, użyj go (dla przeglądarek)
        if selector:
            try:
                # Sprawdź czy przeglądarki wspierają selectory (użyj pyautogui)
                element = pyautogui.locateOnScreen(selector)
                if element:
                    x, y = pyautogui.center(element)
                else:
                    self.logger.error(f"Nie znaleziono elementu z selektorem: {selector}")
                    return False
            except Exception as e:
                self.logger.error(f"Błąd podczas lokalizacji elementu z selektorem: {str(e)}")
                return False

        # Jeśli podano obraz, znajdź go na ekranie
        elif image:
            try:
                position = find_image_on_screen(image, confidence=confidence)
                if position:
                    x, y = position
                else:
                    self.logger.error(f"Nie znaleziono obrazu: {image}")
                    return False
            except Exception as e:
                self.logger.error(f"Błąd podczas wyszukiwania obrazu: {str(e)}")
                return False

        # Wykonaj kliknięcie
        try:
            # Przesuń kursor
            pyautogui.moveTo(x, y, duration=duration)
            # Kliknij
            pyautogui.click(x, y)
            self.logger.info(f"Kliknięto w pozycji ({x}, {y})")

            # Opóźnienie po kliknięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas kliknięcia: {str(e)}")
            return False


class RightClickAction(BaseAction):
    """
    Akcja kliknięcia prawym przyciskiem myszy.
    """

    ACTION_NAME = "right_click"
    ACTION_DESCRIPTION = "Klika prawym przyciskiem myszy w określonym miejscu lub na znalezionym obrazie."

    REQUIRED_PARAMS = {}
    OPTIONAL_PARAMS = {
        "x": (int, None),  # Współrzędna X
        "y": (int, None),  # Współrzędna Y
        "image": (str, None),  # Ścieżka do obrazu
        "selector": (str, None),  # Selektor CSS (dla aplikacji webowych)
        "confidence": (float, 0.8),  # Pewność dopasowania obrazu (0.0 - 1.0)
        "duration": (float, 0.1),  # Czas ruchu myszy (w sekundach)
        "delay": (float, 0.1)  # Opóźnienie po kliknięciu (w sekundach)
    }

    def validate(self) -> bool:
        """
        Sprawdza czy parametry akcji są poprawne.

        Returns:
            True jeśli parametry są poprawne, False w przeciwnym razie
        """
        # Musi być podane x,y LUB image LUB selector
        has_coords = self.get_param("x") is not None and self.get_param("y") is not None
        has_image = self.get_param("image") is not None
        has_selector = self.get_param("selector") is not None

        return has_coords or has_image or has_selector

    def execute(self) -> bool:
        """
        Wykonuje akcję kliknięcia prawym przyciskiem.

        Returns:
            True jeśli kliknięcie się powiodło, False w przeciwnym razie
        """
        # Sprawdzenie parametrów
        if not self.validate():
            self.logger.error("Brak wymaganych parametrów. Podaj współrzędne (x, y) lub obraz lub selektor.")
            return False

        # Pobranie parametrów
        x = self.get_param("x")
        y = self.get_param("y")
        image = self.get_param("image")
        selector = self.get_param("selector")
        confidence = self.get_param("confidence")
        duration = self.get_param("duration")
        delay = self.get_param("delay")

        # Jeśli podano selektor CSS, użyj go (dla przeglądarek)
        if selector:
            try:
                element = pyautogui.locateOnScreen(selector)
                if element:
                    x, y = pyautogui.center(element)
                else:
                    self.logger.error(f"Nie znaleziono elementu z selektorem: {selector}")
                    return False
            except Exception as e:
                self.logger.error(f"Błąd podczas lokalizacji elementu z selektorem: {str(e)}")
                return False

        # Jeśli podano obraz, znajdź go na ekranie
        elif image:
            try:
                position = find_image_on_screen(image, confidence=confidence)
                if position:
                    x, y = position
                else:
                    self.logger.error(f"Nie znaleziono obrazu: {image}")
                    return False
            except Exception as e:
                self.logger.error(f"Błąd podczas wyszukiwania obrazu: {str(e)}")
                return False

        # Wykonaj kliknięcie prawym przyciskiem
        try:
            # Przesuń kursor
            pyautogui.moveTo(x, y, duration=duration)
            # Kliknij prawym przyciskiem
            pyautogui.rightClick(x, y)
            self.logger.info(f"Kliknięto prawym przyciskiem w pozycji ({x}, {y})")

            # Opóźnienie po kliknięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas kliknięcia prawym przyciskiem: {str(e)}")
            return False


class DoubleClickAction(BaseAction):
    """
    Akcja podwójnego kliknięcia lewym przyciskiem myszy.
    """

    ACTION_NAME = "double_click"
    ACTION_DESCRIPTION = "Podwójnie klika lewym przyciskiem myszy w określonym miejscu lub na znalezionym obrazie."

    REQUIRED_PARAMS = {}
    OPTIONAL_PARAMS = {
        "x": (int, None),  # Współrzędna X
        "y": (int, None),  # Współrzędna Y
        "image": (str, None),  # Ścieżka do obrazu
        "selector": (str, None),  # Selektor CSS (dla aplikacji webowych)
        "confidence": (float, 0.8),  # Pewność dopasowania obrazu (0.0 - 1.0)
        "duration": (float, 0.1),  # Czas ruchu myszy (w sekundach)
        "delay": (float, 0.1)  # Opóźnienie po kliknięciu (w sekundach)
    }

    def validate(self) -> bool:
        """
        Sprawdza czy parametry akcji są poprawne.

        Returns:
            True jeśli parametry są poprawne, False w przeciwnym razie
        """
        # Musi być podane x,y LUB image LUB selector
        has_coords = self.get_param("x") is not None and self.get_param("y") is not None
        has_image = self.get_param("image") is not None
        has_selector = self.get_param("selector") is not None

        return has_coords or has_image or has_selector

    def execute(self) -> bool:
        """
        Wykonuje akcję podwójnego kliknięcia.

        Returns:
            True jeśli kliknięcie się powiodło, False w przeciwnym razie
        """
        # Sprawdzenie parametrów
        if not self.validate():
            self.logger.error("Brak wymaganych parametrów. Podaj współrzędne (x, y) lub obraz lub selektor.")
            return False

        # Pobranie parametrów
        x = self.get_param("x")
        y = self.get_param("y")
        image = self.get_param("image")
        selector = self.get_param("selector")
        confidence = self.get_param("confidence")
        duration = self.get_param("duration")
        delay = self.get_param("delay")

        # Jeśli podano selektor CSS, użyj go (dla przeglądarek)
        if selector:
            try:
                element = pyautogui.locateOnScreen(selector)
                if element:
                    x, y = pyautogui.center(element)
                else:
                    self.logger.error(f"Nie znaleziono elementu z selektorem: {selector}")
                    return False
            except Exception as e:
                self.logger.error(f"Błąd podczas lokalizacji elementu z selektorem: {str(e)}")
                return False

        # Jeśli podano obraz, znajdź go na ekranie
        elif image:
            try:
                position = find_image_on_screen(image, confidence=confidence)
                if position:
                    x, y = position
                else:
                    self.logger.error(f"Nie znaleziono obrazu: {image}")
                    return False
            except Exception as e:
                self.logger.error(f"Błąd podczas wyszukiwania obrazu: {str(e)}")
                return False

        # Wykonaj podwójne kliknięcie
        try:
            # Przesuń kursor
            pyautogui.moveTo(x, y, duration=duration)
            # Podwójne kliknięcie
            pyautogui.doubleClick(x, y)
            self.logger.info(f"Podwójnie kliknięto w pozycji ({x}, {y})")

            # Opóźnienie po kliknięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas podwójnego kliknięcia: {str(e)}")
            return False


class DragAction(BaseAction):
    """
    Akcja przeciągnięcia myszą (drag and drop).
    """

    ACTION_NAME = "drag"
    ACTION_DESCRIPTION = "Przeciąga myszą z jednej pozycji do drugiej."

    REQUIRED_PARAMS = {
        "x1": int,  # Początkowa współrzędna X
        "y1": int,  # Początkowa współrzędna Y
        "x2": int,  # Końcowa współrzędna X
        "y2": int  # Końcowa współrzędna Y
    }
    OPTIONAL_PARAMS = {
        "duration": (float, 0.5),  # Czas trwania przeciągnięcia (w sekundach)
        "delay": (float, 0.1)  # Opóźnienie po przeciągnięciu (w sekundach)
    }

    def execute(self) -> bool:
        """
        Wykonuje akcję przeciągnięcia.

        Returns:
            True jeśli przeciągnięcie się powiodło, False w przeciwnym razie
        """
        # Pobranie parametrów
        x1 = self.get_param("x1")
        y1 = self.get_param("y1")
        x2 = self.get_param("x2")
        y2 = self.get_param("y2")
        duration = self.get_param("duration")
        delay = self.get_param("delay")

        try:
            # Przesuń kursor na pozycję początkową
            pyautogui.moveTo(x1, y1)
            # Przeciągnij na pozycję końcową
            pyautogui.dragTo(x2, y2, duration=duration, button='left')
            self.logger.info(f"Przeciągnięto z ({x1}, {y1}) do ({x2}, {y2})")

            # Opóźnienie po przeciągnięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas przeciągnięcia: {str(e)}")
            return False


class ScrollAction(BaseAction):
    """
    Akcja przewijania (scroll).
    """

    ACTION_NAME = "scroll"
    ACTION_DESCRIPTION = "Przewija w górę lub w dół strony."

    REQUIRED_PARAMS = {
        "clicks": int  # Liczba kliknięć przewijania (dodatnia - w dół, ujemna - w górę)
    }
    OPTIONAL_PARAMS = {
        "x": (int, None),  # Współrzędna X (jeśli None, to aktualna pozycja)
        "y": (int, None),  # Współrzędna Y (jeśli None, to aktualna pozycja)
        "delay": (float, 0.1)  # Opóźnienie po przewinięciu (w sekundach)
    }

    def execute(self) -> bool:
        """
        Wykonuje akcję przewijania.

        Returns:
            True jeśli przewijanie się powiodło, False w przeciwnym razie
        """
        # Pobranie parametrów
        clicks = self.get_param("clicks")
        x = self.get_param("x")
        y = self.get_param("y")
        delay = self.get_param("delay")

        try:
            # Jeśli podano współrzędne, przesuń kursor
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)

            # Przewiń
            pyautogui.scroll(clicks)
            direction = "dół" if clicks < 0 else "górę"
            self.logger.info(f"Przewinięto w {direction} o {abs(clicks)} kliknięć")

            # Opóźnienie po przewinięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas przewijania: {str(e)}")
            return False


class MoveToAction(BaseAction):
    """
    Akcja przesunięcia kursora myszy.
    """

    ACTION_NAME = "move_to"
    ACTION_DESCRIPTION = "Przesuwa kursor myszy na określoną pozycję."

    REQUIRED_PARAMS = {}
    OPTIONAL_PARAMS = {
        "x": (int, None),  # Współrzędna X
        "y": (int, None),  # Współrzędna Y
        "image": (str, None),  # Ścieżka do obrazu
        "selector": (str, None),  # Selektor CSS (dla aplikacji webowych)
        "confidence": (float, 0.8),  # Pewność dopasowania obrazu (0.0 - 1.0)
        "duration": (float, 0.1),  # Czas ruchu myszy (w sekundach)
        "delay": (float, 0.1)  # Opóźnienie po ruchu (w sekundach)
    }

    def validate(self) -> bool:
        """
        Sprawdza czy parametry akcji są poprawne.

        Returns:
            True jeśli parametry są poprawne, False w przeciwnym razie
        """
        # Musi być podane x,y LUB image LUB selector
        has_coords = self.get_param("x") is not None and self.get_param("y") is not None
        has_image = self.get_param("image") is not None
        has_selector = self.get_param("selector") is not None

        return has_coords or has_image or has_selector

    def execute(self) -> bool:
        """
        Wykonuje akcję przesunięcia kursora.

        Returns:
            True jeśli przesunięcie się powiodło, False w przeciwnym razie
        """
        # Sprawdzenie parametrów
        if not self.validate():
            self.logger.error("Brak wymaganych parametrów. Podaj współrzędne (x, y) lub obraz lub selektor.")
            return False

        # Pobranie parametrów
        x = self.get_param("x")
        y = self.get_param("y")
        image = self.get_param("image")
        selector = self.get_param("selector")
        confidence = self.get_param("confidence")
        duration = self.get_param("duration")
        delay = self.get_param("delay")

        # Jeśli podano selektor CSS, użyj go (dla przeglądarek)
        if selector:
            try:
                element = pyautogui.locateOnScreen(selector)
                if element:
                    x, y = pyautogui.center(element)
                else:
                    self.logger.error(f"Nie znaleziono elementu z selektorem: {selector}")
                    return False
            except Exception as e:
                self.logger.error(f"Błąd podczas lokalizacji elementu z selektorem: {str(e)}")
                return False

        # Jeśli podano obraz, znajdź go na ekranie
        elif image:
            try:
                position = find_image_on_screen(image, confidence=confidence)
                if position:
                    x, y = position
                else:
                    self.logger.error(f"Nie znaleziono obrazu: {image}")
                    return False
            except Exception as e:
                self.logger.error(f"Błąd podczas wyszukiwania obrazu: {str(e)}")
                return False

        # Przesuń kursor
        try:
            pyautogui.moveTo(x, y, duration=duration)
            self.logger.info(f"Przesunięto kursor na pozycję ({x}, {y})")

            # Opóźnienie po ruchu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas przesuwania kursora: {str(e)}")
            return False


class ScreenContainsAction(BaseAction):
    """
    Akcja sprawdzająca czy ekran zawiera określony obraz.
    """

    ACTION_NAME = "screen_contains"
    ACTION_DESCRIPTION = "Sprawdza czy ekran zawiera określony obraz."

    REQUIRED_PARAMS = {
        "image": str  # Ścieżka do obrazu
    }
    OPTIONAL_PARAMS = {
        "confidence": (float, 0.8),  # Pewność dopasowania obrazu (0.0 - 1.0)
        "return_position": (bool, False)  # Czy zwrócić pozycję znalezionego obrazu
    }

    def execute(self) -> Union[bool, Tuple[bool, Tuple[int, int]]]:
        """
        Wykonuje akcję sprawdzenia obecności obrazu na ekranie.

        Returns:
            True jeśli obraz znaleziono, False w przeciwnym przypadku lub
            krotka (True, (x, y)) jeśli return_position=True
        """
        # Pobranie parametrów
        image = self.get_param("image")
        confidence = self.get_param("confidence")
        return_position = self.get_param("return_position")

        try:
            position = find_image_on_screen(image, confidence=confidence)

            if position:
                self.logger.info(f"Znaleziono obraz {image} na pozycji {position}")
                if return_position:
                    return position
                return True
            else:
                self.logger.info(f"Nie znaleziono obrazu {image} na ekranie")
                return False
        except Exception as e:
            self.logger.error(f"Błąd podczas wyszukiwania obrazu: {str(e)}")
            return False