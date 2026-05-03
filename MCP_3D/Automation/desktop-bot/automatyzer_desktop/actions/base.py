# Bazowa klasa akcji
"""
base.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bazowa klasa dla wszystkich akcji wykonywanych przez bota.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, ClassVar


class BaseAction(ABC):
    """
    Abstrakcyjna klasa bazowa dla wszystkich akcji.

    Każda akcja powinna dziedziczyć po tej klasie i implementować
    metodę execute() oraz określić swoje parametry.
    """

    # Nazwa akcji używana w DSL (do nadpisania w podklasach)
    ACTION_NAME: ClassVar[str] = ""

    # Opis akcji (do dokumentacji i pomocy)
    ACTION_DESCRIPTION: ClassVar[str] = ""

    # Wymagane parametry (nazwa -> typ)
    REQUIRED_PARAMS: ClassVar[Dict[str, Type]] = {}

    # Opcjonalne parametry (nazwa -> (typ, wartość domyślna))
    OPTIONAL_PARAMS: ClassVar[Dict[str, tuple]] = {}

    def __init__(self, bot, **kwargs):
        """
        Inicjalizacja akcji.

        Args:
            bot: Referencja do głównego obiektu bota
            **kwargs: Parametry akcji
        """
        self.bot = bot
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Walidacja wymaganych parametrów
        for param_name, param_type in self.REQUIRED_PARAMS.items():
            if param_name not in kwargs:
                raise ValueError(f"Brak wymaganego parametru: {param_name}")

            value = kwargs[param_name]
            if not isinstance(value, param_type):
                raise TypeError(
                    f"Parametr {param_name} powinien być typu {param_type.__name__}, "
                    f"otrzymano {type(value).__name__}"
                )

        # Ustawienie opcjonalnych parametrów z wartościami domyślnymi
        for param_name, (param_type, default_value) in self.OPTIONAL_PARAMS.items():
            if param_name in kwargs:
                value = kwargs[param_name]
                if not isinstance(value, param_type):
                    raise TypeError(
                        f"Parametr {param_name} powinien być typu {param_type.__name__}, "
                        f"otrzymano {type(value).__name__}"
                    )
            else:
                kwargs[param_name] = default_value

        # Zapisanie parametrów
        self.params = kwargs

    @classmethod
    def get_action_name(cls) -> str:
        """
        Zwraca nazwę akcji.

        Returns:
            Nazwa akcji
        """
        return cls.ACTION_NAME

    @classmethod
    def get_description(cls) -> str:
        """
        Zwraca opis akcji.

        Returns:
            Opis akcji
        """
        return cls.ACTION_DESCRIPTION

    @classmethod
    def get_required_params(cls) -> Dict[str, Type]:
        """
        Zwraca informacje o wymaganych parametrach.

        Returns:
            Słownik z wymaganymi parametrami
        """
        return cls.REQUIRED_PARAMS

    @classmethod
    def get_optional_params(cls) -> Dict[str, tuple]:
        """
        Zwraca informacje o opcjonalnych parametrach.

        Returns:
            Słownik z opcjonalnymi parametrami
        """
        return cls.OPTIONAL_PARAMS

    def get_param(self, name: str, default: Any = None) -> Any:
        """
        Pobiera wartość parametru.

        Args:
            name: Nazwa parametru
            default: Wartość domyślna, jeśli parametr nie istnieje

        Returns:
            Wartość parametru lub wartość domyślna
        """
        return self.params.get(name, default)

    @abstractmethod
    def execute(self) -> Any:
        """
        Wykonuje akcję.

        Returns:
            Wynik wykonania akcji
        """
        pass

    def validate(self) -> bool:
        """
        Dodatkowa walidacja parametrów i stanu akcji.
        Może być nadpisana w podklasach.

        Returns:
            True, jeśli akcja jest poprawna, False w przeciwnym razie
        """
        return True

    def __str__(self) -> str:
        """
        Zwraca tekstową reprezentację akcji.

        Returns:
            Tekstowa reprezentacja akcji
        """
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.ACTION_NAME}({params_str})"