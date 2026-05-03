# Główna klasa bota
"""
bot.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Główna klasa bota do automatyzacji zadań.
Integruje wszystkie komponenty i zarządza przepływem pracy.
"""

import importlib
import logging
import os
from typing import Any, Dict, List, Optional, Union, Type

from automatyzer_desktop.core.config import Config
from automatyzer_desktop.actions.base import BaseAction
from automatyzer_desktop.pipeline.pipeline import Pipeline
from automatyzer_desktop.pipeline.builder import PipelineBuilder
from automatyzer_desktop.dsl.interpreter import DSLInterpreter
from automatyzer_desktop.nlp.intent_parser import IntentParser
from automatyzer_desktop.nlp.command_generator import CommandGenerator


class AutomationBot:
    """
    Główna klasa bota do automatyzacji zadań.
    Integruje wszystkie komponenty i zarządza przepływem pracy.
    """

    def __init__(self, config_path: str = '.env'):
        """
        Inicjalizacja bota z konfiguracją.

        Args:
            config_path: Ścieżka do pliku konfiguracyjnego
        """
        self.logger = logging.getLogger(__name__)
        self.config = Config(config_path)

        # Inicjalizacja interpretera DSL
        self.dsl_interpreter = DSLInterpreter()

        # Inicjalizacja komponentów NLP
        self.intent_parser = IntentParser()
        self.command_generator = CommandGenerator()

        # Rejestr dostępnych akcji
        self.actions_registry = {}

        # Zarejestruj wszystkie dostępne akcje
        self._register_actions()

        self.logger.info("Bot został zainicjalizowany")

    def _register_actions(self) -> None:
        """
        Rejestruje wszystkie dostępne akcje na podstawie plików w katalogu actions.
        """
        # Importujemy moduły dynamicznie
        actions_path = 'automatyzer_desktop.actions'
        actions_package = importlib.import_module(actions_path)

        # Znajdź wszystkie moduły w pakiecie actions
        for module_info in actions_package.__path__:
            for file in os.listdir(module_info):
                if file.endswith('.py') and not file.startswith('__'):
                    module_name = file[:-3]  # Usuń rozszerzenie .py
                    try:
                        # Zaimportuj moduł
                        module = importlib.import_module(f"{actions_path}.{module_name}")

                        # Znajdź wszystkie klasy w module, które dziedziczą po BaseAction
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and
                                    issubclass(attr, BaseAction) and
                                    attr is not BaseAction):
                                # Zarejestruj akcję
                                action_name = attr.get_action_name()
                                if action_name:
                                    self.actions_registry[action_name] = attr
                                    self.logger.debug(f"Zarejestrowano akcję: {action_name}")
                    except Exception as e:
                        self.logger.error(f"Błąd podczas rejestrowania akcji z modułu {module_name}: {str(e)}")

        self.logger.info(f"Zarejestrowano {len(self.actions_registry)} akcji")

    def get_action(self, action_name: str) -> Optional[Type[BaseAction]]:
        """
        Pobiera klasę akcji na podstawie jej nazwy.

        Args:
            action_name: Nazwa akcji

        Returns:
            Klasa akcji lub None, jeśli nie znaleziono
        """
        return self.actions_registry.get(action_name)

    def create_action(self, action_name: str, **kwargs) -> Optional[BaseAction]:
        """
        Tworzy instancję akcji na podstawie jej nazwy.

        Args:
            action_name: Nazwa akcji
            **kwargs: Parametry do przekazania do konstruktora akcji

        Returns:
            Instancja akcji lub None, jeśli nie znaleziono
        """
        action_class = self.get_action(action_name)
        if action_class:
            return action_class(bot=self, **kwargs)
        return None

    def execute_command(self, command: str) -> Any:
        """
        Wykonuje komendę DSL.

        Args:
            command: Komenda w formacie DSL

        Returns:
            Wynik wykonania komendy
        """
        try:
            return self.dsl_interpreter.interpret(command, self)
        except Exception as e:
            self.logger.error(f"Błąd podczas wykonywania komendy: {str(e)}")
            raise

    def execute_script(self, script_path: str) -> List[Any]:
        """
        Wykonuje skrypt DSL z pliku.

        Args:
            script_path: Ścieżka do pliku ze skryptem

        Returns:
            Lista wyników wykonania komend
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            return self.dsl_interpreter.interpret_script(script_content, self)
        except Exception as e:
            self.logger.error(f"Błąd podczas wykonywania skryptu: {str(e)}")
            raise

    def process_natural_language(self, text: str) -> Optional[str]:
        """
        Przetwarza tekst w języku naturalnym na komendę DSL.

        Args:
            text: Tekst w języku naturalnym

        Returns:
            Komenda DSL lub None, jeśli nie udało się przetworzyć
        """
        try:
            # Rozpoznaj intencję i encje
            intent_data = self.intent_parser.parse(text)

            # Generuj komendę DSL
            if intent_data:
                dsl_command = self.command_generator.generate(intent_data)
                self.logger.info(f"Wygenerowano komendę DSL: {dsl_command}")
                return dsl_command
            else:
                self.logger.warning(f"Nie udało się rozpoznać intencji: {text}")
                return None
        except Exception as e:
            self.logger.error(f"Błąd podczas przetwarzania języka naturalnego: {str(e)}")
            return None

    def execute_natural_language(self, text: str) -> Any:
        """
        Wykonuje polecenie wyrażone w języku naturalnym.

        Args:
            text: Tekst w języku naturalnym

        Returns:
            Wynik wykonania lub None w przypadku błędu
        """
        dsl_command = self.process_natural_language(text)
        if dsl_command:
            return self.execute_command(dsl_command)
        return None

    def create_pipeline(self) -> PipelineBuilder:
        """
        Tworzy nowy builder pipeline'u.

        Returns:
            Builder pipeline'u
        """
        return PipelineBuilder(self)

    def execute_pipeline(self, pipeline: Pipeline) -> Dict[str, Any]:
        """
        Wykonuje pipeline.

        Args:
            pipeline: Pipeline do wykonania

        Returns:
            Słownik z wynikami wykonania pipeline'u
        """
        return pipeline.execute()