import pyautogui
import subprocess
import time
import platform
import paramiko
import re
import json
import logging
from PIL import Image, ImageGrab
import pytesseract
import cv2
import numpy as np
import os
import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import argparse
from dotenv import load_dotenv

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automatyzer_desktop.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AutomationBot")


class AutomationBot:
    def __init__(self, env_file='.env'):
        # Załaduj zmienne środowiskowe
        load_dotenv(env_file)

        # Konfiguracja podstawowa
        self.delay = float(os.environ.get('DELAY_BETWEEN_ACTIONS', '0.5'))
        self.screenshot_folder = os.environ.get('SCREENSHOT_FOLDER', 'screenshots')

        # Upewnij się, że folder na zrzuty ekranu istnieje
        os.makedirs(self.screenshot_folder, exist_ok=True)

        # Konfiguracja Tesseract OCR dla Windows
        if platform.system() == 'Windows':
            tesseract_path = os.environ.get('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def connect_rdp(self, host=None, username=None, password=None, port=None, resolution=None):
        """Nawiązuje połączenie przez RDP z odległym komputerem"""
        if not host:
            host = os.environ.get('RDP_HOST', 'localhost')
        if not username:
            username = os.environ.get('RDP_USERNAME', '')
        if not password:
            password = os.environ.get('RDP_PASSWORD', '')
        if not port:
            port = os.environ.get('RDP_PORT', '3389')
        if not resolution:
            resolution = os.environ.get('RDP_RESOLUTION', '1920x1080')

        if platform.system() == 'Windows':
            # Użycie wbudowanego klienta RDP na Windows
            command = f'mstsc /v:{host}:{port} /w:{resolution.split("x")[0]} /h:{resolution.split("x")[1]}'
            if username:
                command += f' /u:{username}'
            if password:
                # Uwaga: przekazywanie hasła w ten sposób nie jest bezpieczne
                # W prawdziwym zastosowaniu należy używać bardziej bezpiecznych metod
                command += f' /p:{password}'

            logger.info(f"Łączenie przez RDP do {host}:{port}")
            subprocess.Popen(command, shell=True)
            time.sleep(5)  # Czekaj na nawiązanie połączenia

        elif platform.system() == 'Linux':
            # Użycie klienta FreeRDP na Linux
            command = f'xfreerdp /v:{host}:{port} /size:{resolution} /u:{username} /p:{password} /cert-ignore'
            logger.info(f"Łączenie przez RDP do {host}:{port}")
            subprocess.Popen(command, shell=True)
            time.sleep(5)  # Czekaj na nawiązanie połączenia

        elif platform.system() == 'Darwin':  # macOS
            # Na macOS można użyć Microsoft Remote Desktop
            logger.warning("Na macOS zalecane jest ręczne połączenie przez Microsoft Remote Desktop")

        else:
            logger.error(f"Nieobsługiwany system operacyjny: {platform.system()}")
            return False

        return True

    def execute_shell_command(self, command, remote_host=None, remote_user=None, remote_password=None):
        """Wykonuje komendę powłoki lokalnie lub na zdalnym hoście przez SSH"""
        if not remote_host and not remote_user:
            remote_host = os.environ.get('SSH_HOST', '')
            remote_user = os.environ.get('SSH_USERNAME', '')
            remote_password = os.environ.get('SSH_PASSWORD', '')

        if remote_host:
            # Wykonanie komendy na zdalnym hoście przez SSH
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    remote_host,
                    username=remote_user,
                    password=remote_password
                )
                stdin, stdout, stderr = client.exec_command(command)
                result = stdout.read().decode()
                error = stderr.read().decode()
                client.close()

                if error:
                    logger.error(f"Błąd podczas wykonywania komendy na zdalnym hoście: {error}")
                    return False, error

                logger.info(f"Komenda wykonana pomyślnie na zdalnym hoście")
                return True, result

            except Exception as e:
                logger.error(f"Nie udało się wykonać komendy przez SSH: {str(e)}")
                return False, str(e)
        else:
            # Wykonanie komendy lokalnie
            try:
                result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode()
                logger.info(f"Komenda lokalna wykonana pomyślnie")
                return True, result
            except subprocess.CalledProcessError as e:
                logger.error(f"Błąd podczas wykonywania lokalnej komendy: {e.output.decode()}")
                return False, e.output.decode()

    def take_screenshot(self, filename=None):
        """Wykonuje zrzut ekranu i zapisuje go do pliku"""
        if not filename:
            filename = f"{self.screenshot_folder}/screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"

        screenshot = ImageGrab.grab()
        screenshot.save(filename)
        logger.info(f"Zapisano zrzut ekranu: {filename}")
        return filename

    def find_image_on_screen(self, image_path, confidence=0.8):
        """Szuka obrazu na ekranie i zwraca jego pozycję"""
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                return (location.left + location.width / 2, location.top + location.height / 2)
            else:
                logger.warning(f"Nie znaleziono obrazu: {image_path}")
                return None
        except Exception as e:
            logger.error(f"Błąd podczas szukania obrazu: {str(e)}")
            return None

    def click(self, x=None, y=None, image_path=None, double=False):
        """Klika w określonym miejscu lub na znalezionym obrazie"""
        if image_path:
            position = self.find_image_on_screen(image_path)
            if position:
                x, y = position
            else:
                logger.error(f"Nie można kliknąć - obraz nie znaleziony: {image_path}")
                return False

        if x is not None and y is not None:
            pyautogui.moveTo(x, y)
            time.sleep(self.delay)
            if double:
                pyautogui.doubleClick()
            else:
                pyautogui.click()
            logger.info(f"Kliknięto w pozycji ({x}, {y})")
            return True
        else:
            logger.error("Nie można kliknąć - brak współrzędnych")
            return False

    def right_click(self, x=None, y=None, image_path=None):
        """Wykonuje kliknięcie prawym przyciskiem myszy"""
        if image_path:
            position = self.find_image_on_screen(image_path)
            if position:
                x, y = position
            else:
                logger.error(f"Nie można kliknąć prawym przyciskiem - obraz nie znaleziony: {image_path}")
                return False

        if x is not None and y is not None:
            pyautogui.moveTo(x, y)
            time.sleep(self.delay)
            pyautogui.rightClick()
            logger.info(f"Kliknięto prawym przyciskiem w pozycji ({x}, {y})")
            return True
        else:
            logger.error("Nie można kliknąć prawym przyciskiem - brak współrzędnych")
            return False

    def double_click(self, x=None, y=None, image_path=None):
        """Wykonuje podwójne kliknięcie"""
        return self.click(x, y, image_path, double=True)

    def type_text(self, text):
        """Wpisuje tekst"""
        pyautogui.write(text)
        logger.info(f"Wpisano tekst: {text}")
        time.sleep(self.delay)
        return True

    def press_key(self, key):
        """Naciska określony klawisz"""
        pyautogui.press(key)
        logger.info(f"Naciśnięto klawisz: {key}")
        time.sleep(self.delay)
        return True

    def press_hotkey(self, *keys):
        """Naciska kombinację klawiszy"""
        pyautogui.hotkey(*keys)
        logger.info(f"Naciśnięto kombinację klawiszy: {keys}")
        time.sleep(self.delay)
        return True

    def get_text_from_region(self, left, top, width, height):
        """Odczytuje tekst z określonego obszaru ekranu za pomocą OCR"""
        screenshot = ImageGrab.grab(bbox=(left, top, left + width, top + height))
        screenshot_path = f"{self.screenshot_folder}/ocr_region_{time.strftime('%Y%m%d_%H%M%S')}.png"
        screenshot.save(screenshot_path)

        text = pytesseract.image_to_string(screenshot)
        logger.info(f"Odczytano tekst z obszaru: {text}")
        return text

    def get_email(self, email_address, subject_filter=None, max_emails=1):
        """Pobiera wiadomości z określonego adresu email"""
        try:
            # Konfiguracja z pliku .env
            server = os.environ.get('EMAIL_IMAP_SERVER', '')
            port = int(os.environ.get('EMAIL_PORT', '993'))
            username = os.environ.get('EMAIL_USERNAME', '')
            password = os.environ.get('EMAIL_PASSWORD', '')

            # Połączenie z serwerem IMAP
            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(username, password)
            mail.select('inbox')

            search_criteria = f'FROM "{email_address}"'
            if subject_filter:
                search_criteria += f' SUBJECT "{subject_filter}"'

            status, data = mail.search(None, search_criteria)
            mail_ids = data[0].split()

            emails = []
            count = 0

            # Rozpocznij od najnowszych wiadomości
            for email_id in reversed(mail_ids):
                if count >= max_emails:
                    break

                status, data = mail.fetch(email_id, '(RFC822)')
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Dekodowanie tematu
                subject, encoding = decode_header(msg['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')

                # Dekodowanie nadawcy
                from_, encoding = decode_header(msg.get('From'))[0]
                if isinstance(from_, bytes):
                    from_ = from_.decode(encoding if encoding else 'utf-8')

                # Odczytanie treści wiadomości
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get('Content-Disposition'))

                        if 'attachment' not in content_disposition:
                            if content_type == 'text/plain':
                                body_part = part.get_payload(decode=True)
                                charset = part.get_content_charset()
                                if charset:
                                    body += body_part.decode(charset)
                                else:
                                    body += body_part.decode()
                else:
                    body = msg.get_payload(decode=True).decode()

                emails.append({
                    'subject': subject,
                    'from': from_,
                    'body': body,
                    'date': msg['Date']
                })

                count += 1

            mail.close()
            mail.logout()

            if emails:
                logger.info(f"Pobrano {len(emails)} wiadomości email")
                return emails
            else:
                logger.warning(f"Nie znaleziono wiadomości od {email_address}")
                return []

        except Exception as e:
            logger.error(f"Błąd podczas pobierania email: {str(e)}")
            return []

    def extract_code_from_email(self, email_body, regex_pattern=None):
        """Wyciąga kod z treści wiadomości email za pomocą wyrażenia regularnego"""
        if regex_pattern is None:
            regex_pattern = os.environ.get('AUTH_CODE_REGEX', r'\b\d{6}\b')

        match = re.search(regex_pattern, email_body)
        if match:
            code = match.group(0)
            logger.info(f"Znaleziono kod: {code}")
            return code
        else:
            logger.warning(f"Nie znaleziono kodu pasującego do wzorca: {regex_pattern}")
            return None

    def wait_for_image(self, image_path, timeout=30, confidence=0.8):
        """Czeka na pojawienie się obrazu na ekranie przez określony czas"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            position = self.find_image_on_screen(image_path, confidence)
            if position:
                logger.info(f"Znaleziono obraz: {image_path}")
                return position
            time.sleep(1)

        logger.warning(f"Nie znaleziono obrazu: {image_path} w czasie {timeout} sekund")
        return None

    def open_application(self, app_name, system_type=None):
        """Otwiera aplikację o podanej nazwie"""
        if not system_type:
            system_type = platform.system()

        if system_type.lower() == 'windows':
            # Na systemie Windows
            # Próba otwarcia przez menu Start
            pyautogui.press('win')
            time.sleep(self.delay)
            pyautogui.write(app_name)
            time.sleep(self.delay)
            pyautogui.press('enter')

        elif system_type.lower() == 'linux':
            # Na systemie Linux
            subprocess.Popen(app_name, shell=True)

        elif system_type.lower() == 'darwin':
            # Na systemie macOS
            subprocess.Popen(['open', '-a', app_name])

        logger.info(f"Otwarto aplikację: {app_name}")
        time.sleep(2)  # Czekaj na uruchomienie aplikacji
        return True

    def execute_task(self, task_description):
        """Przetwarza i wykonuje zadanie opisane tekstem"""
        # Rozpoznawanie różnych typów zadań

        # Otwieranie aplikacji
        match = re.search(r'otworz (?:aplikacje|program|aplikację|program) (?:o nazwie )?(.+?)(?:\s|$)',
                          task_description, re.IGNORECASE)
        if match:
            app_name = match.group(1).strip()
            return self.open_application(app_name)

        # Logowanie do portalu
        match = re.search(r'zaloguj (?:sie|się) do (?:portalu|strony) (.+)', task_description, re.IGNORECASE)
        if match:
            portal = match.group(1).strip()

            # Przykład dla LinkedIn
            if 'linkedin' in portal.lower():
                # Czekaj na pojawienie się pola logowania
                username_field = self.wait_for_image('linkedin_username_field.png')
                if username_field:
                    self.click(username_field[0], username_field[1])
                    # Pobierz dane logowania z pliku .env
                    username = os.environ.get('LINKEDIN_USERNAME', '')
                    if username:
                        self.type_text(username)
                    else:
                        logger.error("Brak nazwy użytkownika dla LinkedIn w pliku .env")
                        return False

                    # Przejdź do pola hasła
                    self.press_key('tab')

                    password = os.environ.get('LINKEDIN_PASSWORD', '')
                    if password:
                        self.type_text(password)
                    else:
                        logger.error("Brak hasła dla LinkedIn w pliku .env")
                        return False

                    # Kliknij przycisk zaloguj
                    login_button = self.wait_for_image('linkedin_login_button.png')
                    if login_button:
                        self.click(login_button[0], login_button[1])
                        return True
                return False

        # Pobieranie emaila i wyciąganie kodu
        match = re.search(
            r'pobierz z programu pocztowego ze skrzynki (.+?) ostatni(?:a|ą)? wiadomos(?:c|ć) aby wpisac kod',
            task_description, re.IGNORECASE)
        if match:
            email_address = match.group(1).strip()

            # Pobierz ostatnią wiadomość
            emails = self.get_email(email_address, max_emails=1)
            if emails:
                # Wyciągnij kod z wiadomości
                code = self.extract_code_from_email(emails[0]['body'])
                if code:
                    # Wpisz kod (zakładając, że pole do wpisania kodu jest aktywne)
                    self.type_text(code)
                    return True
            return False

        # Jeśli nie rozpoznano zadania
        logger.warning(f"Nie rozpoznano zadania: {task_description}")
        return False

    def run_script(self, script_file):
        """Wykonuje skrypt zadań z pliku"""
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                logger.info(f"Wykonywanie zadania: {line}")
                result = self.execute_task(line)

                if not result:
                    logger.error(f"Nie udało się wykonać zadania: {line}")
                    stop_on_error = os.environ.get('STOP_ON_ERROR', 'False').lower() == 'true'
                    if stop_on_error:
                        break
            return True

        except Exception as e:
            logger.error(f"Błąd podczas wykonywania skryptu: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Bot do automatyzacji zadań przez Remote Desktop')
    parser.add_argument('--env', type=str, default='.env', help='Ścieżka do pliku .env')
    parser.add_argument('--script', type=str, help='Ścieżka do pliku ze skryptem zadań')
    parser.add_argument('--task', type=str, help='Zadanie do wykonania (opisane tekstem)')
    parser.add_argument('--rdp-host', type=str, help='Host do połączenia RDP (nadpisuje wartość z .env)')
    parser.add_argument('--rdp-user', type=str, help='Nazwa użytkownika RDP (nadpisuje wartość z .env)')
    parser.add_argument('--rdp-pass', type=str, help='Hasło RDP (nadpisuje wartość z .env)')

    args = parser.parse_args()

    # Inicjalizacja bota
    bot = AutomationBot(env_file=args.env)

    # Połączenie RDP jeśli podano parametry lub są w .env
    if args.rdp_host or os.environ.get('RDP_HOST'):
        bot.connect_rdp(
            host=args.rdp_host,
            username=args.rdp_user,
            password=args.rdp_pass
        )

    # Wykonanie zadania lub skryptu
    if args.task:
        bot.execute_task(args.task)
    elif args.script:
        bot.run_script(args.script)
    else:
        print("Nie podano zadania ani skryptu do wykonania. Użyj --task lub --script")
        parser.print_help()

if __name__ == "__main__":
    main()
