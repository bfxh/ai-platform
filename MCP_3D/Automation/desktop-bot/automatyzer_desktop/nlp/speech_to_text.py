#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł do konwersji mowy na tekst.
Umożliwia przechwytywanie i rozpoznawanie komend głosowych.
"""

import os
import tempfile
import logging
import time
from typing import Optional, Callable, Dict, List, Any, Union
import queue
import threading
import numpy as np

# Obsługa wyjątków dla różnych bibliotek (mogą nie być zainstalowane)
try:
    import speech_recognition as sr

    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyaudio

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import torch
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class SpeechToText:
    """
    Klasa do konwersji mowy na tekst.
    Obsługuje różne metody rozpoznawania mowy.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicjalizacja konwertera mowy na tekst.

        Args:
            config: Konfiguracja (opcjonalna)
        """
        self.logger = logging.getLogger(__name__)

        # Domyślna konfiguracja
        self.config = {
            "engine": "google",  # Silnik rozpoznawania mowy: google, whisper, sphinx
            "language": "pl-PL",  # Język rozpoznawania (kod BCP-47)
            "device_index": None,  # Indeks urządzenia audio (None = domyślne)
            "energy_threshold": 4000,  # Próg energii dla wykrywania mowy
            "pause_threshold": 0.8,  # Próg przerwy (w sekundach)
            "dynamic_energy_threshold": True,  # Dynamiczne dostosowanie progu energii
            "non_speaking_duration": 0.5,  # Czas ciszy uznawany za koniec wypowiedzi (w sekundach)
            "whisper_model": "small",  # Model whisper: tiny, base, small, medium, large
            # Opcje dla trybu nasłuchiwania
            "keyword": "bot",  # Słowo kluczowe aktywujące bota
            "keyword_threshold": 0.5,  # Próg pewności dla słowa kluczowego
            "continuous_listening": False,  # Ciągłe nasłuchiwanie
            "timeout": 5,  # Limit czasu oczekiwania na komendę (w sekundach)
        }

        # Aktualizacja konfiguracji z podanych wartości
        if config:
            self.config.update(config)

        # Sprawdzenie dostępności wymaganych bibliotek
        if not SPEECH_RECOGNITION_AVAILABLE:
            self.logger.error("Biblioteka speech_recognition nie jest zainstalowana!")
            raise ImportError("Zainstaluj bibliotekę 'speech_recognition' za pomocą 'pip install SpeechRecognition'")

        # Inicjalizacja rozpoznawania mowy
        self.recognizer = sr.Recognizer()
        self.microphone = None

        # Dostosowanie parametrów rozpoznawania
        self.recognizer.energy_threshold = self.config["energy_threshold"]
        self.recognizer.pause_threshold = self.config["pause_threshold"]
        self.recognizer.dynamic_energy_threshold = self.config["dynamic_energy_threshold"]
        self.recognizer.non_speaking_duration = self.config["non_speaking_duration"]

        # Inicjalizacja modelu whisper (jeśli wybrany)
        self.whisper_pipeline = None
        if self.config["engine"] == "whisper" and WHISPER_AVAILABLE:
            self._initialize_whisper()

        # Zmienne dla trybu nasłuchiwania
        self.command_queue = queue.Queue()
        self.listening_thread = None
        self.is_listening = False
        self.stop_listening = threading.Event()

    def _initialize_whisper(self) -> None:
        """
        Inicjalizuje model Whisper do rozpoznawania mowy.
        """
        try:
            self.logger.info(f"Inicjalizacja modelu Whisper {self.config['whisper_model']}...")

            # Sprawdź dostępność CUDA
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            # Inicjalizacja modelu
            model_id = f"openai/whisper-{self.config['whisper_model']}"
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True
            )
            model.to(device)

            # Inicjalizacja procesora
            processor = AutoProcessor.from_pretrained(model_id)

            # Stworzenie pipeline
            self.whisper_pipeline = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=30,
                batch_size=16,
                return_timestamps=False,
                torch_dtype=torch_dtype,
                device=device,
            )

            self.logger.info(f"Model Whisper został zainicjalizowany (urządzenie: {device})")
        except Exception as e:
            self.logger.error(f"Błąd inicjalizacji modelu Whisper: {str(e)}")
            self.whisper_pipeline = None

    def recognize_from_microphone(self) -> Optional[str]:
        """
        Nagrywa i rozpoznaje mowę z mikrofonu.

        Returns:
            Rozpoznany tekst lub None w przypadku błędu
        """
        if not PYAUDIO_AVAILABLE:
            self.logger.error("Biblioteka pyaudio nie jest zainstalowana!")
            raise ImportError("Zainstaluj bibliotekę 'pyaudio' za pomocą 'pip install pyaudio'")

        # Inicjalizacja mikrofonu (jeśli jeszcze nie zainicjalizowany)
        if self.microphone is None:
            self.microphone = sr.Microphone(device_index=self.config["device_index"])

            # Dostosowanie progu energii do szumu otoczenia
            if self.config["dynamic_energy_threshold"]:
                with self.microphone as source:
                    self.logger.info("Dostosowywanie do szumu otoczenia...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    self.logger.info(f"Próg energii dostosowany do: {self.recognizer.energy_threshold}")

        # Nagrywanie i rozpoznawanie
        try:
            with self.microphone as source:
                self.logger.info("Nasłuchiwanie...")
                audio = self.recognizer.listen(source, timeout=self.config["timeout"])

            return self._process_audio(audio)

        except sr.WaitTimeoutError:
            self.logger.warning("Przekroczony czas oczekiwania na mowę")
            return None
        except sr.UnknownValueError:
            self.logger.warning("Nie rozpoznano mowy")
            return None
        except Exception as e:
            self.logger.error(f"Błąd podczas rozpoznawania mowy: {str(e)}")
            return None

    def recognize_from_file(self, file_path: str) -> Optional[str]:
        """
        Rozpoznaje mowę z pliku audio.

        Args:
            file_path: Ścieżka do pliku audio

        Returns:
            Rozpoznany tekst lub None w przypadku błędu
        """
        try:
            with sr.AudioFile(file_path) as source:
                audio = self.recognizer.record(source)

            return self._process_audio(audio)

        except Exception as e:
            self.logger.error(f"Błąd podczas rozpoznawania mowy z pliku: {str(e)}")
            return None

    def _process_audio(self, audio: sr.AudioData) -> Optional[str]:
        """
        Przetwarza dane audio na tekst w zależności od wybranego silnika.

        Args:
            audio: Dane audio

        Returns:
            Rozpoznany tekst lub None w przypadku błędu
        """
        engine = self.config["engine"]

        try:
            if engine == "google":
                return self.recognizer.recognize_google(audio, language=self.config["language"])

            elif engine == "whisper":
                if self.whisper_pipeline is None:
                    if WHISPER_AVAILABLE:
                        self._initialize_whisper()
                    else:
                        raise ImportError("Whisper nie jest dostępny. Zainstaluj wymagane biblioteki.")

                # Konwersja audio do formatu obsługiwanego przez Whisper
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                    temp_path = temp_file.name
                    with open(temp_path, "wb") as f:
                        f.write(audio.get_wav_data())

                    # Rozpoznanie tekstu
                    result = self.whisper_pipeline(temp_path, language=self.config["language"][:2])
                    return result["text"]

            elif engine == "sphinx":
                return self.recognizer.recognize_sphinx(audio, language=self.config["language"])

            else:
                self.logger.error(f"Nieznany silnik rozpoznawania mowy: {engine}")
                return None

        except sr.UnknownValueError:
            self.logger.warning("Nie rozpoznano mowy")
            return None
        except Exception as e:
            self.logger.error(f"Błąd podczas rozpoznawania mowy ({engine}): {str(e)}")
            return None

    def start_listening(self, callback: Callable[[str], None]) -> bool:
        """
        Rozpoczyna ciągłe nasłuchiwanie komend w osobnym wątku.

        Args:
            callback: Funkcja wywoływana dla każdej rozpoznanej komendy

        Returns:
            True jeśli rozpoczęto nasłuchiwanie, False w przypadku błędu
        """
        if not PYAUDIO_AVAILABLE:
            self.logger.error("Biblioteka pyaudio nie jest zainstalowana!")
            return False

        if self.is_listening:
            self.logger.warning("Nasłuchiwanie jest już aktywne")
            return True

        # Reset flag
        self.stop_listening.clear()
        self.is_listening = True

        # Uruchomienie wątku nasłuchiwania
        self.listening_thread = threading.Thread(
            target=self._listening_worker,
            args=(callback,),
            daemon=True
        )
        self.listening_thread.start()

        self.logger.info("Rozpoczęto nasłuchiwanie komend")
        return True

    def stop_listening_thread(self) -> None:
        """
        Zatrzymuje wątek nasłuchiwania.
        """
        if not self.is_listening:
            return

        self.stop_listening.set()
        self.is_listening = False

        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=2.0)

        self.logger.info("Zatrzymano nasłuchiwanie komend")

    def _listening_worker(self, callback: Callable[[str], None]) -> None:
        """
        Funkcja wątku nasłuchiwania komend.

        Args:
            callback: Funkcja wywoływana dla każdej rozpoznanej komendy
        """
        # Inicjalizacja mikrofonu (jeśli jeszcze nie zainicjalizowany)
        if self.microphone is None:
            self.microphone = sr.Microphone(device_index=self.config["device_index"])

            # Dostosowanie progu energii do szumu otoczenia
            with self.microphone as source:
                self.logger.info("Dostosowywanie do szumu otoczenia...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.logger.info(f"Próg energii dostosowany do: {self.recognizer.energy_threshold}")

        continuous_mode = self.config["continuous_listening"]
        keyword = self.config["keyword"].lower()
        waiting_for_command = False

        with self.microphone as source:
            while not self.stop_listening.is_set():
                try:
                    # Nasłuchiwanie mowy
                    audio = self.recognizer.listen(source, timeout=self.config["timeout"], phrase_time_limit=10)

                    # Rozpoznawanie mowy
                    text = self._process_audio(audio)

                    if not text:
                        continue

                    text = text.lower()
                    self.logger.debug(f"Rozpoznano: {text}")

                    # Tryb ciągły lub wykryto słowo kluczowe
                    if continuous_mode or waiting_for_command or keyword in text:
                        if not continuous_mode and not waiting_for_command:
                            # Aktywowano bota słowem kluczowym, czekaj na właściwą komendę
                            waiting_for_command = True
                            continue

                        # Wykonanie callback z rozpoznanym tekstem
                        callback(text)

                        # Reset flagi oczekiwania na komendę
                        waiting_for_command = False

                except sr.WaitTimeoutError:
                    # Timeout jest normalny w trybie nasłuchiwania
                    waiting_for_command = False
                    continue
                except Exception as e:
                    self.logger.error(f"Błąd podczas nasłuchiwania: {str(e)}")
                    time.sleep(1)  # Krótka przerwa przed kolejną próbą