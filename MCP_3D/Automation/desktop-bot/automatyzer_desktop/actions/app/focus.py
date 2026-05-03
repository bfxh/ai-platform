#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implementacja akcji przenoszenia fokusa na okno aplikacji.
"""

import os
import time
import logging
import subprocess
from typing import Any, Dict, Optional, List, Union

from automatyzer_desktop.actions.app.base import AppBaseAction


class FocusApplicationAction(AppBaseAction):
    """
    Akcja przenoszenia fokusa na okno aplikacji.
    """

    ACTION_NAME = "focus_application"
    ACTION_DESCRIPTION = "Przenosi fokus na okno aplikacji o podanej nazwie."

    REQUIRED_PARAMS = {
        "name": str  # Nazwa aplikacji, na którą przenieść fokus
    }
    OPTIONAL_PARAMS = {
        "window_title": (str, None),  # Tytuł okna (jeśli aplikacja ma wiele okien)
        "delay": (float, 0.5)  # Opóźnienie po przeniesieniu fokusa (w sekundach)
    }

    def execute(self) -> bool:
        """
        Wykonuje akcję przeniesienia fokusa na okno aplikacji.

        Returns:
            True jeśli fokus został przeniesiony, False w przypadku błędu
        """
        # Pobranie parametrów
        app_name = self.get_param("name")
        window_title = self.get_param("window_title")
        delay = self.get_param("delay")

        try:
            # Przeniesienie fokusa w zależności od systemu
            if self.system_type == 'Windows':
                return self._focus_windows(app_name, window_title, delay)
            elif self.system_type == 'Linux':
                return self._focus_linux(app_name, window_title, delay)
            elif self.system_type == 'Darwin':  # macOS
                return self._focus_macos(app_name, window_title, delay)
            else:
                self.logger.error(f"Nieobsługiwany system operacyjny: {self.system_type}")
                return False
        except Exception as e:
            self.logger.error(f"Błąd podczas przenoszenia fokusa na aplikację: {str(e)}")
            return False

    def _focus_windows(self, app_name: str, window_title: Optional[str], delay: float) -> bool:
        """
        Przenosi fokus na okno aplikacji w systemie Windows.
        """
        try:
            # Importuj bibliotekę pygetwindow (wrapper dla Win32 API)
            import pygetwindow as gw

            # Znajdź wszystkie okna danej aplikacji
            windows = []

            if window_title:
                # Szukaj po tytule okna
                windows = gw.getWindowsWithTitle(window_title)
            else:
                # Szukaj po nazwie aplikacji (częściowe dopasowanie)
                all_windows = gw.getAllWindows()
                for window in all_windows:
                    if app_name.lower() in window.title.lower():
                        windows.append(window)

            if not windows:
                self.logger.warning(f"Nie znaleziono okien aplikacji '{app_name}'")
                return False

            # Uaktywnij pierwsze okno
            window = windows[0]

            # Jeśli okno jest zminimalizowane, przywróć je
            if window.isMinimized:
                window.restore()

            # Przenieś okno na wierzch i przenieś fokus
            window.activate()

            self.logger.info(f"Przeniesiono fokus na okno '{window.title}'")

            # Opóźnienie po przeniesieniu fokusa
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas przenoszenia fokusa w systemie Windows: {str(e)}")

            # Alternatywna metoda - przez Alt+Tab
            try:
                import pyautogui
                self.logger.info("Próba alternatywnej metody przeniesienia fokusa...")

                # Naciśnij Alt+Tab aby przejść do następnego okna
                pyautogui.keyDown('alt')
                pyautogui.press('tab')
                pyautogui.keyUp('alt')

                # Opóźnienie po przeniesieniu fokusa
                if delay > 0:
                    time.sleep(delay)

                return True
            except Exception as e2:
                self.logger.error(f"Błąd podczas alternatywnej metody przenoszenia fokusa: {str(e2)}")
                return False

    def _focus_linux(self, app_name: str, window_title: Optional[str], delay: float) -> bool:
        """
        Przenosi fokus na okno aplikacji w systemie Linux.
        """
        try:
            # Użyj wmctrl do przeniesienia fokusa
            if window_title:
                # Szukaj po tytule okna
                cmd = ['wmctrl', '-a', window_title]
            else:
                # Szukaj po nazwie aplikacji
                cmd = ['wmctrl', '-a', app_name]

            result = subprocess.run(cmd, capture_output=True)

            if result.returncode != 0:
                self.logger.warning(
                    f"Nie udało się przenieść fokusa na aplikację '{app_name}': {result.stderr.decode()}")

                # Alternatywna metoda - przez xdotool
                try:
                    # Znajdź ID okna
                    find_cmd = ['xdotool', 'search', '--name', app_name if not window_title else window_title]
                    window_id = subprocess.check_output(find_cmd).decode().strip()

                    if window_id:
                        # Przenieś fokus na okno
                        focus_cmd = ['xdotool', 'windowactivate', window_id.split('\n')[0]]
                        subprocess.run(focus_cmd, check=True)
                        self.logger.info(f"Przeniesiono fokus na okno aplikacji '{app_name}'")
                    else:
                        self.logger.warning(f"Nie znaleziono okna aplikacji '{app_name}'")
                        return False
                except Exception as e:
                    self.logger.error(f"Błąd podczas alternatywnej metody przenoszenia fokusa: {str(e)}")
                    return False
            else:
                self.logger.info(f"Przeniesiono fokus na okno aplikacji '{app_name}'")

            # Opóźnienie po przeniesieniu fokusa
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas przenoszenia fokusa w systemie Linux: {str(e)}")
            return False

    def _focus_macos(self, app_name: str, window_title: Optional[str], delay: float) -> bool:
        """
        Przenosi fokus na okno aplikacji w systemie macOS.
        """
        try:
            # Usuń rozszerzenie .app, jeśli istnieje
            app_name_clean = self.get_app_name_clean(app_name)

            # Skrypt AppleScript do aktywacji aplikacji
            script = f'tell application "{app_name_clean}" to activate'

            # Jeśli podano tytuł okna, użyj bardziej złożonego skryptu
            if window_title:
                script = f'''
                tell application "{app_name_clean}"
                    activate
                    set allWindows to every window
                    repeat with w in allWindows
                        if name of w contains "{window_title}" then
                            set index of w to 1
                            exit repeat
                        end if
                    end repeat
                end tell
                '''

            # Wykonaj skrypt AppleScript
            cmd = ['osascript', '-e', script]
            result = subprocess.run(cmd, capture_output=True)

            if result.returncode != 0:
                self.logger.warning(
                    f"Nie udało się przenieść fokusa na aplikację '{app_name}': {result.stderr.decode()}")
                return False

            self.logger.info(f"Przeniesiono fokus na aplikację '{app_name}'")

            # Opóźnienie po przeniesieniu fokusa
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas przenoszenia fokusa w systemie macOS: {str(e)}")
            return False