import logging
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_to_supabase(data: dict, table_name="passport_applications"):
    try:
        for key in data:
            if data[key] is None:
                data[key] = ""
            elif not isinstance(data[key], str):
                data[key] = str(data[key])
        response = supabase.table(table_name).insert([data]).execute()
        if hasattr(response, "error") and response.error:
            logger.error(f"Supabase Insert Error: {response.error}")
            return False
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения в Supabase: {e}", exc_info=True)
        return False
