# Builder dla pipeline
"""
builder.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Builder do tworzenia pipeline'ów automatyzacji.
Pozwala na wygodne budowanie złożonych sekwencji kroków.
"""

import logging
from typing import Any, Dict, Optional, Callable, List, Union, Type
from automatyzer_desktop.pipeline.pipeline import Pipeline
from automatyzer_desktop.pipeline.step import PipelineStep
from automatyzer_desktop.actions.base import BaseAction


class PipelineBuilder:
    """
    Builder do tworzenia pipeline'ów.
    Umożliwia wygodne definiowanie sekwencji kroków.
    """

    def __init__(self, bot):
        """
        Inicjalizacja buildera.

        Args:
            bot: Referencja do głównego obiektu bota
        """
        self.logger = logging.getLogger(__name__)
        self.bot = bot
        self.steps = []
        self.name = "Pipeline"
        self.description = ""
        self.error_handler = None
        self.condition = None

    def set_name(self, name: str) -> 'PipelineBuilder':
        """
        Ustawia nazwę pipeline'u.

        Args:
            name: Nazwa pipeline'u

        Returns:
            Self (dla chainingu)
        """
        self.name = name
        return self

    def set_description(self, description: str) -> 'PipelineBuilder':
        """
        Ustawia opis pipeline'u.

        Args:
            description: Opis pipeline'u

        Returns:
            Self (dla chainingu)
        """
        self.description = description
        return self

    def set_error_handler(self,
                          handler: Callable[[Exception, PipelineStep, Dict[str, Any]], None]) -> 'PipelineBuilder':
        """
        Ustawia handler błędów dla pipeline'u.

        Args:
            handler: Funkcja obsługi błędów

        Returns:
            Self (dla chainingu)
        """
        self.error_handler = handler
        return self

    def set_condition(self, condition: Callable[[Dict[str, Any]], bool]) -> 'PipelineBuilder':
        """
        Ustawia warunek dla całego pipeline'u.

        Args:
            condition: Funkcja warunku

        Returns:
            Self (dla chainingu)
        """
        self.condition = condition
        return self

    def add_step(self, action: Union[str, BaseAction], **kwargs) -> 'PipelineBuilder':
        """
        Dodaje krok do pipeline'u.

        Args:
            action: Nazwa akcji lub instancja akcji
            **kwargs: Parametry dla akcji (jeśli podano nazwę) lub dla kroku

        Returns:
            Self (dla chainingu)

        Raises:
            ValueError: Gdy nie można utworzyć akcji
        """
        # Jeśli podano nazwę akcji, utwórz instancję
        if isinstance(action, str):
            # Wyodrębnij parametry dla kroku i akcji
            step_params = {
                k: v for k, v in kwargs.items()
                if k in ['name', 'conditions']
            }

            action_params = {
                k: v for k, v in kwargs.items()
                if k not in step_params
            }

            # Utwórz akcję
            action_instance = self.bot.create_action(action, **action_params)
            if not action_instance:
                raise ValueError(f"Nie można utworzyć akcji: {action}")

            # Utwórz krok
            step = PipelineStep(
                action=action_instance,
                name=step_params.get('name'),
                conditions=step_params.get('conditions')
            )
        elif isinstance(action, BaseAction):
            # Jeśli podano instancję akcji, utwórz krok
            step = PipelineStep(
                action=action,
                name=kwargs.get('name'),
                conditions=kwargs.get('conditions')
            )
        else:
            raise ValueError(f"Nieprawidłowy typ akcji: {type(action)}")

        # Dodaj krok do listy
        self.steps.append(step)
        return self

    def add_condition_step(self, condition: Callable[[Dict[str, Any]], bool],
                           true_branch: List[PipelineStep],
                           false_branch: Optional[List[PipelineStep]] = None) -> 'PipelineBuilder':
        """
        Dodaje rozgałęzienie warunkowe do pipeline'u.

        Args:
            condition: Funkcja warunku
            true_branch: Lista kroków do wykonania, gdy warunek jest spełniony
            false_branch: Lista kroków do wykonania, gdy warunek nie jest spełniony (opcjonalna)

        Returns:
            Self (dla chainingu)
        """
        # Tworzenie akcji warunkowej
        condition_action = self.bot.create_action(
            "condition",
            condition=condition,
            true_branch=true_branch,
            false_branch=false_branch
        )

        # Dodanie kroku z akcją warunkową
        step = PipelineStep(
            action=condition_action,
            name=f"Condition_{len(self.steps)}"
        )

        self.steps.append(step)
        return self

    def add_loop_step(self, condition: Callable[[Dict[str, Any]], bool],
                      body: List[PipelineStep],
                      max_iterations: int = 100) -> 'PipelineBuilder':
        """
        Dodaje pętlę do pipeline'u.

        Args:
            condition: Funkcja warunku
            body: Lista kroków do wykonania w pętli
            max_iterations: Maksymalna liczba iteracji

        Returns:
            Self (dla chainingu)
        """
        # Tworzenie akcji pętli
        loop_action = self.bot.create_action(
            "loop",
            condition=condition,
            body=body,
            max_iterations=max_iterations
        )

        # Dodanie kroku z akcją pętli
        step = PipelineStep(
            action=loop_action,
            name=f"Loop_{len(self.steps)}"
        )

        self.steps.append(step)
        return self

    def build(self) -> Pipeline:
        """
        Buduje pipeline na podstawie zdefiniowanych kroków i parametrów.

        Returns:
            Gotowy pipeline
        """
        return Pipeline(
            steps=self.steps,
            name=self.name,
            description=self.description,
            error_handler=self.error_handler,
            condition=self.condition
        )