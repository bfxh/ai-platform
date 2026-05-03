# Lekser do tokenizacji DSL
"""
lexer.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Lekser do tokenizacji kodu DSL.
"""

import re
from typing import List, Iterator, Tuple, Optional
from automatyzer_desktop.dsl.grammar import Token, TokenType, KEYWORDS, COMPILED_PATTERNS


class LexerError(Exception):
    """Wyjątek zgłaszany przez lekser"""

    def __init__(self, message: str, line: int, column: int):
        """
        Inicjalizacja wyjątku.

        Args:
            message: Komunikat błędu
            line: Numer linii, w której wystąpił błąd
            column: Numer kolumny, w której wystąpił błąd
        """
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"{message} at line {line}, column {column}")


class Lexer:
    """
    Lekser do tokenizacji kodu DSL.
    Zamienia kod źródłowy na listę tokenów.
    """

    def __init__(self, source_code: str):
        """
        Inicjalizacja leksera.

        Args:
            source_code: Kod źródłowy do tokenizacji
        """
        self.source_code = source_code
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        """
        Tokenizuje kod źródłowy.

        Returns:
            Lista tokenów

        Raises:
            LexerError: Gdy wystąpi błąd podczas tokenizacji
        """
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.column = 1

        while self.pos < len(self.source_code):
            token = self._get_next_token()
            if token is not None:
                # Ignorujemy białe znaki i komentarze
                if token.type not in (TokenType.WHITESPACE, TokenType.COMMENT):
                    self.tokens.append(token)

                # Aktualizacja pozycji dla nowych linii
                if token.type == TokenType.NEWLINE:
                    self.line += 1
                    self.column = 1

        # Dodaj token końca pliku
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))

        return self.tokens

    def _get_next_token(self) -> Optional[Token]:
        """
        Pobiera następny token z kodu źródłowego.

        Returns:
            Token lub None, jeśli koniec pliku

        Raises:
            LexerError: Gdy nie udało się rozpoznać tokenu
        """
        if self.pos >= len(self.source_code):
            return None

        # Sprawdź każdy wzorzec
        for pattern, token_type in COMPILED_PATTERNS:
            match = pattern.match(self.source_code[self.pos:])
            if match:
                value = match.group(0)
                token = self._create_token(token_type, value)

                # Aktualizacja pozycji
                self.pos += len(value)
                self.column += len(value)

                return token

        # Jeśli żaden wzorzec nie pasuje, to błąd
        char = self.source_code[self.pos]
        raise LexerError(f"Nierozpoznany znak: '{char}'", self.line, self.column)

    def _create_token(self, token_type: TokenType, value: str) -> Token:
        """
        Tworzy token na podstawie typu i wartości.

        Args:
            token_type: Typ tokenu
            value: Wartość tokenu

        Returns:
            Utworzony token
        """
        # Sprawdź czy to słowo kluczowe
        if token_type == TokenType.IDENTIFIER and value in KEYWORDS:
            token_type = KEYWORDS[value]

        # Przetwarzanie literałów
        if token_type == TokenType.STRING:
            # Usuń cudzysłowy i przetwórz sekwencje escape
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1].replace("\\'", "'").replace('\\\\', '\\')
        elif token_type == TokenType.NUMBER:
            # Konwersja do liczby
            if '.' in value:
                value = float(value)
            else:
                value = int(value)
        elif token_type == TokenType.BOOLEAN:
            value = (value.lower() == 'true')

        return Token(token_type, value, self.line, self.column)