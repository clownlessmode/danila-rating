"""
НейроРодион — проверка сообщений Данилы на соответствие моральным нормам.
"""

import json
from typing import Optional

import requests

# URL нейросети — укажи IP сервера в коде
API_URL = "http://10.1.1.15:1234/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

SYSTEM_PROMPT = """Ты — НейроРодион, модератор чата. Твоя задача — оценить, нарушает ли сообщение серьёзно моральные нормы.

Допустимо (НЕ штрафовать):
- "го курить", "как дела", обычный сленг
- Лёгкие оскорбления, мат в дружеском контексте
- Шутки, ирония, сарказм

Штрафовать -10 (ответь только ДА):
- Серьёзные угрозы, призывы к насилию
- Откровенная дискриминация, разжигание ненависти
- Крайне оскорбительный контент
- Что-то по-настоящему ужасное и недопустимое

Отвечай только одним словом: ДА или НЕТ. ДА — если нужно штрафовать, НЕТ — если сообщение допустимо."""


def is_message_bad(text: str, max_retries: int = 2) -> Optional[bool]:
    """
    Проверяет, нарушает ли сообщение моральные нормы.
    Возвращает True если штрафовать, False если ок, None при ошибке.
    """
    if not text or not text.strip():
        return False

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Сообщение для проверки: {text}"},
    ]

    for retry in range(max_retries):
        try:
            data = {
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 5,  # ДА/НЕТ — 2-3 буквы
            }
            response = requests.post(
                API_URL,
                headers=HEADERS,
                data=json.dumps(data),
                timeout=15,
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip().upper()
            return "ДА" in content or "YES" in content
        except Exception as e:
            if retry == max_retries - 1:
                return None
            continue
    return None
