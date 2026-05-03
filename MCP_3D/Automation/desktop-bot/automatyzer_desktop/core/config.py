# Zarządzanie konfiguracją
"""
config.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Klasa zarządzająca konfiguracją bota.
Obsługuje ładowanie parametrów z plików .env i innych źródeł konfiguracji.
"""

import os
import logging
import json
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv


class Config:
    """
    Zarządza konfiguracją bota.
    Obsługuje ładowanie parametrów z plików .env i innych źródeł.
    """

    def __init__(self, env_file: str = '.env', config_file: str = None):
        """
        Inicjalizacja konfiguracji.

        Args:
            env_file: Ścieżka do pliku .env (zmienne środowiskowe)
            config_file: Ścieżka do pliku konfiguracyjnego JSON (opcjonalnie)
        """
        self.logger = logging.getLogger(__name__)
        self.config = {}

        # Ładowanie zmiennych środowiskowych z pliku .env
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
            self.logger.info(f"Załadowano zmienne środowiskowe z pliku {env_file}")
        else:
            self.logger.warning(f"Plik .env nie znaleziony: {env_file}")

        # Ładowanie konfiguracji z pliku JSON
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.logger.info(f"Załadowano konfigurację z pliku {config_file}")
            except Exception as e:
                self.logger.error(f"Błąd podczas ładowania pliku konfiguracyjnego {config_file}: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Pobiera wartość konfiguracji.
        Najpierw sprawdza zmienne środowiskowe, potem plik konfiguracyjny.

        Args:
            key: Klucz konfiguracji
            default: Wartość domyślna, jeśli klucz nie istnieje

        Returns:
            Wartość konfiguracji lub wartość domyślna
        """
        # Najpierw sprawdź zmienne środowiskowe
        env_value = os.environ.get(key)
        if env_value is not None:
            return self._convert_value(env_value)

        # Następnie sprawdź konfigurację z pliku
        config_value = self.config.get(key)
        if config_value is not None:
            return config_value

        # Jeśli nie znaleziono, zwróć wartość domyślną
        return default

    def set(self, key: str, value: Any) -> None:
        """
        Ustawia wartość konfiguracji.

        Args:
            key: Klucz konfiguracji
            value: Wartość do ustawienia
        """
        self.config[key] = value

    def save(self, config_file: str) -> bool:
        """
        Zapisuje konfigurację do pliku JSON.

        Args:
            config_file: Ścieżka do pliku, do którego zapisać konfigurację

        Returns:
            True jeśli udało się zapisać, False w przypadku błędu
        """
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Zapisano konfigurację do pliku {config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas zapisywania konfiguracji do pliku {config_file}: {str(e)}")
            return False

    def save_env(self, env_file: str) -> bool:
        """
        Zapisuje zmienne środowiskowe do pliku .env.

        Args:
            env_file: Ścieżka do pliku .env

        Returns:
            True jeśli udało się zapisać, False w przypadku błędu
        """
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                for key, value in self.config.items():
                    # Zapisujemy tylko wartości podstawowe (str, int, float, bool)
                    if isinstance(value, (str, int, float, bool)):
                        f.write(f"{key}={value}\n")
            self.logger.info(f"Zapisano zmienne środowiskowe do pliku {env_file}")
            return True
        except Exception as e:
            self.logger.error(f"Błąd podczas zapisywania zmiennych środowiskowych do pliku {env_file}: {str(e)}")
            return False

    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """
        Konwertuje wartość ze stringa na odpowiedni typ.

        Args:
            value: Wartość do konwersji

        Returns:
            Skonwertowana wartość
        """
        # Próba konwersji na liczbę całkowitą
        try:
            if value.isdigit():
                return int(value)
        except (ValueError, AttributeError):
            pass

        # Próba konwersji na liczbę zmiennoprzecinkową
        try:
            return float(value)
        except (ValueError, AttributeError):
            pass

        # Próba konwersji na wartość logiczną
        if value.lower() in ('true', 't', 'yes', 'y', '1'):
            return True
        elif value.lower() in ('false', 'f', 'no', 'n', '0'):
            return False

        # Pozostawienie jako string
        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Pobiera sekcję konfiguracji.

        Args:
            section: Nazwa sekcji

        Returns:
            Słownik z konfiguracją sekcji
        """
        result = {}

        # Szukaj zmiennych środowiskowych z prefixem sekcji
        prefix = f"{section}_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Usuń prefix i dodaj do wyników
                section_key = key[len(prefix):]
                result[section_key] = self._convert_value(value)

        # Dodaj konfigurację z pliku
        if section in self.config and isinstance(self.config[section], dict):
            # Aktualizuj rezultat (zmienne środowiskowe mają priorytet)
            section_config = self.config[section]
            for key, value in section_config.items():
                if key not in result:  # Tylko jeśli nie ma już w zmiennych środowiskowych
                    result[key] = value

        return result

    def has(self, key: str) -> bool:
        """
        Sprawdza czy klucz istnieje w konfiguracji.

        Args:
            key: Klucz do sprawdzenia

        Returns:
            True jeśli klucz istnieje, False w przeciwnym razie
        """
        return key in os.environ or key in self.config

    def __getitem__(self, key: str) -> Any:
        """
        Pobiera wartość konfiguracji z użyciem składni słownika.

        Args:
            key: Klucz konfiguracji

        Returns:
            Wartość konfiguracji

        Raises:
            KeyError: Gdy klucz nie istnieje
        """
        value = self.get(key)
        if value is None:
            raise KeyError(f"Klucz konfiguracji nie znaleziony: {key}")
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Ustawia wartość konfiguracji z użyciem składni słownika.

        Args:
            key: Klucz konfiguracji
            value: Wartość do ustawienia
        """
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """
        Sprawdza czy klucz istnieje w konfiguracji z użyciem składni 'in'.

        Args:
            key: Klucz do sprawdzenia

        Returns:
            True jeśli klucz istnieje, False w przeciwnym razie
        """
        return self.has(key)