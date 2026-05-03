#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Inicjalizacja modułu akcji aplikacji.
"""

from automatyzer_desktop.actions.app.open import OpenApplicationAction
from automatyzer_desktop.actions.app.close import CloseApplicationAction
from automatyzer_desktop.actions.app.focus import FocusApplicationAction

# Lista wszystkich akcji aplikacji do automatycznego zarejestrowania
__all__ = [
    'OpenApplicationAction',
    'CloseApplicationAction',
    'FocusApplicationAction'
]