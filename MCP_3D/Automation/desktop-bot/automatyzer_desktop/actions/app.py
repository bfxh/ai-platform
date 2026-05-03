# Akcje dla konkretnych aplikacji
"""
app.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implementacja akcji związanych z aplikacjami.
"""

import os
import time
import logging
import platform
import subprocess
import shutil
from typing import Any, Dict, Optional, List, Union

from automatyzer_desktop.actions.base import BaseAction


class OpenApplicationAction(BaseAction):
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
        system_type = self.get_param("system_type") or platform.system()
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


class CloseApplicationAction(BaseAction):
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

        # Ustalenie systemu operacyjnego
        system_type = platform.system()

        try:
            # Zamknięcie aplikacji w zależności od systemu
            if system_type == 'Windows':
                return self._close_windows(app_name, pid, force, timeout, delay)
            elif system_type == 'Linux':
                return self._close_linux(app_name, pid, force, timeout, delay)
            elif system_type == 'Darwin':  # macOS
                return self._close_macos(app_name, pid, force, timeout, delay)
            else:
                self.logger.error(f"Nieobsługiwany system operacyjny: {system_type}")
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
                if app_name.endswith('.app') or os.path.exists(f"/Applications/{app_name}.app"):
                    # Usuń rozszerzenie .app, jeśli istnieje
                    app_name_clean = app_name[:-4] if app_name.endswith('.app') else app_name

                    # Skrypt AppleScript do zamknięcia aplikacji
                    script = f'tell application "{app_name_clean}" to quit'

                    if force:
                        cmd = ['osascript', '-e', f'tell application "{app_name_clean}" to quit with saving']
                    else:
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


class FocusApplicationAction(BaseAction):
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

        # Ustalenie systemu operacyjnego
        system_type = platform.system()

        try:
            # Przeniesienie fokusa w zależności od systemu
            if system_type == 'Windows':
                return self._focus_windows(app_name, window_title, delay)
            elif system_type == 'Linux':
                return self._focus_linux(app_name, window_title, delay)
            elif system_type == 'Darwin':  # macOS
                return self._focus_macos(app_name, window_title, delay)
            else:
                self.logger.error(f"Nieobsługiwany system operacyjny: {system_type}")
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
            app_name_clean = app_name[:-4] if app_name.endswith('.app') else app_name

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
            if delay >