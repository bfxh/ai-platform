from bot import AutomationBot
import os
import re
import os
from dotenv import load_dotenv
from bot import AutomationBot

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Inicjalizacja bota
bot = AutomationBot()

# Połączenie z RDP (dane pobierane automatycznie z .env)
bot.connect_rdp()

# Wykonanie zadania
bot.execute_task("otworz aplikacje o nazwie firefox i zaloguj sie do portalu linkedin")

# Stworzenie instancji bota
# bot = AutomationBot()
#
# # Połączenie przez RDP
# bot.connect_rdp(host="w11", username="tom", password="Tom4Win11")
#
# # Przykład wykonania zadania z Twojego przykładu
# bot.execute_task("otworz aplikacje o nazwie firefox i zaloguj sie do portalu linkedin")
# bot.execute_task("pobierz z programu pocztowego ze skrzynki test@email.com ostatnia wiadomosci aby wpisac kod z wiadomosci do uwierzytelnienia")