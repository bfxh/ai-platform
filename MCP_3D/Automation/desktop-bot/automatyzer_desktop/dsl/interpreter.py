# Interpreter komend DSL
"""
interpreter.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interpreter kodu DSL, który wykonuje instrukcje na podstawie drzewa składniowego.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from automatyzer_desktop.dsl.grammar import (
    ASTNode, CommandNode, AssignmentNode,
    VariableNode, LiteralNode, BlockNode, ConditionalNode,
    LoopNode, PipelineNode
)
from automatyzer_desktop.dsl.lexer import Lexer
from automatyzer_desktop.dsl.parser import Parser


class InterpreterError(Exception):
    """Wyjątek zgłaszany przez interpreter"""

    def __init__(self, message: str, node: Optional[ASTNode] = None):
        """
        Inicjalizacja wyjątku.

        Args:
            message: Komunikat błędu
            node: Węzeł, przy którym wystąpił błąd
        """
        self.message = message
        self.node = node

        if node and node.token:
            location = f" at line {node.token.line}, column {node.token.column}"
        else:
            location = ""

        super().__init__(f"{message}{location}")


class DSLInterpreter:
    """
    Interpreter kodu DSL.
    Wykonuje instrukcje na podstawie drzewa składniowego.
    """

    def __init__(self):
        """
        Inicjalizacja interpretera.
        """
        self.logger = logging.getLogger(__name__)

        # Środowisko wykonania (zmienne)
        self.environment = {}

        # Zdefiniowane pipeline'y
        self.pipelines = {}

    def interpret(self, code: str, bot) -> Any:
        """
        Interpretuje kod DSL.

        Args:
            code: Kod DSL
            bot: Referencja do głównego obiektu bota

        Returns:
            Wynik wykonania ostatniej instrukcji

        Raises:
            InterpreterError: Gdy wystąpi błąd podczas interpretacji
        """
        try:
            # Tokenizacja
            tokens = Lexer(code).tokenize()

            # Parsowanie
            ast = Parser(tokens).parse()

            # Wykonanie
            return self._execute_statements(ast, bot)
        except Exception as e:
            self.logger.error(f"Błąd interpretacji DSL: {str(e)}")
            raise

    def interpret_script(self, script: str, bot) -> List[Any]:
        """
        Interpretuje skrypt DSL.

        Args:
            script: Skrypt DSL
            bot: Referencja do głównego obiektu bota

        Returns:
            Lista wyników wykonania instrukcji

        Raises:
            InterpreterError: Gdy wystąpi błąd podczas interpretacji
        """
        try:
            # Tokenizacja
            tokens = Lexer(script).tokenize()

            # Parsowanie
            ast = Parser(tokens).parse()

            # Wykonanie
            results = []
            for node in ast:
                result = self._execute_node(node, bot)
                results.append(result)

            return results
        except Exception as e:
            self.logger.error(f"Błąd interpretacji skryptu DSL: {str(e)}")
            raise

    def _execute_statements(self, statements: List[ASTNode], bot) -> Any:
        """
        Wykonuje listę instrukcji.

        Args:
            statements: Lista węzłów AST
            bot: Referencja do głównego obiektu bota

        Returns:
            Wynik wykonania ostatniej instrukcji
        """
        result = None

        for node in statements:
            result = self._execute_node(node, bot)

        return result

    def _execute_node(self, node: ASTNode, bot) -> Any:
        """
        Wykonuje pojedynczy węzeł AST.

        Args:
            node: Węzeł AST
            bot: Referencja do głównego obiektu bota

        Returns:
            Wynik wykonania węzła

        Raises:
            InterpreterError: Gdy wystąpi nieobsługiwany typ węzła
        """
        if isinstance(node, CommandNode):
            return self._execute_command(node, bot)
        elif isinstance(node, AssignmentNode):
            return self._execute_assignment(node, bot)
        elif isinstance(node, VariableNode):
            return self._get_variable_value(node)
        elif isinstance(node, LiteralNode):
            return node.value
        elif isinstance(node, BlockNode):
            return self._execute_block(node, bot)
        elif isinstance(node, ConditionalNode):
            return self._execute_conditional(node, bot)
        elif isinstance(node, LoopNode):
            return self._execute_loop(node, bot)
        elif isinstance(node, PipelineNode):
            return self._define_pipeline(node)
        else:
            raise InterpreterError(f"Nieobsługiwany typ węzła: {type(node).__name__}", node)

    def _execute_command(self, node: CommandNode, bot) -> Any:
        """
        Wykonuje komendę.

        Args:
            node: Węzeł komendy
            bot: Referencja do głównego obiektu bota

        Returns:
            Wynik wykonania komendy

        Raises:
            InterpreterError: Gdy nie znaleziono komendy
        """
        command_name = node.name

        # Sprawdź czy to wywołanie pipeline'a
        if command_name == "execute_pipeline":
            return self._execute_pipeline_call(node, bot)

        # Ewaluacja parametrów
        params = {}
        for param_name, param_value_node in node.params.items():
            params[param_name] = self._execute_node(param_value_node, bot)

        # Wykonanie akcji
        try:
            action = bot.create_action(command_name, **params)
            if action:
                return action.execute()
            else:
                raise InterpreterError(f"Nie znaleziono akcji: {command_name}", node)
        except Exception as e:
            self.logger.error(f"Błąd podczas wykonywania komendy {command_name}: {str(e)}")
            raise InterpreterError(f"Błąd podczas wykonywania komendy {command_name}: {str(e)}", node)

    def _execute_assignment(self, node: AssignmentNode, bot) -> Any:
        """
        Wykonuje przypisanie zmiennej.

        Args:
            node: Węzeł przypisania
            bot: Referencja do głównego obiektu bota

        Returns:
            Wartość przypisania
        """
        var_name = node.variable
        value = self._execute_node(node.value, bot)

        # Zapisz zmienną w środowisku
        self.environment[var_name] = value

        return value

    def _get_variable_value(self, node: VariableNode) -> Any:
        """
        Pobiera wartość zmiennej.

        Args:
            node: Węzeł zmiennej

        Returns:
            Wartość zmiennej

        Raises:
            InterpreterError: Gdy zmienna nie istnieje
        """
        var_name = node.name

        # Sprawdź czy zmienna istnieje
        if var_name not in self.environment:
            # Sprawdź czy to specjalna zmienna 'env' (do dostępu do zmiennych środowiskowych)
            if var_name == "env":
                # Zwracamy proxy dla zmiennych środowiskowych
                # (będzie obsługiwane specjalnie przez interpreter)
                return EnvProxy()

            raise InterpreterError(f"Niezdefiniowana zmienna: {var_name}", node)

        return self.environment[var_name]

    def _execute_block(self, node: BlockNode, bot) -> Any:
        """
        Wykonuje blok kodu.

        Args:
            node: Węzeł bloku
            bot: Referencja do głównego obiektu bota

        Returns:
            Wynik wykonania ostatniej instrukcji w bloku
        """
        return self._execute_statements(node.statements, bot)

    def _execute_conditional(self, node: ConditionalNode, bot) -> Any:
        """
        Wykonuje instrukcję warunkową.

        Args:
            node: Węzeł instrukcji warunkowej
            bot: Referencja do głównego obiektu bota

        Returns:
            Wynik wykonania odpowiedniego bloku
        """
        condition = self._execute_node(node.condition, bot)

        if condition:
            return self._execute_node(node.true_block, bot)
        elif node.false_block:
            return self._execute_node(node.false_block, bot)

        return None

    def _execute_loop(self, node: LoopNode, bot) -> Any:
        """
        Wykonuje pętlę.

        Args:
            node: Węzeł pętli
            bot: Referencja do głównego obiektu bota

        Returns:
            Wynik ostatniego wykonania bloku pętli
        """
        result = None

        if node.is_repeat:
            # Pętla repeat (określona liczba powtórzeń)
            count = self._execute_node(node.condition, bot)

            if not isinstance(count, int):
                raise InterpreterError("Liczba powtórzeń musi być liczbą całkowitą", node)

            for _ in range(count):
                result = self._execute_node(node.block, bot)
        else:
            # Pętla while (wykonuje się, dopóki warunek jest prawdziwy)
            while self._execute_node(node.condition, bot):
                result = self._execute_node(node.block, bot)

        return result

    def _define_pipeline(self, node: PipelineNode) -> None:
        """
        Definiuje pipeline.

        Args:
            node: Węzeł pipeline

        Returns:
            None
        """
        pipeline_name = node.name

        # Zapisz pipeline w rejestrze
        self.pipelines[pipeline_name] = node.steps

        self.logger.info(f"Zdefiniowano pipeline: {pipeline_name} z {len(node.steps)} krokami")

        return None

    def _execute_pipeline_call(self, node: CommandNode, bot) -> Any:
        """
        Wykonuje wywołanie pipeline'a.

        Args:
            node: Węzeł komendy wywołującej pipeline
            bot: Referencja do głównego obiektu bota

        Returns:
            Wynik wykonania ostatniego kroku pipeline'a

        Raises:
            InterpreterError: Gdy nie znaleziono pipeline'a
        """
        # Pobierz nazwę pipeline'a
        pipeline_name_node = node.params.get("name")
        if not pipeline_name_node:
            raise InterpreterError("Brak parametru 'name' w wywołaniu execute_pipeline", node)

        pipeline_name = self._execute_node(pipeline_name_node, bot)

        # Sprawdź czy pipeline istnieje
        if pipeline_name not in self.pipelines:
            raise InterpreterError(f"Niezdefiniowany pipeline: {pipeline_name}", node)

        # Wykonaj kolejne kroki pipeline'a
        steps = self.pipelines[pipeline_name]
        result = None

        for step in steps:
            result = self._execute_node(step, bot)

        return result


class EnvProxy:
    """
    Proxy dla dostępu do zmiennych środowiskowych.
    Umożliwia notację env.NAZWA_ZMIENNEJ w kodzie DSL.
    """

    def __getattr__(self, name: str) -> str:
        """
        Pobiera zmienną środowiskową.

        Args:
            name: Nazwa zmiennej środowiskowej

        Returns:
            Wartość zmiennej środowiskowej

        Raises:
            AttributeError: Gdy zmienna środowiskowa nie istnieje
        """
        import os

        value = os.environ.get(name)
        if value is None:
            raise AttributeError(f"Zmienna środowiskowa '{name}' nie istnieje")

        return value