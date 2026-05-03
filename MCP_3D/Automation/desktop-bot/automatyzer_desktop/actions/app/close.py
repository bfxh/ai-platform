#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implementacja akcji zamykania aplikacji.
"""

import os
import time
import logging
import subprocess
import platform
from typing import Any, Dict, Optional, Union

from automatyzer_desktop.actions.app.base import AppBaseAction


class CloseApplicationAction(AppBaseAction):
    """
    Akcja zamykania aplikacji.
    """

    ACTION_NAME = "close_application"
    ACTION_DESCRIPTION = "Zamyka aplikację o podanej nazwie lub identyfikatorze procesu."

    REQUIRED_PARAMS = {}
    OPTIONAL_PARAMS = {
        "name": (str, None),  # Nazwa aplikacji do zamknięcia
        "pid": (int, None),  # Identyfikator procesu do zamknięcia
        "force": (bool, False),  # Czy wymusić zamknięcie (kill)
        "timeout": (float, 5.0),  # Limit czasu oczekiwania na zamknięcie (w sekundach)
        "delay": (float, 0.5)  # Opóźnienie po zamknięciu aplikacji (w sekundach)
    }

    def validate(self) -> bool:
        """
        Sprawdza czy parametry akcji są poprawne.

        Returns:
            True jeśli parametry są poprawne, False w przeciwnym razie
        """
        # Musi być podane name LUB pid
        has_name = self.get_param("name") is not None
        has_pid = self.get_param("pid") is not None

        return has_name or has_pid

    def execute(self) -> bool:
        """
        Wykonuje akcję zamknięcia aplikacji.

        Returns:
            True jeśli aplikacja została zamknięta, False w przypadku błędu
        """
        # Sprawdzenie parametrów
        if not self.validate():
            self.logger.error(
                "Brak wymaganych parametrów. Podaj nazwę aplikacji (name) lub identyfikator procesu (pid).")
            return False

        # Pobranie parametrów
        app_name = self.get_param("name")
        pid = self.get_param("pid")
        force = self.get_param("force")
        timeout = self.get_param("timeout")
        delay = self.get_param("delay")

        try:
            # Zamknięcie aplikacji w zależności od systemu
            if self.system_type == 'Windows':
                return self._close_windows(app_name, pid, force, timeout, delay)
            elif self.system_type == 'Linux':
                return self._close_linux(app_name, pid, force, timeout, delay)
            elif self.system_type == 'Darwin':  # macOS
                return self._close_macos(app_name, pid, force, timeout, delay)
            else:
                self.logger.error(f"Nieobsługiwany system operacyjny: {self.system_type}")
                return False
        except Exception as e:
            self.logger.error(f"Błąd podczas zamykania aplikacji: {str(e)}")
            return False

    def _close_windows(self, app_name: Optional[str], pid: Optional[int], force: bool, timeout: float,
                       delay: float) -> bool:
        """
        Zamyka aplikację w systemie Windows.
        """
        import psutil

        try:
            if pid is not None:
                # Zamknij proces o podanym PID
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()

                    if force:
                        process.kill()
                        self.logger.info(f"Wymuszono zamknięcie procesu o PID {pid} ({process_name})")
                    else:
                        process.terminate()
                        process.wait(timeout=timeout)
                        self.logger.info(f"Zamknięto proces o PID {pid} ({process_name})")
                except psutil.NoSuchProcess:
                    self.logger.warning(f"Proces o PID {pid} nie istnieje")
                    return False
                except psutil.TimeoutExpired:
                    if force:
                        process.kill()
                        self.logger.info(f"Wymuszono zamknięcie procesu o PID {pid} po upływie limitu czasu")
                    else:
                        self.logger.warning(f"Nie udało się zamknąć procesu o PID {pid} w ciągu {timeout} sekund")
                        return False
            elif app_name is not None:
                # Znajdź i zamknij procesy o podanej nazwie
                found = False
                for process in psutil.process_iter(['pid', 'name']):
                    if app_name.lower() in process.info['name'].lower():
                        found = True
                        try:
                            if force:
                                process.kill()
                                self.logger.info(
                                    f"Wymuszono zamknięcie procesu {process.info['name']} (PID {process.info['pid']})")
                            else:
                                process.terminate()
                                process.wait(timeout=timeout)
                                self.logger.info(f"Zamknięto proces {process.info['name']} (PID {process.info['pid']})")
                        except psutil.NoSuchProcess:
                            continue
                        except psutil.TimeoutExpired:
                            if force:
                                process.kill()
                                self.logger.info(
                                    f"Wymuszono zamknięcie procesu {process.info['name']} (PID {process.info['pid']}) po upływie limitu czasu")
                            else:
                                self.logger.warning(
                                    f"Nie udało się zamknąć procesu {process.info['name']} (PID {process.info['pid']}) w ciągu {timeout} sekund")

                if not found:
                    self.logger.warning(f"Nie znaleziono procesu o nazwie zawierającej '{app_name}'")
                    return False

            # Opóźnienie po zamknięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas zamykania aplikacji w systemie Windows: {str(e)}")
            return False

    def _close_linux(self, app_name: Optional[str], pid: Optional[int], force: bool, timeout: float,
                     delay: float) -> bool:
        """
        Zamyka aplikację w systemie Linux.
        """
        import psutil
        import signal

        try:
            if pid is not None:
                # Zamknij proces o podanym PID
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()

                    if force:
                        process.send_signal(signal.SIGKILL)
                        self.logger.info(f"Wymuszono zamknięcie procesu o PID {pid} ({process_name})")
                    else:
                        process.send_signal(signal.SIGTERM)
                        process.wait(timeout=timeout)
                        self.logger.info(f"Zamknięto proces o PID {pid} ({process_name})")
                except psutil.NoSuchProcess:
                    self.logger.warning(f"Proces o PID {pid} nie istnieje")
                    return False
                except psutil.TimeoutExpired:
                    if force:
                        process.send_signal(signal.SIGKILL)
                        self.logger.info(f"Wymuszono zamknięcie procesu o PID {pid} po upływie limitu czasu")
                    else:
                        self.logger.warning(f"Nie udało się zamknąć procesu o PID {pid} w ciągu {timeout} sekund")
                        return False
            elif app_name is not None:
                # Znajdź i zamknij procesy o podanej nazwie
                found = False
                for process in psutil.process_iter(['pid', 'name']):
                    if app_name.lower() in process.info['name'].lower():
                        found = True
                        try:
                            if force:
                                process.send_signal(signal.SIGKILL)
                                self.logger.info(
                                    f"Wymuszono zamknięcie procesu {process.info['name']} (PID {process.info['pid']})")
                            else:
                                process.send_signal(signal.SIGTERM)
                                process.wait(timeout=timeout)
                                self.logger.info(f"Zamknięto proces {process.info['name']} (PID {process.info['pid']})")
                        except psutil.NoSuchProcess:
                            continue
                        except psutil.TimeoutExpired:
                            if force:
                                process.send_signal(signal.SIGKILL)
                                self.logger.info(
                                    f"Wymuszono zamknięcie procesu {process.info['name']} (PID {process.info['pid']}) po upływie limitu czasu")
                            else:
                                self.logger.warning(
                                    f"Nie udało się zamknąć procesu {process.info['name']} (PID {process.info['pid']}) w ciągu {timeout} sekund")

                if not found:
                    self.logger.warning(f"Nie znaleziono procesu o nazwie zawierającej '{app_name}'")
                    return False

            # Opóźnienie po zamknięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas zamykania aplikacji w systemie Linux: {str(e)}")
            return False

    def _close_macos(self, app_name: Optional[str], pid: Optional[int], force: bool, timeout: float,
                     delay: float) -> bool:
        """
        Zamyka aplikację w systemie macOS.
        """
        import psutil
        import signal

        try:
            if pid is not None:
                # Zamknij proces o podanym PID
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()

                    if force:
                        process.send_signal(signal.SIGKILL)
                        self.logger.info(f"Wymuszono zamknięcie procesu o PID {pid} ({process_name})")
                    else:
                        process.send_signal(signal.SIGTERM)
                        process.wait(timeout=timeout)
                        self.logger.info(f"Zamknięto proces o PID {pid} ({process_name})")
                except psutil.NoSuchProcess:
                    self.logger.warning(f"Proces o PID {pid} nie istnieje")
                    return False
                except psutil.TimeoutExpired:
                    if force:
                        process.send_signal(signal.SIGKILL)
                        self.logger.info(f"Wymuszono zamknięcie procesu o PID {pid} po upływie limitu czasu")
                    else:
                        self.logger.warning(f"Nie udało się zamknąć procesu o PID {pid} w ciągu {timeout} sekund")
                        return False
            elif app_name is not None:
                # Jeśli to aplikacja .app, użyj polecenia 'osascript'
                app_name_clean = self.get_app_name_clean(app_name)

                if app_name.endswith('.app') or os.path.exists(f"/Applications/{app_name}.app"):
                    # Skrypt AppleScript do zamknięcia aplikacji
                    if force:
                        script = f'tell application "{app_name_clean}" to quit with saving'
                    else:
                        script = f'tell application "{app_name_clean}" to quit'

                    cmd = ['osascript', '-e', script]
                    subprocess.run(cmd, check=True)
                    self.logger.info(f"Zamknięto aplikację '{app_name}'")
                else:
                    # Znajdź i zamknij procesy o podanej nazwie
                    found = False
                    for process in psutil.process_iter(['pid', 'name']):
                        if app_name.lower() in process.info['name'].lower():
                            found = True
                            try:
                                if force:
                                    process.send_signal(signal.SIGKILL)
                                    self.logger.info(
                                        f"Wymuszono zamknięcie procesu {process.info['name']} (PID {process.info['pid']})")
                                else:
                                    process.send_signal(signal.SIGTERM)
                                    process.wait(timeout=timeout)
                                    self.logger.info(
                                        f"Zamknięto proces {process.info['name']} (PID {process.info['pid']})")
                            except psutil.NoSuchProcess:
                                continue
                            except psutil.TimeoutExpired:
                                if force:
                                    process.send_signal(signal.SIGKILL)
                                    self.logger.info(
                                        f"Wymuszono zamknięcie procesu {process.info['name']} (PID {process.info['pid']}) po upływie limitu czasu")
                                else:
                                    self.logger.warning(
                                        f"Nie udało się zamknąć procesu {process.info['name']} (PID {process.info['pid']}) w ciągu {timeout} sekund")

                    if not found:
                        self.logger.warning(f"Nie znaleziono procesu o nazwie zawierającej '{app_name}'")
                        return False

            # Opóźnienie po zamknięciu
            if delay > 0:
                time.sleep(delay)

            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas zamykania aplikacji w systemie macOS: {str(e)}")
            return False