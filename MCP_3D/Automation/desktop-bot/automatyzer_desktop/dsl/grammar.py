#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Definicja gramatyki języka DSL (Domain Specific Language) używanego
do tworzenia skryptów automatyzacji.
"""

import re
from typing import Dict, List, Tuple, Any, Union
from enum import Enum, auto


class TokenType(Enum):
    """Typy tokenów używanych w DSL"""
    COMMAND = auto()  # Komenda (action)
    IDENTIFIER = auto()  # Identyfikator (nazwa zmiennej)
    STRING = auto()  # Łańcuch znaków
    NUMBER = auto()  # Liczba
    BOOLEAN = auto()  # Wartość logiczna (true/false)
    EQUALS = auto()  # Znak przypisania (=)
    OPEN_PAREN = auto()  # Nawias otwierający (
    CLOSE_PAREN = auto()  # Nawias zamykający )
    OPEN_BRACE = auto()  # Nawias klamrowy otwierający {
    CLOSE_BRACE = auto()  # Nawias klamrowy zamykający }
    COMMA = auto()  # Przecinek
    COLON = auto()  # Dwukropek
    ARROW = auto()  # Strzałka (-> dla pipeline)
    PIPE = auto()  # Potok (| dla alternatywnych ścieżek)
    DOT = auto()  # Kropka (do dostępu do właściwości)
    SEMICOLON = auto()  # Średnik (oddziela instrukcje)
    COMMENT = auto()  # Komentarz
    KEYWORD = auto()  # Słowo kluczowe
    IF = auto()  # Słowo kluczowe if
    ELSE = auto()  # Słowo kluczowe else
    WHILE = auto()  # Słowo kluczowe while
    REPEAT = auto()  # Słowo kluczowe repeat
    PIPELINE = auto()  # Słowo kluczowe pipeline
    END = auto()  # Słowo kluczowe end
    NEWLINE = auto()  # Nowa linia
    WHITESPACE = auto()  # Biały znak
    EOF = auto()  # Koniec pliku


class Token:
    """Reprezentuje token w DSL"""

    def __init__(self, token_type: TokenType, value: str, line: int, column: int):
        """
        Inicjalizacja tokenu.

        Args:
            token_type: Typ tokenu
            value: Wartość tokenu
            line: Numer linii
            column: Numer kolumny
        """
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return f"Token({self.type}, '{self.value}', line={self.line}, col={self.column})"

    def __repr__(self) -> str:
        return self.__str__()


class ASTNode:
    """Bazowa klasa dla węzłów drzewa składniowego (AST)"""

    def __init__(self, token: Token = None):
        """
        Inicjalizacja węzła AST.

        Args:
            token: Token związany z węzłem
        """
        self.token = token

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"


class CommandNode(ASTNode):
    """Reprezentuje komendę w AST"""

    def __init__(self, token: Token, name: str, params: Dict[str, Any]):
        """
        Inicjalizacja węzła komendy.

        Args:
            token: Token komendy
            name: Nazwa komendy
            params: Parametry komendy
        """
        super().__init__(token)
        self.name = name
        self.params = params

    def __str__(self) -> str:
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"Command({self.name}, {params_str})"


class AssignmentNode(ASTNode):
    """Reprezentuje przypisanie w AST"""

    def __init__(self, token: Token, variable: str, value: ASTNode):
        """
        Inicjalizacja węzła przypisania.

        Args:
            token: Token przypisania
            variable: Nazwa zmiennej
            value: Wartość przypisania (węzeł AST)
        """
        super().__init__(token)
        self.variable = variable
        self.value = value

    def __str__(self) -> str:
        return f"Assignment({self.variable} = {self.value})"


class VariableNode(ASTNode):
    """Reprezentuje zmienną w AST"""

    def __init__(self, token: Token, name: str):
        """
        Inicjalizacja węzła zmiennej.

        Args:
            token: Token zmiennej
            name: Nazwa zmiennej
        """
        super().__init__(token)
        self.name = name

    def __str__(self) -> str:
        return f"Variable({self.name})"


class LiteralNode(ASTNode):
    """Reprezentuje literał w AST (string, number, boolean)"""

    def __init__(self, token: Token, value: Any):
        """
        Inicjalizacja węzła literału.

        Args:
            token: Token literału
            value: Wartość literału
        """
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return f"Literal(\"{self.value}\")"
        return f"Literal({self.value})"


class BlockNode(ASTNode):
    """Reprezentuje blok kodu w AST"""

    def __init__(self, statements: List[ASTNode]):
        """
        Inicjalizacja węzła bloku.

        Args:
            statements: Lista węzłów AST reprezentujących instrukcje
        """
        super().__init__()
        self.statements = statements

    def __str__(self) -> str:
        return f"Block({len(self.statements)} statements)"


class ConditionalNode(ASTNode):
    """Reprezentuje instrukcję warunkową (if/else) w AST"""

    def __init__(self, token: Token, condition: ASTNode, true_block: BlockNode, false_block: BlockNode = None):
        """
        Inicjalizacja węzła instrukcji warunkowej.

        Args:
            token: Token instrukcji warunkowej
            condition: Warunek (węzeł AST)
            true_block: Blok wykonywany, gdy warunek jest prawdziwy
            false_block: Blok wykonywany, gdy warunek jest fałszywy (opcjonalny)
        """
        super().__init__(token)
        self.condition = condition
        self.true_block = true_block
        self.false_block = false_block

    def __str__(self) -> str:
        if self.false_block:
            return f"Conditional(if {self.condition} then {self.true_block} else {self.false_block})"
        return f"Conditional(if {self.condition} then {self.true_block})"


class LoopNode(ASTNode):
    """Reprezentuje pętlę (while/repeat) w AST"""

    def __init__(self, token: Token, condition: ASTNode, block: BlockNode, is_repeat: bool = False):
        """
        Inicjalizacja węzła pętli.

        Args:
            token: Token pętli
            condition: Warunek lub liczba powtórzeń (węzeł AST)
            block: Blok kodu wykonywany w pętli
            is_repeat: Czy to pętla repeat (True) czy while (False)
        """
        super().__init__(token)
        self.condition = condition
        self.block = block
        self.is_repeat = is_repeat

    def __str__(self) -> str:
        if self.is_repeat:
            return f"Loop(repeat {self.condition} times: {self.block})"
        return f"Loop(while {self.condition}: {self.block})"


class PipelineNode(ASTNode):
    """Reprezentuje pipeline w AST"""

    def __init__(self, token: Token, name: str, steps: List[CommandNode]):
        """
        Inicjalizacja węzła pipeline.

        Args:
            token: Token pipeline
            name: Nazwa pipeline
            steps: Lista kroków (węzły komend)
        """
        super().__init__(token)
        self.name = name
        self.steps = steps

    def __str__(self) -> str:
        return f"Pipeline({self.name}, {len(self.steps)} steps)"


# Słowa kluczowe DSL
KEYWORDS = {
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'repeat': TokenType.REPEAT,
    'pipeline': TokenType.PIPELINE,
    'end': TokenType.END,
    'true': TokenType.BOOLEAN,
    'false': TokenType.BOOLEAN
}

# Wzorce tokenów
TOKEN_PATTERNS = [
    (r'[ \t]+', TokenType.WHITESPACE),  # Białe znaki
    (r'\n', TokenType.NEWLINE),  # Nowa linia
    (r'#.*', TokenType.COMMENT),  # Komentarz
    (r';', TokenType.SEMICOLON),  # Średnik
    (r'\(', TokenType.OPEN_PAREN),  # Nawias otwierający
    (r'\)', TokenType.CLOSE_PAREN),  # Nawias zamykający
    (r'\{', TokenType.OPEN_BRACE),  # Nawias klamrowy otwierający
    (r'\}', TokenType.CLOSE_BRACE),  # Nawias klamrowy zamykający
    (r',', TokenType.COMMA),  # Przecinek
    (r':', TokenType.COLON),  # Dwukropek
    (r'\.', TokenType.DOT),  # Kropka
    (r'->', TokenType.ARROW),  # Strzałka
    (r'\|', TokenType.PIPE),  # Potok
    (r'=', TokenType.EQUALS),  # Znak przypisania
    (r'"([^"\\]|\\["\\])*"', TokenType.STRING),  # String w cudzysłowach
    (r'\'([^\'\\]|\\[\'\\])*\'', TokenType.STRING),  # String w apostrofach
    (r'-?\d+\.\d+', TokenType.NUMBER),  # Liczba zmiennoprzecinkowa
    (r'-?\d+', TokenType.NUMBER),  # Liczba całkowita
    (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER)  # Identyfikator
]

# Skompilowane wyrażenia regularne dla tokenizacji
COMPILED_PATTERNS = [(re.compile(pattern), token_type) for pattern, token_type in TOKEN_PATTERNS]

# Gramatyka DSL

# Definicja gramatyki w formie EBNF (Extended Backus-Naur Form):
"""
program        ::= statement*
statement      ::= command | assignment | conditional | loop | pipeline | block | comment
command        ::= IDENTIFIER "(" parameters? ")" ";"?
parameters     ::= parameter ("," parameter)*
parameter      ::= IDENTIFIER "=" expression
expression     ::= literal | variable | command
literal        ::= STRING | NUMBER | BOOLEAN
variable       ::= IDENTIFIER
assignment     ::= IDENTIFIER "=" expression ";"?
conditional    ::= "if" expression "{" statement* "}" ("else" "{" statement* "}")? ";"?
loop           ::= ("while" expression | "repeat" NUMBER) "{" statement* "}" ";"?
pipeline       ::= "pipeline" IDENTIFIER "{" pipeline_step+ "}" ";"?
pipeline_step  ::= command ("->" command)*
block          ::= "{" statement* "}" ";"?
comment        ::= "#" STRING
"""

# Przykłady poprawnych instrukcji w DSL:
"""
# Otwarcie aplikacji Firefox
open_application(name="firefox");

# Logowanie do LinkedIn
login_to_website(url="linkedin.com", username=env.LINKEDIN_USERNAME, password=env.LINKEDIN_PASSWORD);

# Pobranie wiadomości z emaila
emails = get_emails(from="test@email.com", max_count=1);
auth_code = extract_code(text=emails[0].body, regex="\\b\\d{6}\\b");

# Przypisanie wartości
x = 10;
result = perform_calculation(a=5, b=x);

# Instrukcja warunkowa
if screen_contains(image="login_button.png") {
    click(image="login_button.png");
} else {
    refresh_page();
}

# Pętla while
while not screen_contains(image="success.png") {
    wait(seconds=1);
}

# Pętla repeat
repeat 5 {
    click(x=100, y=200);
    wait(seconds=0.5);
}

# Pipeline
pipeline login_process {
    open_application(name="firefox") ->
    navigate_to(url="linkedin.com") ->
    type_text(selector="#username", text=env.LINKEDIN_USERNAME) ->
    type_text(selector="#password", text=env.LINKEDIN_PASSWORD) ->
    click(selector="#login-button");
}

# Wykonanie pipeline'u
execute_pipeline(name="login_process");
"""