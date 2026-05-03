# Wyodrębnianie encji z tekstu
"""
entity_extractor.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ekstraktor encji z tekstu dla automatyzacji.
Wyodrębnia różne typy encji z tekstu, które mogą być używane w akcjach automatyzacji.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Union


class EntityExtractor:
    """
    Ekstraktor encji z tekstu.
    Wykorzystuje wzorce i reguły do wyodrębniania różnych typów encji.
    """

    def __init__(self):
        """
        Inicjalizacja ekstraktora encji.
        """
        self.logger = logging.getLogger(__name__)

    def extract_username(self, text: str) -> Optional[str]:
        """
        Wyekstrahuj nazwę użytkownika z tekstu.

        Args:
            text: Tekst do analizy

        Returns:
            Nazwa użytkownika lub None, jeśli nie znaleziono
        """
        # Wzorce dla nazwy użytkownika
        patterns = [
            r"(?:użytkownik|nazwa użytkownika|login)[\s:]+['\"]?([a-zA-Z0-9@._-]+)['\"]?",
            r"zaloguj się jako ['\"]?([a-zA-Z0-9@._-]+)['\"]?",
            r"z (?:użytkownikiem|nazwą użytkownika|loginem) ['\"]?([a-zA-Z0-9@._-]+)['\"]?"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def extract_password(self, text: str) -> Optional[str]:
        """
        Wyekstrahuj hasło z tekstu.

        Args:
            text: Tekst do analizy

        Returns:
            Hasło lub None, jeśli nie znaleziono
        """
        # Wzorce dla hasła
        patterns = [
            r"(?:hasło|haslem|hasłem)[\s:]+['\"]?([a-zA-Z0-9@._\-!#$%^&*]+)['\"]?",
            r"z (?:hasłem|haslem) ['\"]?([a-zA-Z0-9@._\-!#$%^&*]+)['\"]?"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def extract_subject_filter(self, text: str) -> Optional[str]:
        """
        Wyekstrahuj filtr tematu dla wiadomości email.

        Args:
            text: Tekst do analizy

        Returns:
            Filtr tematu lub None, jeśli nie znaleziono
        """
        # Wzorce dla filtra tematu
        patterns = [
            r"temat(?:em|em)? ['\"]([^'\"]+)['\"]",
            r"z temat(?:em|em)? ['\"]([^'\"]+)['\"]",
            r"o temacie ['\"]([^'\"]+)['\"]"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def extract_email_count(self, text: str) -> Optional[int]:
        """
        Wyekstrahuj liczbę wiadomości email do pobrania.

        Args:
            text: Tekst do analizy

        Returns:
            Liczba wiadomości lub None, jeśli nie znaleziono
        """
        # Wzorce dla liczby wiadomości
        patterns = [
            r"pobierz (\d+) (?:wiadomości|emaile|maile)",
            r"ostatni(?:e|ch)? (\d+) (?:wiadomości|emaile|maile)",
            r"maksymalnie (\d+) (?:wiadomości|emaile|maile)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        # Jeśli text zawiera "ostatnią wiadomość" lub podobne, zwróć 1
        if re.search(r"ostatni(?:a|ą)? wiadomoś(?:ć|c)", text, re.IGNORECASE):
            return 1

        return None

    def extract_click_type(self, text: str) -> Optional[str]:
        """
        Wyekstrahuj typ kliknięcia (pojedyncze, podwójne, prawy przycisk).

        Args:
            text: Tekst do analizy

        Returns:
            Typ kliknięcia ("single", "double", "right") lub None, jeśli nie znaleziono
        """
        if re.search(r"podwójn(?:ie|e|ym|o)|dwukrotnie", text, re.IGNORECASE):
            return "double"
        elif re.search(r"praw(?:ym|y|ego) (?:przyciskiem|klawiszem)", text, re.IGNORECASE):
            return "right"
        elif re.search(r"kliknij|naciśnij|klik", text, re.IGNORECASE):
            return "single"

        return None

    def extract_coordinates(self, text: str) -> Optional[Tuple[int, int]]:
        """
        Wyekstrahuj współrzędne (x, y) dla akcji myszy.

        Args:
            text: Tekst do analizy

        Returns:
            Krotka (x, y) lub None, jeśli nie znaleziono
        """
        # Wzorce dla współrzędnych
        patterns = [
            r"(?:w|na) (?:pozycji|współrzędnych|koordynatach|punkcie) ?\((\d+)[,\s]+(\d+)\)",
            r"(?:w|na) (?:pozycji|współrzędnych|koordynatach|punkcie) (\d+)[,\s]+(\d+)",
            r"x=(\d+)[,\s]+y=(\d+)",
            r"x:(\d+)[,\s]+y:(\d+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    x = int(match.group(1))
                    y = int(match.group(2))
                    return (x, y)
                except ValueError:
                    continue

        return None

    def extract_wait_time(self, text: str) -> Optional[float]:
        """
        Wyekstrahuj czas oczekiwania (w sekundach).

        Args:
            text: Tekst do analizy

        Returns:
            Czas oczekiwania (w sekundach) lub None, jeśli nie znaleziono
        """
        # Wzorce dla czasu oczekiwania
        patterns = [
            r"(?:czekaj|poczekaj|odczekaj)(?: przez)? (\d+(?:\.\d+)?) (?:sekund(?:y|ę)?|s)",
            r"czekanie (?:przez )?(\d+(?:\.\d+)?) (?:sekund(?:y|ę)?|s)",
            r"(?:opóźnienie|timeout|delay)(?: przez | wynoszące | równe )?(\d+(?:\.\d+)?) (?:sekund(?:y|ę)?|s)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def extract_text_to_type(self, text: str) -> Optional[str]:
        """
        Wyekstrahuj tekst do wpisania.

        Args:
            text: Tekst do analizy

        Returns:
            Tekst do wpisania lub None, jeśli nie znaleziono
        """
        # Wzorce dla tekstu do wpisania
        patterns = [
            r"(?:wpisz|wprowadź|napisz)(?: tekst)? ['\"]([^'\"]+)['\"]",
            r"(?:wpisz|wprowadź|napisz)(?: tekst)? (.+?)(?:\s|$)",
            r"tekst (?:do (?:wpisania|wprowadzenia))? ['\"]([^'\"]+)['\"]"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def extract_key_combination(self, text: str) -> Optional[List[str]]:
        """
        Wyekstrahuj kombinację klawiszy.

        Args:
            text: Tekst do analizy

        Returns:
            Lista klawiszy lub None, jeśli nie znaleziono
        """
        # Mapowanie polskich nazw klawiszy na nazwy używane przez pyautogui
        key_mapping = {
            "ctrl": "ctrl", "control": "ctrl", "kontrola": "ctrl",
            "alt": "alt", "option": "alt", "opcje": "alt",
            "shift": "shift", "przesunięcie": "shift",
            "win": "win", "windows": "win", "okna": "win",
            "enter": "enter", "return": "enter", "zatwierdź": "enter",
            "esc": "esc", "escape": "esc", "ucieknij": "esc",
            "tab": "tab", "tabulator": "tab",
            "del": "delete", "delete": "delete", "usuń": "delete",
            # można dodać więcej mapowań
        }

        # Wzorce dla kombinacji klawiszy
        patterns = [
            r"(?:naciśnij|wciśnij|użyj|użycie) (?:kombinacji )?(.+?)(?:\s|$)",
            r"(?:kombinacja klawiszy|klawisze|skrót) (.+?)(?:\s|$)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                keys_text = match.group(1)

                # Rozdziel klawisze (mogą być rozdzielone znakami +, -, ,, spacja)
                keys = re.split(r'[+\-,\s]+', keys_text)

                # Mapuj nazwy klawiszy
                mapped_keys = []
                for key in keys:
                    key = key.lower()
                    if key in key_mapping:
                        mapped_keys.append(key_mapping[key])
                    else:
                        mapped_keys.append(key)

                if mapped_keys:
                    return mapped_keys

        return None

    def extract_regex_pattern(self, text: str) -> Optional[str]:
        """
        Wyekstrahuj wzorzec wyrażenia regularnego.

        Args:
            text: Tekst do analizy

        Returns:
            Wzorzec regex lub None, jeśli nie znaleziono
        """
        # Wzorce dla wzorca regex
        patterns = [
            r"wyrażenie(?:m)? (?:regularnym|regularnym) ['\"]([^'\"]+)['\"]",
            r"regex(?:em)? ['\"]([^'\"]+)['\"]",
            r"(?:wzorcem|wzorzec|pattern(?:em)?|wzór) ['\"]([^'\"]+)['\"]"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def extract_action_parameters(self, text: str, action_type: str) -> Dict[str, Any]:
        """
        Wyekstrahuj wszystkie parametry dla danego typu akcji.

        Args:
            text: Tekst do analizy
            action_type: Typ akcji

        Returns:
            Słownik z parametrami
        """
        params = {}

        if action_type == "open_application":
            app_name = re.search(
                r"(?:otworz|otwórz|uruchom|włącz|wlacz)(?:aplikacje|aplikację|program)(?: o nazwie)? (\w+)", text,
                re.IGNORECASE)
            if app_name:
                params["name"] = app_name.group(1)

        elif action_type == "login_to_website":
            website = re.search(r"(?:zaloguj|wejdź)(?:[^\w]+)(?:do|na)(?:[^\w]+)(\w+)", text, re.IGNORECASE)
            if website:
                params["website"] = website.group(1)

            username = self.extract_username(text)
            if username:
                params["username"] = username

            password = self.extract_password(text)
            if password:
                params["password"] = password

        elif action_type == "get_email":
            email_addr = re.search(r"skrzynki ([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text, re.IGNORECASE)
            if email_addr:
                params["email_address"] = email_addr.group(1)

            subject = self.extract_subject_filter(text)
            if subject:
                params["subject_filter"] = subject

            count = self.extract_email_count(text)
            if count:
                params["max_emails"] = count
            else:
                params["max_emails"] = 1  # Domyślnie 1 wiadomość

        elif action_type == "click":
            click_type = self.extract_click_type(text)
            if click_type:
                params["click_type"] = click_type

            coords = self.extract_coordinates(text)
            if coords:
                params["x"] = coords[0]
                params["y"] = coords[1]

            target = re.search(r"(?:kliknij|naciśnij)(?: w| na)? (.+?)(?:\s|$)", text, re.IGNORECASE)
            if target and not coords:
                params["target"] = target.group(1)

        elif action_type == "type_text":
            text_to_type = self.extract_text_to_type(text)
            if text_to_type:
                params["text"] = text_to_type

        elif action_type == "wait":
            wait_time = self.extract_wait_time(text)
            if wait_time:
                params["seconds"] = wait_time

        elif action_type == "shell_command":
            command = re.search(r"(?:wykonaj|uruchom) komendę ['\"]([^'\"]+)['\"]", text, re.IGNORECASE)
            if command:
                params["command"] = command.group(1)

        elif action_type == "find_on_screen":
            image = re.search(r"(?:znajdź|poszukaj) na ekranie(?: obraz)? ['\"]([^'\"]+)['\"]", text, re.IGNORECASE)
            if image:
                params["image"] = image.group(1)

            confidence = re.search(
                r"(?:z|ze) (?:pewnością|pewnoscia|dokładnością|dokladnoscia|confidence) (\d+(?:\.\d+)?)", text,
                re.IGNORECASE)
            if confidence:
                try:
                    params["confidence"] = float(confidence.group(1))
                except ValueError:
                    pass

        return params