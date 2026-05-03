#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Instalacja pakietu automatyzer_desktop.
"""

import os
import platform
from setuptools import setup, find_packages

# Wymagane zależności
REQUIRED = [
    'python-dotenv>=0.21.0',
    'psutil>=5.9.0',
    'pyautogui>=0.9.53',
    'pillow>=9.2.0',
    'numpy>=1.23.0',
    'opencv-python>=4.6.0',
    'pytesseract>=0.3.10',
    'pyperclip>=1.8.2',
    'paramiko>=2.11.0',
    'imaplib2>=3.6',
    'email-validator>=1.2.1',
]

# Dodatkowe zależności w zależności od systemu operacyjnego
if platform.system() == 'Windows':
    REQUIRED.append('pygetwindow>=0.0.9')
else:
    REQUIRED.append('pywinctl>=0.0.5')

# Dodatkowe zależności dla NLP
NLP = [
    'spacy>=3.4.0',
    'transformers>=4.24.0',
    'torch>=1.13.0',
    'SpeechRecognition>=3.8.1',
    'pyaudio>=0.2.12',
    'python-Levenshtein>=0.12.2',
]

# TensorFlow ma inne wersje w zależności od platformy i wersji Pythona
if platform.system() == 'Windows' and platform.python_version() >= '3.10':
    NLP.append('tensorflow-cpu>=2.10.0')
else:
    NLP.append('tensorflow>=2.10.0')

# Dodatkowe narzędzia
EXTRAS = {
    'nlp': NLP,
    'data': [
        'pandas>=1.5.0',
        'matplotlib>=3.6.0',
        'seaborn>=0.12.0',
        'scikit-learn>=1.1.0',
    ],
    'test': [
        'pytest>=7.2.0',
        'pytest-cov>=4.0.0',
        'pytest-mock>=3.10.0',
    ],
    'dev': [
        'black',
        'isort',
        'flake8',
        'mypy',
        'pre-commit',
    ]
}

# Pełna instalacja
EXTRAS['all'] = [pkg for group in EXTRAS.values() for pkg in group]

# Długi opis z pliku README.md
try:
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.md"), encoding="utf-8") as f:
        LONG_DESCRIPTION = '\n' + f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = ''

# Konfiguracja instalacji
setup(
    name="automatyzer_desktop",
    version="0.1.8",
    description="Bot do automatyzacji zadań poprzez Remote Desktop",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Tom Sapletta",
    author_email="info@softreck.dev",
    python_requires=">=3.7.0",
    url="https://github.com/automatyzer/desktop",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="MIT",
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    entry_points={
        'console_scripts': [
            'automatyzer_desktop=automatyzer_desktop.cli.main:main',
        ],
    },
)
