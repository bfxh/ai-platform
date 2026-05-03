# Narzędzia do pracy z obrazami
"""
image_utils.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Narzędzia do pracy z obrazami dla automatyzacji.
"""

import os
import logging
import tempfile
from typing import Optional, Tuple, Union, List

import cv2
import numpy as np
from PIL import Image, ImageGrab

# Konfiguracja loggera
logger = logging.getLogger(__name__)


def find_image_on_screen(image_path: str, confidence: float = 0.8, region: Tuple[int, int, int, int] = None) -> \
Optional[Tuple[int, int]]:
    """
    Znajduje obraz na ekranie.

    Args:
        image_path: Ścieżka do pliku obrazu do znalezienia
        confidence: Poziom pewności dopasowania (0.0 - 1.0)
        region: Region ekranu do przeszukania (x, y, width, height)

    Returns:
        Krotka (x, y) z pozycją środka znalezionego obrazu lub None, jeśli nie znaleziono
    """
    try:
        # Sprawdź czy plik istnieje
        if not os.path.exists(image_path):
            logger.error(f"Plik obrazu nie istnieje: {image_path}")
            return None

        # Zrzut ekranu
        screenshot = ImageGrab.grab(bbox=region)
        screenshot_np = np.array(screenshot)

        # Konwersja z RGB do BGR (cv2 używa BGR)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        # Wczytaj obraz wzorcowy
        template = cv2.imread(image_path)

        # Sprawdź czy obraz wzorcowy został poprawnie wczytany
        if template is None:
            logger.error(f"Nie udało się wczytać obrazu: {image_path}")
            return None

        # Pobierz wymiary szablonu
        template_height, template_width = template.shape[:2]

        # Wykonaj dopasowanie szablonu
        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)

        # Znajdź położenie najlepszego dopasowania
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Sprawdź czy poziom pewności jest wystarczający
        if max_val >= confidence:
            # Oblicz środek znalezionego obrazu
            x = max_loc[0] + template_width // 2
            y = max_loc[1] + template_height // 2

            # Jeśli podano region, dodaj jego początek do współrzędnych
            if region:
                x += region[0]
                y += region[1]

            logger.info(f"Znaleziono obraz '{image_path}' na pozycji ({x}, {y}) z pewnością {max_val:.2f}")
            return (x, y)
        else:
            logger.debug(
                f"Nie znaleziono obrazu '{image_path}' z wymaganą pewnością (max_val={max_val:.2f}, wymagane={confidence:.2f})")
            return None
    except Exception as e:
        logger.error(f"Błąd podczas wyszukiwania obrazu na ekranie: {str(e)}")
        return None


def find_all_on_screen(image_path: str, confidence: float = 0.8, region: Tuple[int, int, int, int] = None) -> List[
    Tuple[int, int]]:
    """
    Znajduje wszystkie wystąpienia obrazu na ekranie.

    Args:
        image_path: Ścieżka do pliku obrazu do znalezienia
        confidence: Poziom pewności dopasowania (0.0 - 1.0)
        region: Region ekranu do przeszukania (x, y, width, height)

    Returns:
        Lista krotek (x, y) z pozycjami środków znalezionych obrazów
    """
    try:
        # Sprawdź czy plik istnieje
        if not os.path.exists(image_path):
            logger.error(f"Plik obrazu nie istnieje: {image_path}")
            return []

        # Zrzut ekranu
        screenshot = ImageGrab.grab(bbox=region)
        screenshot_np = np.array(screenshot)

        # Konwersja z RGB do BGR (cv2 używa BGR)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        # Wczytaj obraz wzorcowy
        template = cv2.imread(image_path)

        # Sprawdź czy obraz wzorcowy został poprawnie wczytany
        if template is None:
            logger.error(f"Nie udało się wczytać obrazu: {image_path}")
            return []

        # Pobierz wymiary szablonu
        template_height, template_width = template.shape[:2]

        # Wykonaj dopasowanie szablonu
        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)

        # Znajdź wszystkie dopasowania powyżej progu pewności
        locations = np.where(result >= confidence)
        positions = []

        # Konwersja do użytecznych współrzędnych
        for pt in zip(*locations[::-1]):
            # Oblicz środek znalezionego obrazu
            x = pt[0] + template_width // 2
            y = pt[1] + template_height // 2

            # Jeśli podano region, dodaj jego początek do współrzędnych
            if region:
                x += region[0]
                y += region[1]

            positions.append((x, y))

        # Usuń duplikaty (gdy wykrycie jest bardzo blisko innego)
        filtered_positions = []
        for pos in positions:
            # Sprawdź czy podobna pozycja już istnieje
            if not any(abs(pos[0] - p[0]) < 10 and abs(pos[1] - p[1]) < 10 for p in filtered_positions):
                filtered_positions.append(pos)

        logger.info(f"Znaleziono {len(filtered_positions)} wystąpień obrazu '{image_path}'")
        return filtered_positions
    except Exception as e:
        logger.error(f"Błąd podczas wyszukiwania obrazów na ekranie: {str(e)}")
        return []


def take_screenshot(output_path: Optional[str] = None, region: Tuple[int, int, int, int] = None) -> Optional[str]:
    """
    Wykonuje zrzut ekranu i zapisuje go do pliku.

    Args:
        output_path: Ścieżka do pliku wyjściowego (opcjonalnie)
        region: Region ekranu do zrzutu (x, y, width, height)

    Returns:
        Ścieżka do zapisanego pliku lub None w przypadku błędu
    """
    try:
        # Wykonaj zrzut ekranu
        screenshot = ImageGrab.grab(bbox=region)

        # Jeśli nie podano ścieżki, utwórz plik tymczasowy
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix='.png')
            os.close(fd)

        # Zapisz zrzut ekranu
        screenshot.save(output_path)
        logger.info(f"Zapisano zrzut ekranu do pliku: {output_path}")

        return output_path
    except Exception as e:
        logger.error(f"Błąd podczas wykonywania zrzutu ekranu: {str(e)}")
        return None


def compare_images(image1_path: str, image2_path: str) -> float:
    """
    Porównuje dwa obrazy i zwraca poziom podobieństwa.

    Args:
        image1_path: Ścieżka do pierwszego obrazu
        image2_path: Ścieżka do drugiego obrazu

    Returns:
        Poziom podobieństwa (0.0 - 1.0) gdzie 1.0 oznacza identyczne obrazy
    """
    try:
        # Wczytaj obrazy
        img1 = cv2.imread(image1_path)
        img2 = cv2.imread(image2_path)

        # Sprawdź czy obrazy zostały poprawnie wczytane
        if img1 is None or img2 is None:
            logger.error(f"Nie udało się wczytać obrazów: {image1_path}, {image2_path}")
            return 0.0

        # Dopasuj rozmiary obrazów
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        # Konwersja na skalę szarości
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # Oblicz współczynnik korelacji
        similarity = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)[0][0]

        logger.info(f"Podobieństwo obrazów: {similarity:.2f}")
        return float(similarity)
    except Exception as e:
        logger.error(f"Błąd podczas porównywania obrazów: {str(e)}")
        return 0.0