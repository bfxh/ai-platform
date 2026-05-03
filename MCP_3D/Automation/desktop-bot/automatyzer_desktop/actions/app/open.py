#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implementacja akcji otwierania aplikacji.
"""

import os
import time
import shutil
import logging
import subprocess
from typing import Any, Dict, Optional, List, Union

from automatyzer_desktop.actions.app.base import AppBaseAction


class OpenApplicationAction(AppBaseAction):
    """
    Akcja otwierania aplikacji.
    """

    ACTION_NAME = "open_application"
    ACTION_DESCRIPTION = "Otwiera aplikację o podanej nazwie."

    REQUIRED_PARAMS = {
        "name": str  # Nazwa aplikacji do otwarcia
    }
    OPTIONAL_PARAMS = {
        "system_type": (str, None),  # Typ systemu (Windows, Linux, Darwin), domyślnie wykrywany automatycznie
        "path": (str, None),  # Pełna ścieżka do aplikacji
        "args": (list, None),  # Argumenty przekazywane do aplikacji
        "wait": (bool, False),  # Czy czekać na zakończenie aplikacji
        "delay": (float, 1.0)  # Opóźnienie po uruchomieniu aplikacji (w sekundach)
    }

    def execute(self) -> Union[bool, int]:
        """
        Wykonuje akcję otwarcia aplikacji.

        Returns:
            True jeśli aplikacja została otwarta, kod zakończenia jeśli wait=True, False w przypadku błędu
        """
        # Pobranie parametrów
        app_name = self.get_param("name")
        system_type = self.get_param("system_type") or self.system_type
        app_path = self.get_param("path")
        args = self.get_param("args") or []
        wait = self.get_param("wait")
        delay = self.get_param("delay")

        try:
            # Otwarcie aplikacji w zależności od systemu
            if system_type.lower() == 'windows':
                return self._open_windows(app_name, app_path, args, wait, delay)
            elif system_type.lower() == 'linux':
                return self._open_linux(app_name, app_path, args, wait, delay)
            elif system_type.lower() == 'darwin':  # macOS
                return self._open_macos(app_name, app_path, args, wait, delay)
            else:
                self.logger.error(f"Nieobsługiwany system operacyjny: {system_type}")
                return False
        except Exception as e:
            self.logger.error(f"Błąd podczas otwierania aplikacji: {str(e)}")
            return False

    def _open_windows(self, app_name: str, app_path: Optional[str], args: List[str], wait: bool, delay: float) -> Union[
        bool, int]:
        """
        Otwiera aplikację w systemie Windows.
        """
        try:
            if app_path:
                # Użyj pełnej ścieżki
                cmd = [app_path] + args
            else:
                # Spróbuj znaleźć aplikację w systemie
                app_path = shutil.which(app_name)
                if app_path:
                    cmd = [app_path] + args
                else:
                    # Użyj 'start' do otwarcia aplikacji
                    cmd = ['start', app_name] + args
                    shell = True

            # Uruchomienie procesu
            if wait:
                self.logger.info(f"Uruchamianie aplikacji '{app_name}' i oczekiwanie na zakończenie...")
                process = subprocess.run(cmd, shell=shell if 'shell' in locals() else False, check=True)
                return process.returncode
            else:
                self.logger.info(f"Uruchamianie aplikacji '{app_name}'...")
                subprocess.Popen(cmd, shell=shell if 'shell' in locals() else False)

                # Opóźnienie po uruchomieniu
                if delay > 0:
                    time.sleep(delay)

                return True
        except Exception as e:
            self.logger.error(f"Błąd podczas otwierania aplikacji w systemie Windows: {str(e)}")

            # Spróbuj alternatywną metodę - przez menu Start
            try:
                import pyautogui
                self.logger.info(f"Próba alternatywnej metody uruchomienia aplikacji '{app_name}'...")

                # Naciśnij przycisk Windows
                pyautogui.press('win')
                time.sleep(0.5)

                # Wpisz nazwę aplikacji
                pyautogui.write(app_name)
                time.sleep(0.5)

                # Naciśnij Enter
                pyautogui.press('enter')

                # Opóźnienie po uruchomieniu
                if delay > 0:
                    time.sleep(delay)

                return True
            except Exception as e2:
                self.logger.error(f"Błąd podczas alternatywnej metody uruchamiania: {str(e2)}")
                return False

    def _open_linux(self, app_name: str, app_path: Optional[str], args: List[str], wait: bool, delay: float) -> Union[
        bool, int]:
        """
        Otwiera aplikację w systemie Linux.
        """
        try:
            if app_path:
                # Użyj pełnej ścieżki
                cmd = [app_path] + args
            else:
                # Spróbuj znaleźć aplikację w systemie
                app_path = shutil.which(app_name)
                if app_path:
                    cmd = [app_path] + args
                else:
                    # Użyj nazwy aplikacji
                    cmd = [app_name] + args

            # Uruchomienie procesu
            if wait:
                self.logger.info(f"Uruchamianie aplikacji '{app_name}' i oczekiwanie na zakończenie...")
                process = subprocess.run(cmd, check=True)
                return process.returncode
            else:
                self.logger.info(f"Uruchamianie aplikacji '{app_name}'...")
                subprocess.Popen(cmd)

                # Opóźnienie po uruchomieniu
                if delay > 0:
                    time.sleep(delay)

                return True
        except Exception as e:
            self.logger.error(f"Błąd podczas otwierania aplikacji w systemie Linux: {str(e)}")
            return False

    def _open_macos(self, app_name: str, app_path: Optional[str], args: List[str], wait: bool, delay: float) -> Union[
        bool, int]:
        """
        Otwiera aplikację w systemie macOS.
        """
        try:
            if app_path:
                # Użyj pełnej ścieżki
                if app_path.endswith('.app'):
                    cmd = ['open', app_path, '--args'] + args
                else:
                    cmd = [app_path] + args
            else:
                # Sprawdź czy to aplikacja (.app)
                if app_name.endswith('.app') or os.path.exists(f"/Applications/{app_name}.app"):
                    cmd = ['open', '-a', app_name, '--args'] + args
                else:
                    # Spróbuj znaleźć aplikację w systemie
                    app_path = shutil.which(app_name)
                    if app_path:
                        cmd = [app_path] + args
                    else:
                        cmd = [app_name] + args

            # Uruchomienie procesu
            if wait:
                self.logger.info(f"Uruchamianie aplikacji '{app_name}' i oczekiwanie na zakończenie...")
                process = subprocess.run(cmd, check=True)
                return process.returncode
            else:
                self.logger.info(f"Uruchamianie aplikacji '{app_name}'...")
                subprocess.Popen(cmd)

                # Opóźnienie po uruchomieniu
                if delay > 0:
                    time.sleep(delay)

                return True
        except Exception as e:
            self.logger.error(f"Błąd podczas otwierania aplikacji w systemie macOS: {str(e)}")
            return False