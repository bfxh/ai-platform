# Pojedynczy krok w pipeline
"""
step.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implementacja kroku w pipeline do automatyzacji zadań.
"""

import logging
from typing import Any, Dict, Optional, Callable, List, Union, Tuple
from automatyzer_desktop.actions.base import BaseAction


class PipelineStep:
    """
    Reprezentuje pojedynczy krok w pipeline automatyzacji.
    Każdy krok wykonuje jedną akcję z określonymi parametrami.
    """

    def __init__(self, action: BaseAction, name: str = None, conditions: List[Callable] = None):
        """
        Inicjalizacja kroku pipeline.

        Args:
            action: Akcja do wykonania w tym kroku
            name: Nazwa kroku (opcjonalna)
            conditions: Lista warunków, które muszą być spełnione przed wykonaniem kroku
        """
        self.logger = logging.getLogger(__name__)
        self.action = action
        self.name = name or f"Step_{id(self)}"
        self.conditions = conditions or []
        self.result = None
        self.executed = False
        self.success = False
        self.error = None

    def execute(self, context: Dict[str, Any] = None) -> Tuple[bool, Any]:
        """
        Wykonuje krok pipeline.

        Args:
            context: Kontekst wykonania pipeline (zmienne, wyniki poprzednich kroków)

        Returns:
            Krotka (sukces, wynik), gdzie sukces to True/False, a wynik to wartość zwrócona przez akcję
        """
        if context is None:
            context = {}

        # Sprawdzenie warunków
        for condition in self.conditions:
            try:
                if not condition(context):
                    self.logger.info(f"Krok {self.name} pominięty - warunek nie spełniony")
                    return False, None
            except Exception as e:
                self.logger.error(f"Błąd podczas sprawdzania warunku dla kroku {self.name}: {str(e)}")
                self.error = str(e)
                self.executed = True
                self.success = False
                return False, None

        # Wykonanie akcji
        try:
            self.logger.info(f"Wykonywanie kroku {self.name}")
            self.result = self.action.execute()
            self.success = True
            self.executed = True
            self.logger.info(f"Krok {self.name} wykonany pomyślnie")
            return True, self.result
        except Exception as e:
            self.logger.error(f"Błąd podczas wykonywania kroku {self.name}: {str(e)}")
            self.error = str(e)
            self.success = False
            self.executed = True
            return False, None

    def reset(self) -> None:
        """
        Resetuje stan kroku.
        """
        self.result = None
        self.executed = False
        self.success = False
        self.error = None

    def add_condition(self, condition: Callable) -> None:
        """
        Dodaje warunek do kroku.

        Args:
            condition: Funkcja warunku, która przyjmuje kontekst i zwraca True/False
        """
        self.conditions.append(condition)

    def __str__(self) -> str:
        """
        Zwraca tekstową reprezentację kroku.

        Returns:
            Tekstowa reprezentacja kroku
        """
        return f"PipelineStep(name={self.name}, action={self.action})"