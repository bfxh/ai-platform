#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Inicjalizacja modułu akcji.
Importuje wszystkie dostępne akcje z podmodułów.
"""

# Importuj akcję bazową
from automatyzer_desktop.actions.base import BaseAction

# Importuj podmoduły z akcjami
from automatyzer_desktop.actions.app import *
from automatyzer_desktop.actions.mouse import *
from automatyzer_desktop.actions.keyboard import *

# Można dodać więcej importów dla innych kategorii akcji

# Lista wszystkich dostępnych akcji
__all__ = [
    # Akcja bazowa
    'BaseAction',

    # Akcje aplikacji
    'OpenApplicationAction',
    'CloseApplicationAction',
    'FocusApplicationAction',

    # Akcje myszy
    'ClickAction',
    'RightClickAction',
    'DoubleClickAction',
    'DragAction',
    'ScrollAction',
    'MoveToAction',
    'ScreenContainsAction',

    # Akcje klawiatury
    'TypeTextAction',
    'PressKeyAction',
    'HotkeyAction',
    'KeyDownAction',
    'KeyUpAction',
    'PasteTextAction',
    'CopyTextAction',

    # Można dodać więcej akcji
]