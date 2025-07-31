import logging
import aiohttp
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

async def extract_doc_fields_with_gpt(raw_text: str, prompt: str):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    full_prompt = prompt + raw_text
    data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": full_prompt}],
        "max_tokens": 512,
        "temperature": 0.1
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                res = await resp.json()
                if "error" in res:
                    logger.error(f"ChatGPT API error {resp.status}: {res['error']}")
                    return "Ошибка при обработке документа (AI API)."
                return res["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Ошибка при AI-сортировке: {e}", exc_info=True)
        return "Ошибка при обработке документа (AI)."
