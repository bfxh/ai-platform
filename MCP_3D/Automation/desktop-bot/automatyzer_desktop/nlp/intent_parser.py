# Rozpoznawanie intencji z tekstu
"""
intent_parser.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parser intencji z języka naturalnego dla automatyzacji.
Przekształca polecenia wydane w języku naturalnym na strukturę intencji.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from automatyzer_desktop.nlp.entity_extractor import EntityExtractor


class IntentData:
    """
    Struktura danych reprezentująca intencję użytkownika oraz wyekstrahowane encje.
    """

    def __init__(self, intent_type: str, confidence: float = 1.0):
        """
        Inicjalizacja danych intencji.

        Args:
            intent_type: Typ intencji (np. "open_application", "login_to_website")
            confidence: Pewność rozpoznania intencji (0.0 - 1.0)
        """
        self.intent_type = intent_type
        self.confidence = confidence
        self.entities = {}  # Słownik encji (nazwa -> wartość)

    def add_entity(self, name: str, value: Any) -> None:
        """
        Dodaje encję do intencji.

        Args:
            name: Nazwa encji
            value: Wartość encji
        """
        self.entities[name] = value

    def get_entity(self, name: str, default: Any = None) -> Any:
        """
        Pobiera wartość encji.

        Args:
            name: Nazwa encji
            default: Wartość domyślna, jeśli encja nie istnieje

        Returns:
            Wartość encji lub wartość domyślna
        """
        return self.entities.get(name, default)

    def has_entity(self, name: str) -> bool:
        """
        Sprawdza czy encja istnieje.

        Args:
            name: Nazwa encji

        Returns:
            True, jeśli encja istnieje, False w przeciwnym razie
        """
        return name in self.entities

    def __str__(self) -> str:
        """
        Zwraca tekstową reprezentację intencji.

        Returns:
            Tekstowa reprezentacja intencji
        """
        entities_str = ", ".join(f"{k}={v}" for k, v in self.entities.items())
        return f"Intent({self.intent_type}, confidence={self.confidence}, entities=[{entities_str}])"


class IntentParser:
    """
    Parser intencji z języka naturalnego.
    Wykorzystuje modele NLP do rozpoznawania intencji i encji.
    """

    # Definicje wzorców intencji (regex)
    INTENT_PATTERNS = [
        # Otwieranie aplikacji
        (r"otworz (?:aplikacje|program|aplikację|program)(?: o nazwie)? (\w+)", "open_application"),
        (r"uruchom (?:aplikacje|program|aplikację|program)(?: o nazwie)? (\w+)", "open_application"),
        (r"włącz (?:aplikacje|program|aplikację|program)(?: o nazwie)? (\w+)", "open_application"),

        # Logowanie do strony
        (r"zaloguj (?:sie|się) do (?:portalu|strony|serwisu) (\w+)", "login_to_website"),
        (r"wejdź na (?:stronę|portal|serwis) (\w+)(?: i zaloguj się)?", "login_to_website"),

        # Pobieranie emaila
        (r"pobierz (?:z programu pocztowego )?ze skrzynki ([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+) ostatni(?:a|ą)? wiadomos(?:c|ć)",
         "get_email"),
        (r"sprawdź (?:wiadomości|emaile|maile) (?:z|od|ze) ([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
         "get_email"),

        # Kliknięcie
        (r"kliknij(?: w)? (.+)", "click"),
        (r"naciśnij(?: przycisk)? (.+)", "click"),

        # Wpisywanie tekstu
        (r"wpisz (?:tekst )?['\"](.+)['\"]", "type_text"),
        (r"wprowadź (?:tekst )?['\"](.+)['\"]", "type_text"),

        # Czekanie
        (r"czekaj(?: przez)? (\d+)(?: sekund(?:y)?)?", "wait"),
        (r"poczekaj(?: przez)? (\d+)(?: sekund(?:y)?)?", "wait"),

        # Wykonywanie komendy powłoki
        (r"wykonaj komendę ['\"](.+)['\"]", "shell_command"),
        (r"uruchom komendę ['\"](.+)['\"]", "shell_command"),

        # Przeszukiwanie ekranu
        (r"znajdź na ekranie(?: obraz)? ['\"](.+)['\"]", "find_on_screen"),
        (r"poszukaj na ekranie(?: obrazu)? ['\"](.+)['\"]", "find_on_screen"),
    ]

    def __init__(self):
        """
        Inicjalizacja parsera intencji.
        """
        self.logger = logging.getLogger(__name__)

        # Wczytanie modelu NLP (spaCy)
        try:
            self.nlp = spacy.load("pl_core_news_sm")
        except:
            self.logger.warning("Nie można załadować modelu pl_core_news_sm. Używanie modelu en_core_web_sm.")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                self.logger.error("Nie można załadować modelu spaCy. Funkcjonalność NLP będzie ograniczona.")
                self.nlp = None

        # Inicjalizacja ekstraktorów encji
        self.entity_extractor = EntityExtractor()

        # Kompilacja wyrażeń regularnych
        self.compiled_patterns = [(re.compile(pattern, re.IGNORECASE), intent_type) for pattern, intent_type in
                                  self.INTENT_PATTERNS]

        # Inicjalizacja matchera spaCy (jeśli dostępny)
        if self.nlp:
            self.matcher = Matcher(self.nlp.vocab)
            self.phrase_matcher = PhraseMatcher(self.nlp.vocab)
            self._setup_spacy_matchers()

    def _setup_spacy_matchers(self) -> None:
        """
        Konfiguruje matchery spaCy dla różnych intencji.
        """
        # Dodaj wzorce dla każdej intencji
        # Open application
        self.matcher.add("OPEN_APP", [
            [{"LOWER": {"IN": ["otworz", "otwórz", "uruchom", "włącz", "wlacz"]}},
             {"LOWER": {"IN": ["aplikacje", "aplikację", "program"]}},
             {"OP": "?"},  # opcjonalne "o nazwie"
             {"IS_ALPHA": True}]
        ])

        # Login to website
        self.matcher.add("LOGIN", [
            [{"LOWER": {"IN": ["zaloguj"]}},
             {"LOWER": {"IN": ["się", "sie"]}},
             {"LOWER": {"IN": ["do", "na"]}},
             {"LOWER": {"IN": ["portalu", "strony", "serwisu", "stronę", "portal", "serwis"]}},
             {"IS_ALPHA": True}]
        ])

        # Get email
        self.matcher.add("GET_EMAIL", [
            [{"LOWER": {"IN": ["pobierz", "sprawdź", "sprawdz", "odczytaj"]}},
             {"OP": "*"},  # różne opcjonalne słowa
             {"LOWER": {"IN": ["skrzynki", "maila", "email", "emaila", "wiadomość", "wiadomosc"]}},
             {"SHAPE": {"REGEX": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"}}]
        ])

    def parse(self, text: str) -> Optional[IntentData]:
        """
        Parsuje tekst i rozpoznaje intencję oraz encje.

        Args:
            text: Tekst do sparsowania

        Returns:
            Dane intencji lub None, jeśli nie rozpoznano intencji
        """
        # Najpierw próbujemy rozpoznać intencję za pomocą wyrażeń regularnych
        intent_data = self._parse_with_regex(text)

        # Jeśli nie udało się rozpoznać intencji za pomocą regex, próbujemy z NLP
        if not intent_data and self.nlp:
            intent_data = self._parse_with_spacy(text)

        # Jeśli udało się rozpoznać intencję, wyekstrahuj dodatkowe encje
        if intent_data:
            self._extract_additional_entities(text, intent_data)
            self.logger.info(f"Rozpoznano intencję: {intent_data}")
        else:
            self.logger.warning(f"Nie rozpoznano intencji z tekstu: {text}")

        return intent_data

    def _parse_with_regex(self, text: str) -> Optional[IntentData]:
        """
        Parsuje tekst za pomocą wyrażeń regularnych.

        Args:
            text: Tekst do sparsowania

        Returns:
            Dane intencji lub None, jeśli nie rozpoznano intencji
        """
        for pattern, intent_type in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                # Tworzymy obiekt intencji
                intent_data = IntentData(intent_type)

                # Dodajemy główną encję z dopasowania
                if len(match.groups()) > 0:
                    main_entity = match.group(1)

                    # Dodaj główną encję w zależności od typu intencji
                    if intent_type == "open_application":
                        intent_data.add_entity("app_name", main_entity)
                    elif intent_type == "login_to_website":
                        intent_data.add_entity("website", main_entity)
                    elif intent_type == "get_email":
                        intent_data.add_entity("email_address", main_entity)
                    elif intent_type == "click":
                        intent_data.add_entity("target", main_entity)
                    elif intent_type == "type_text":
                        intent_data.add_entity("text", main_entity)
                    elif intent_type == "wait":
                        intent_data.add_entity("seconds", int(main_entity))
                    elif intent_type == "shell_command":
                        intent_data.add_entity("command", main_entity)
                    elif intent_type == "find_on_screen":
                        intent_data.add_entity("image", main_entity)

                return intent_data

        return None

    def _parse_with_spacy(self, text: str) -> Optional[IntentData]:
        """
        Parsuje tekst za pomocą modelu spaCy.

        Args:
            text: Tekst do sparsowania

        Returns:
            Dane intencji lub None, jeśli nie rozpoznano intencji
        """
        doc = self.nlp(text)

        # Używamy matchera spaCy
        matches = self.matcher(doc)

        if matches:
            # Bierzemy najlepsze dopasowanie (pierwsze)
            match_id, start, end = matches[0]
            span = doc[start:end]  # Fragment tekstu, który został dopasowany

            # Nazwa intencji z ID dopasowania
            intent_name = self.nlp.vocab.strings[match_id]

            # Mapowanie nazw intencji z matchera na nasze typy intencji
            intent_map = {
                "OPEN_APP": "open_application",
                "LOGIN": "login_to_website",
                "GET_EMAIL": "get_email",
                # można dodać więcej mapowań
            }

            intent_type = intent_map.get(intent_name)
            if intent_type:
                # Tworzymy obiekt intencji
                intent_data = IntentData(intent_type, confidence=0.8)  # Nieco mniejsza pewność niż przy regex

                # Dodajemy encje (w zależności od typu intencji)
                if intent_type == "open_application":
                    # Ostatnie słowo w dopasowaniu to prawdopodobnie nazwa aplikacji
                    app_name = doc[end - 1].text
                    intent_data.add_entity("app_name", app_name)
                elif intent_type == "login_to_website":
                    # Ostatnie słowo w dopasowaniu to prawdopodobnie nazwa strony
                    website = doc[end - 1].text
                    intent_data.add_entity("website", website)
                elif intent_type == "get_email":
                    # Szukamy adresu email w dopasowaniu
                    for token in span:
                        if re.match(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", token.text):
                            intent_data.add_entity("email_address", token.text)
                            break

                return intent_data

        return None

    def _extract_additional_entities(self, text: str, intent_data: IntentData) -> None:
        """
        Wyekstrahuj dodatkowe encje na podstawie tekstu i typu intencji.

        Args:
            text: Oryginalny tekst
            intent_data: Dane intencji do uzupełnienia
        """
        # Ekstrakcja dodatkowych encji w zależności od typu intencji
        if intent_data.intent_type == "login_to_website":
            # Próba wyekstrahowania nazwy użytkownika i hasła
            username = self.entity_extractor.extract_username(text)
            if username:
                intent_data.add_entity("username", username)

            password = self.entity_extractor.extract_password(text)
            if password:
                intent_data.add_entity("password", password)

        elif intent_data.intent_type == "get_email":
            # Próba wyekstrahowania filtra tematu
            subject_filter = self.entity_extractor.extract_subject_filter(text)
            if subject_filter:
                intent_data.add_entity("subject_filter", subject_filter)

            # Próba wyekstrahowania liczby wiadomości
            max_emails = self.entity_extractor.extract_email_count(text)
            if max_emails:
                intent_data.add_entity("max_emails", max_emails)

        elif intent_data.intent_type == "click":
            # Próba wyekstrahowania typu kliknięcia (pojedyncze, podwójne, prawy przycisk)
            click_type = self.entity_extractor.extract_click_type(text)
            if click_type:
                intent_data.add_entity("click_type", click_type)

            # Próba wyekstrahowania współrzędnych
            coordinates = self.entity_extractor.extract_coordinates(text)
            if coordinates:
                intent_data.add_entity("x", coordinates[0])
                intent_data.add_entity("y", coordinates[1])

        # Dodaj więcej ekstrakcji dla innych typów intencji