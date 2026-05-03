# Parser komend DSL
"""
parser.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parser kodu DSL, który tworzy drzewo składniowe (AST) na podstawie tokenów.
"""

from typing import List, Dict, Any, Optional
from automatyzer_desktop.dsl.grammar import (
    Token, TokenType, ASTNode, CommandNode, AssignmentNode,
    VariableNode, LiteralNode, BlockNode, ConditionalNode,
    LoopNode, PipelineNode
)


class ParserError(Exception):
    """Wyjątek zgłaszany przez parser"""

    def __init__(self, message: str, token: Token):
        """
        Inicjalizacja wyjątku.

        Args:
            message: Komunikat błędu
            token: Token, przy którym wystąpił błąd
        """
        self.message = message
        self.token = token
        super().__init__(f"{message} at line {token.line}, column {token.column}, token: {token.value}")


class Parser:
    """
    Parser kodu DSL.
    Zamienia listę tokenów na drzewo składniowe (AST).
    """

    def __init__(self, tokens: List[Token]):
        """
        Inicjalizacja parsera.

        Args:
            tokens: Lista tokenów do parsowania
        """
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> List[ASTNode]:
        """
        Parsuje tokeny i tworzy drzewo składniowe.

        Returns:
            Lista węzłów AST (drzewo składniowe)

        Raises:
            ParserError: Gdy wystąpi błąd składniowy
        """
        return self._parse_program()

    def _parse_program(self) -> List[ASTNode]:
        """
        Parsuje program (lista instrukcji).

        Returns:
            Lista węzłów AST reprezentujących instrukcje
        """
        statements = []

        while self._current_token().type != TokenType.EOF:
            # Ignoruj średniki i nowe linie między instrukcjami
            if self._current_token().type in (TokenType.SEMICOLON, TokenType.NEWLINE):
                self._advance()
                continue

            statement = self._parse_statement()
            if statement:
                statements.append(statement)

        return statements

    def _parse_statement(self) -> Optional[ASTNode]:
        """
        Parsuje pojedynczą instrukcję.

        Returns:
            Węzeł AST reprezentujący instrukcję lub None
        """
        token = self._current_token()

        # Instrukcja warunkowa (if)
        if token.type == TokenType.IF:
            return self._parse_conditional()

        # Pętla (while, repeat)
        elif token.type in (TokenType.WHILE, TokenType.REPEAT):
            return self._parse_loop()

        # Pipeline
        elif token.type == TokenType.PIPELINE:
            return self._parse_pipeline()

        # Blok kodu
        elif token.type == TokenType.OPEN_BRACE:
            return self._parse_block()

        # Przypisanie lub komenda
        elif token.type == TokenType.IDENTIFIER:
            # Sprawdź czy to przypisanie
            next_token = self._peek_token()
            if next_token.type == TokenType.EQUALS:
                return self._parse_assignment()
            else:
                return self._parse_command()

        # Coś nierozpoznanego
        else:
            raise ParserError(f"Nieoczekiwany token: {token.value}", token)

    def _parse_command(self) -> CommandNode:
        """
        Parsuje komendę.

        Returns:
            Węzeł komendy
        """
        command_token = self._current_token()
        if command_token.type != TokenType.IDENTIFIER:
            raise ParserError("Oczekiwano identyfikatora komendy", command_token)

        command_name = command_token.value
        self._advance()

        # Oczekujemy nawiasu otwierającego
        if self._current_token().type != TokenType.OPEN_PAREN:
            raise ParserError("Oczekiwano '(' po nazwie komendy", self._current_token())
        self._advance()

        # Parsowanie parametrów
        params = {}
        if self._current_token().type != TokenType.CLOSE_PAREN:
            params = self._parse_parameters()

        # Oczekujemy nawiasu zamykającego
        if self._current_token().type != TokenType.CLOSE_PAREN:
            raise ParserError("Oczekiwano ')' po parametrach komendy", self._current_token())
        self._advance()

        # Opcjonalny średnik
        if self._current_token().type == TokenType.SEMICOLON:
            self._advance()

        return CommandNode(command_token, command_name, params)

    def _parse_parameters(self) -> Dict[str, Any]:
        """
        Parsuje parametry komendy.

        Returns:
            Słownik z parametrami (nazwa -> wartość)
        """
        params = {}

        while True:
            # Nazwa parametru
            param_name_token = self._current_token()
            if param_name_token.type != TokenType.IDENTIFIER:
                raise ParserError("Oczekiwano nazwy parametru", param_name_token)
            param_name = param_name_token.value
            self._advance()

            # Znak równości
            if self._current_token().type != TokenType.EQUALS:
                raise ParserError("Oczekiwano '=' po nazwie parametru", self._current_token())
            self._advance()

            # Wartość parametru
            param_value = self._parse_expression()
            params[param_name] = param_value

            # Jeśli jest przecinek, to kolejny parametr
            if self._current_token().type == TokenType.COMMA:
                self._advance()
            else:
                break

        return params

    def _parse_expression(self) -> ASTNode:
        """
        Parsuje wyrażenie.

        Returns:
            Węzeł AST reprezentujący wyrażenie
        """
        token = self._current_token()

        # Literał
        if token.type in (TokenType.STRING, TokenType.NUMBER, TokenType.BOOLEAN):
            return self._parse_literal()

        # Zmienna
        elif token.type == TokenType.IDENTIFIER:
            # Sprawdź czy to komenda
            next_token = self._peek_token()
            if next_token.type == TokenType.OPEN_PAREN:
                return self._parse_command()
            else:
                return self._parse_variable()

        # Coś nierozpoznanego
        else:
            raise ParserError(f"Nieoczekiwany token w wyrażeniu: {token.value}", token)

    def _parse_literal(self) -> LiteralNode:
        """
        Parsuje literał (string, number, boolean).

        Returns:
            Węzeł literału
        """
        token = self._current_token()
        literal_value = token.value
        self._advance()
        return LiteralNode(token, literal_value)

    def _parse_variable(self) -> VariableNode:
        """
        Parsuje zmienną.

        Returns:
            Węzeł zmiennej
        """
        token = self._current_token()
        var_name = token.value
        self._advance()
        return VariableNode(token, var_name)

    def _parse_assignment(self) -> AssignmentNode:
        """
        Parsuje przypisanie zmiennej.

        Returns:
            Węzeł przypisania
        """
        var_token = self._current_token()
        var_name = var_token.value
        self._advance()

        # Znak równości
        equals_token = self._current_token()
        if equals_token.type != TokenType.EQUALS:
            raise ParserError("Oczekiwano '=' w przypisaniu", equals_token)
        self._advance()

        # Wyrażenie po prawej stronie
        value = self._parse_expression()

        # Opcjonalny średnik
        if self._current_token().type == TokenType.SEMICOLON:
            self._advance()

        return AssignmentNode(equals_token, var_name, value)

    def _parse_conditional(self) -> ConditionalNode:
        """
        Parsuje instrukcję warunkową (if/else).

        Returns:
            Węzeł instrukcji warunkowej
        """
        if_token = self._current_token()
        self._advance()

        # Warunek
        condition = self._parse_expression()

        # Blok true
        if self._current_token().type != TokenType.OPEN_BRACE:
            raise ParserError("Oczekiwano '{' po warunku if", self._current_token())

        true_block = self._parse_block()

        # Opcjonalny blok else
        false_block = None
        if (self._current_token().type == TokenType.ELSE):
            self._advance()

            if self._current_token().type != TokenType.OPEN_BRACE:
                raise ParserError("Oczekiwano '{' po słowie kluczowym else", self._current_token())

            false_block = self._parse_block()

        # Opcjonalny średnik
        if self._current_token().type == TokenType.SEMICOLON:
            self._advance()

        return ConditionalNode(if_token, condition, true_block, false_block)

    def _parse_loop(self) -> LoopNode:
        """
        Parsuje pętlę (while/repeat).

        Returns:
            Węzeł pętli
        """
        loop_token = self._current_token()
        is_repeat = (loop_token.type == TokenType.REPEAT)
        self._advance()

        # Warunek lub liczba powtórzeń
        condition = self._parse_expression()

        # Blok kodu
        if self._current_token().type != TokenType.OPEN_BRACE:
            raise ParserError("Oczekiwano '{' po warunku pętli", self._current_token())

        block = self._parse_block()

        # Opcjonalny średnik
        if self._current_token().type == TokenType.SEMICOLON:
            self._advance()

        return LoopNode(loop_token, condition, block, is_repeat)

    def _parse_block(self) -> BlockNode:
        """
        Parsuje blok kodu (lista instrukcji w nawiasach klamrowych).

        Returns:
            Węzeł bloku
        """
        # Nawias otwierający
        if self._current_token().type != TokenType.OPEN_BRACE:
            raise ParserError("Oczekiwano '{' na początku bloku", self._current_token())
        self._advance()

        # Lista instrukcji
        statements = []
        while self._current_token().type != TokenType.CLOSE_BRACE:
            # Ignoruj średniki i nowe linie między instrukcjami
            if self._current_token().type in (TokenType.SEMICOLON, TokenType.NEWLINE):
                self._advance()
                continue

            # Koniec pliku przed zamknięciem bloku
            if self._current_token().type == TokenType.EOF:
                raise ParserError("Nieoczekiwany koniec pliku, oczekiwano '}'", self._current_token())

            statement = self._parse_statement()
            if statement:
                statements.append(statement)

        # Nawias zamykający
        self._advance()

        # Opcjonalny średnik
        if self._current_token().type == TokenType.SEMICOLON:
            self._advance()

        return BlockNode(statements)

    def _parse_pipeline(self) -> PipelineNode:
        """
        Parsuje definicję pipeline.

        Returns:
            Węzeł pipeline
        """
        pipeline_token = self._current_token()
        self._advance()

        # Nazwa pipeline
        name_token = self._current_token()
        if name_token.type != TokenType.IDENTIFIER:
            raise ParserError("Oczekiwano nazwy pipeline", name_token)
        pipeline_name = name_token.value
        self._advance()

        # Blok pipeline
        if self._current_token().type != TokenType.OPEN_BRACE:
            raise ParserError("Oczekiwano '{' po nazwie pipeline", self._current_token())
        self._advance()

        # Lista kroków pipeline
        steps = []
        while self._current_token().type != TokenType.CLOSE_BRACE:
            # Ignoruj nowe linie
            if self._current_token().type == TokenType.NEWLINE:
                self._advance()
                continue

            # Koniec pliku przed zamknięciem bloku
            if self._current_token().type == TokenType.EOF:
                raise ParserError("Nieoczekiwany koniec pliku, oczekiwano '}'", self._current_token())

            # Parsuj komendę jako krok
            step = self._parse_command()
            steps.append(step)

            # Jeśli jest strzałka, kontynuuj pipeline
            if self._current_token().type == TokenType.ARROW:
                self._advance()
            # Jeśli jest średnik lub nowa linia, zakończ step
            elif self._current_token().type in (TokenType.SEMICOLON, TokenType.NEWLINE):
                self._advance()
            # Jeśli to zamknięcie bloku, kończymy parsowanie kroków
            elif self._current_token().type == TokenType.CLOSE_BRACE:
                break
            else:
                raise ParserError("Oczekiwano '->', ';' lub '}' po komendzie w pipeline", self._current_token())

        # Nawias zamykający
        self._advance()

        # Opcjonalny średnik
        if self._current_token().type == TokenType.SEMICOLON:
            self._advance()

        return PipelineNode(pipeline_token, pipeline_name, steps)

    def _current_token(self) -> Token:
        """
        Zwraca aktualny token.

        Returns:
            Aktualny token
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # Token EOF

    def _peek_token(self) -> Token:
        """
        Podgląda następny token.

        Returns:
            Następny token lub token EOF
        """
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return self.tokens[-1]  # Token EOF

    def _advance(self) -> None:
        """
        Przesuwa pozycję do następnego tokenu.
        """
        if self.pos < len(self.tokens):
            self.pos += 1