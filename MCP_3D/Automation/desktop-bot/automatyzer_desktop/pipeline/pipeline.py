# Klasa pipeline
"""
pipeline.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implementacja pipeline'u do automatyzacji zadań.
Pipeline to sekwencja kroków wykonywanych w określonej kolejności.
"""

import logging
import time
from typing import Any, Dict, Optional, Callable, List, Union
from automatyzer_desktop.pipeline.step import PipelineStep


class Pipeline:
    """
    Reprezentuje pipeline automatyzacji - sekwencję kroków wykonywanych w określonej kolejności.
    """

    def __init__(self, steps: List[PipelineStep], name: str = "Pipeline",
                 description: str = "", error_handler: Callable = None,
                 condition: Callable = None):
        """
        Inicjalizacja pipeline'u.

        Args:
            steps: Lista kroków pipeline'u
            name: Nazwa pipeline'u
            description: Opis pipeline'u
            error_handler: Funkcja obsługi błędów
            condition: Warunek wykonania pipeline'u
        """
        self.logger = logging.getLogger(__name__)
        self.steps = steps
        self.name = name
        self.description = description
        self.error_handler = error_handler
        self.condition = condition
        self.context = {}  # Kontekst wykonania (zmienne, wyniki kroków)
        self.current_step_index = -1
        self.start_time = None
        self.end_time = None
        self.success = False
        self.error = None

    def execute(self, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Wykonuje wszystkie kroki pipeline'u.

        Args:
            initial_context: Początkowy kontekst wykonania

        Returns:
            Słownik z wynikami wykonania pipeline'u
        """
        # Reset stanu
        self.reset()

        # Inicjalizacja kontekstu
        if initial_context:
            self.context.update(initial_context)

        # Zapisz czas rozpoczęcia
        self.start_time = time.time()

        self.logger.info(f"Rozpoczęcie wykonywania pipeline '{self.name}'")

        # Sprawdzenie warunku dla całego pipeline'u
        if self.condition:
            try:
                if not self.condition(self.context):
                    self.logger.info(f"Pipeline '{self.name}' pominięty - warunek nie spełniony")
                    return self._get_results()
            except Exception as e:
                self.logger.error(f"Błąd podczas sprawdzania warunku dla pipeline '{self.name}': {str(e)}")
                self.error = str(e)
                self.end_time = time.time()
                return self._get_results()

        # Wykonanie kroków
        for i, step in enumerate(self.steps):
            self.current_step_index = i

            try:
                # Wykonanie kroku
                success, result = step.execute(self.context)

                # Zapisanie wyniku w kontekście
                if success:
                    self.context[f"step_{i}_result"] = result
                    self.context["last_result"] = result
                    self.context[f"step_{step.name}_result"] = result
                else:
                    # Krok się nie powiódł lub został pominięty przez warunek
                    if step.error:
                        # Obsługa błędu
                        if self.error_handler:
                            try:
                                self.error_handler(Exception(step.error), step, self.context)
                            except Exception as e:
                                self.logger.error(f"Błąd w handlerze błędów: {str(e)}")

                        # Zapisanie błędu
                        self.error = step.error
                        self.end_time = time.time()
                        self.logger.error(
                            f"Pipeline '{self.name}' zakończony z błędem w kroku {step.name}: {step.error}")
                        return self._get_results()
            except Exception as e:
                # Nieoczekiwany błąd podczas wykonywania kroku
                error_msg = f"Nieoczekiwany błąd w kroku {step.name}: {str(e)}"
                self.logger.error(error_msg)
                self.error = error_msg

                # Obsługa błędu
                if self.error_handler:
                    try:
                        self.error_handler(e, step, self.context)
                    except Exception as handler_e:
                        self.logger.error(f"Błąd w handlerze błędów: {str(handler_e)}")

                self.end_time = time.time()
                return self._get_results()

        # Pipeline wykonany pomyślnie
        self.success = True
        self.end_time = time.time()
        self.logger.info(f"Pipeline '{self.name}' zakończony pomyślnie")

        return self._get_results()

    def reset(self) -> None:
        """
        Resetuje stan pipeline'u.
        """
        self.context = {}
        self.current_step_index = -1
        self.start_time = None
        self.end_time = None
        self.success = False
        self.error = None

        # Reset wszystkich kroków
        for step in self.steps:
            step.reset()

    def _get_results(self) -> Dict[str, Any]:
        """
        Przygotowuje słownik z wynikami wykonania pipeline'u.

        Returns:
            Słownik z wynikami
        """
        execution_time = 0
        if self.start_time and self.end_time:
            execution_time = self.end_time - self.start_time

        return {
            "name": self.name,
            "description": self.description,
            "success": self.success,
            "error": self.error,
            "execution_time": execution_time,
            "steps_count": len(self.steps),
            "steps_executed": self.current_step_index + 1,
            "steps_results": {
                step.name: {
                    "executed": step.executed,
                    "success": step.success,
                    "error": step.error,
                    "result": step.result
                } for step in self.steps
            },
            "context": self.context
        }

    def get_step_by_name(self, name: str) -> Optional[PipelineStep]:
        """
        Pobiera krok po nazwie.

        Args:
            name: Nazwa kroku

        Returns:
            Krok lub None, jeśli nie znaleziono
        """
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def get_step_by_index(self, index: int) -> Optional[PipelineStep]:
        """
        Pobiera krok po indeksie.

        Args:
            index: Indeks kroku

        Returns:
            Krok lub None, jeśli indeks poza zakresem
        """
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None

    def add_step(self, step: PipelineStep) -> None:
        """
        Dodaje krok do pipeline'u.

        Args:
            step: Krok do dodania
        """
        self.steps.append(step)

    def insert_step(self, index: int, step: PipelineStep) -> None:
        """
        Wstawia krok na określonej pozycji.

        Args:
            index: Pozycja, na której wstawić krok
            step: Krok do wstawienia
        """
        self.steps.insert(index, step)

    def remove_step(self, index: int) -> Optional[PipelineStep]:
        """
        Usuwa krok o podanym indeksie.

        Args:
            index: Indeks kroku do usunięcia

        Returns:
            Usunięty krok lub None, jeśli indeks poza zakresem
        """
        if 0 <= index < len(self.steps):
            return self.steps.pop(index)
        return None

    def __str__(self) -> str:
        """
        Zwraca tekstową reprezentację pipeline'u.

        Returns:
            Tekstowa reprezentacja pipeline'u
        """
        return f"Pipeline(name={self.name}, steps_count={len(self.steps)})"