# Generowanie komend DSL z tekstu
"""
command_generator.py
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generator komend DSL na podstawie intencji z języka naturalnego.
Przekształca strukturę intencji na kod DSL do wykonania przez bota.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from automatyzer_desktop.nlp.intent_parser import IntentData


class CommandGenerator:
    """
    Generator komend DSL.
    Przekształca strukturę intencji na kod DSL.
    """

    def __init__(self):
        """
        Inicjalizacja generatora komend.
        """
        self.logger = logging.getLogger(__name__)

    def generate(self, intent_data: IntentData) -> Optional[str]:
        """
        Generuje komendę DSL na podstawie danych intencji.

        Args:
            intent_data: Dane intencji

        Returns:
            Komenda DSL lub None, jeśli nie udało się wygenerować
        """
        intent_type = intent_data.intent_type

        # Mapowanie typów intencji na funkcje generujące
        generators = {
            "open_application": self._generate_open_application,
            "login_to_website": self._generate_login_to_website,
            "get_email": self._generate_get_email,
            "click": self._generate_click,
            "type_text": self._generate_type_text,
            "wait": self._generate_wait,
            "shell_command": self._generate_shell_command,
            "find_on_screen": self._generate_find_on_screen
        }

        # Wywołaj odpowiednią funkcję generującą
        if intent_type in generators:
            return generators[intent_type](intent_data)

        self.logger.warning(f"Nieobsługiwany typ intencji: {intent_type}")
        return None

    def _param_str(self, params: Dict[str, Any]) -> str:
        """
        Konwertuje parametry na string w formacie DSL.

        Args:
            params: Słownik z parametrami

        Returns:
            String z parametrami w formacie DSL
        """
        param_parts = []

        for name, value in params.items():
            if isinstance(value, str):
                param_parts.append(f'{name}="{value}"')
            elif value is None:
                continue  # Pomijamy parametry None
            else:
                param_parts.append(f'{name}={value}')

        return ", ".join(param_parts)

    def _generate_open_application(self, intent_data: IntentData) -> str:
        """
        Generuje komendę do otwarcia aplikacji.

        Args:
            intent_data: Dane intencji

        Returns:
            Komenda DSL
        """
        params = {
            "name": intent_data.get_entity("app_name"),
            "system_type": intent_data.get_entity("system_type", None)
        }

        return f'open_application({self._param_str(params)});'

    def _generate_login_to_website(self, intent_data: IntentData) -> str:
        """
        Generuje komendę do logowania na stronę.

        Args:
            intent_data: Dane intencji

        Returns:
            Komenda DSL
        """
        website = intent_data.get_entity("website")

        # Mapowanie znanych stron na pełne URL
        website_map = {
            "linkedin": "linkedin.com",
            "facebook": "facebook.com",
            "google": "google.com",
            "gmail": "mail.google.com",
            "twitter": "twitter.com",
            "github": "github.com",
            # można dodać więcej mapowań
        }

        # Dodaj protokół, jeśli potrzebny
        if website.lower() in website_map:
            url = website_map[website.lower()]
        elif "." in website and not website.startswith(("http://", "https://")):
            url = f"https://{website}"
        else:
            url = website

        params = {
            "url": url,
            "username": intent_data.get_entity("username", None),
            "password": intent_data.get_entity("password", None)
        }

        commands = []

        # Otwarcie przeglądarki, jeśli nie wspomniano o przeglądarce
        if not intent_data.has_entity("browser_opened"):
            commands.append('open_application(name="firefox");')

        # Logowanie
        commands.append(f'navigate_to(url="{url}");')

        # Jeśli mamy dane logowania, dodaj odpowiednie komendy
        if params["username"]:
            commands.append(f'type_text(selector="#username", text="{params["username"]}");')

        if params["password"]:
            commands.append(f'type_text(selector="#password", text="{params["password"]}");')
            commands.append('click(selector="#login-button");')

        return "\n".join(commands)

    def _generate_get_email(self, intent_data: IntentData) -> str:
        """
        Generuje komendę do pobierania emaila.

        Args:
            intent_data: Dane intencji

        Returns:
            Komenda DSL
        """
        params = {
            "from": intent_data.get_entity("email_address"),
            "subject_filter": intent_data.get_entity("subject_filter", None),
            "max_count": intent_data.get_entity("max_emails", 1)
        }

        # Pobranie emaila
        commands = [f'emails = get_emails({self._param_str(params)});']

        # Jeśli chodzi o kod uwierzytelniający, dodaj ekstrakcję
        if "kod" in intent_data.get_entity("email_address", "") or "auth" in intent_data.get_entity("email_address",
                                                                                                    ""):
            regex = intent_data.get_entity("regex", "\\b\\d{6}\\b")  # Domyślny regex dla 6-cyfrowego kodu
            commands.append(f'auth_code = extract_code(text=emails[0].body, regex="{regex}");')
            commands.append('type_text(text=auth_code);')

        return "\n".join(commands)

    def _generate_click(self, intent_data: IntentData) -> str:
        """
        Generuje komendę do kliknięcia.

        Args:
            intent_data: Dane intencji

        Returns:
            Komenda DSL
        """
        params = {}

        # Współrzędne mają priorytet
        if intent_data.has_entity("x") and intent_data.has_entity("y"):
            params["x"] = intent_data.get_entity("x")
            params["y"] = intent_data.get_entity("y")

        # Inaczej używamy obrazu lub selektora
        elif intent_data.has_entity("target"):
            target = intent_data.get_entity("target")

            # Sprawdź czy target to ścieżka do obrazu
            if "." in target and any(target.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]):
                params["image"] = target
            else:
                # Zakładamy, że to selektor
                params["selector"] = target

        # Typ kliknięcia
        click_type = intent_data.get_entity("click_type", "single")

        # Wybierz odpowiednią funkcję w zależności od typu kliknięcia
        if click_type == "double":
            command = "double_click"
        elif click_type == "right":
            command = "right_click"
        else:
            command = "click"

        return f'{command}({self._param_str(params)});'

    def _generate_type_text(self, intent_data: IntentData) -> str:
        """
        Generuje komendę do wpisywania tekstu.

        Args:
            intent_data: Dane intencji

        Returns:
            Komenda DSL
        """
        params = {
            "text": intent_data.get_entity("text"),
            "selector": intent_data.get_entity("selector", None)
        }

        return f'type_text({self._param_str(params)});'

    def _generate_wait(self, intent_data: IntentData) -> str:
        """
        Generuje komendę do czekania.

        Args:
            intent_data: Dane intencji

        Returns:
            Komenda DSL
        """
        params = {
            "seconds": intent_data.get_entity("seconds", 1)
        }

        return f'wait({self._param_str(params)});'

    def _generate_shell_command(self, intent_data: IntentData) -> str:
        """
        Generuje komendę do wykonania polecenia powłoki.

        Args:
            intent_data: Dane intencji

        Returns:
            Komenda DSL
        """
        params = {
            "command": intent_data.get_entity("command"),
            "remote_host": intent_data.get_entity("remote_host", None),
            "remote_user": intent_data.get_entity("remote_user", None)
        }

        return f'execute_shell_command({self._param_str(params)});'

    def _generate_find_on_screen(self, intent_data: IntentData) -> str:
        """
        Generuje komendę do znalezienia obrazu na ekranie.

        Args:
            intent_data: Dane intencji

        Returns:
            Komenda DSL
        """
        params = {
            "image": intent_data.get_entity("image"),
            "confidence": intent_data.get_entity("confidence", 0.8)
        }

        return f'found = screen_contains({self._param_str(params)});'