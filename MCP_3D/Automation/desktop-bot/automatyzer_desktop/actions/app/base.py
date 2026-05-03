#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Podstawowe klasy dla akcji związanych z aplikacjami.
"""

import logging
import platform
from typing import Dict, Any

from automatyzer_desktop.actions.base import BaseAction


class AppBaseAction(BaseAction):
    """
    Bazowa klasa dla akcji związanych z aplikacjami.
    """

    def __init__(self, bot, **kwargs):
        """
        Inicjalizacja akcji.

        Args:
            bot: Referencja do głównego obiektu bota
            **kwargs: Parametry akcji
        """
        super().__init__(bot, **kwargs)
        self.system_type = platform.system()

    def get_app_name_clean(self, app_name):
        """
        Pobiera oczyszczoną nazwę aplikacji (usuwa rozszerzenie .app dla macOS).

        Args:
            app_name: Nazwa aplikacji

        Returns:
            Oczyszczona nazwa aplikacji
        """
        if self.system_type == 'Darwin' and app_name.endswith('.app'):
            return app_name[:-4]
        return app_name