import re

def parse_migration_fields(text: str):
    res = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if "Серия карты" in key:
            res["migration_card_series"] = val
        elif "Номер карты" in key:
            res["migration_card_number"] = val
        elif "Дата выдачи" in key:
            res["migration_card_date"] = val
        elif "Цель визита" in key:
            res["migration_card_purpose"] = val
    return res

def parse_patent_fields(text: str):
    # Упрощённая (исходная) версия: парсим только строки формата 'Ключ: Значение'.
    # Это возвращает стабильность: меньше ложных срабатываний и не ломает корректные GPT-ответы.
    res = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if "Серия патента" in key:
            res["patent_series"] = val
        elif "Номер патента" in key:
            res["patent_number"] = val
        elif "Дата выдачи" in key:
            res["patent_date"] = val
        elif "Кем выдан" in key:
            res["patent_issuer"] = val
        elif "ФИО" in key and "латиницей" not in key:
            res["fio"] = val
        elif "Серия и номер бланка" in key:
            res["patent_blank"] = val
        elif "ИНН" in key:
            res["inn"] = val
    return res

def parse_passport_fields(text: str):
    res = {}
    # Флаг таджикского паспорта (по ключевой фразе или по наличию спец-поля)
    t = text.lower()
    is_tajik = ("таджик" in t) or ("номер (таджик" in t)

    # Нормализация значений, которые считаются отсутствующими
    def is_missing(v: str) -> bool:
        if v is None:
            return True
        s = str(v).strip().lower()
        return s in {"не найдено", "не найден", "не указано", "нет", "n/a", "none", "null", "-", "—", "not found"}

    for line in text.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        kl = key.lower()

        if key == "ФИО":
            res["fio"] = val.upper()
        elif "дата рождения" in kl:
            res["birthdate"] = val
        elif "место рождения" in kl:
            if "FERGANA" in val.upper():
                res["birth_place"] = "ФЕРГАНСКАЯ ОБЛАСТЬ"
            else:
                res["birth_place"] = val.upper()
        elif "пол" in kl:
            uv = val.upper()
            res["sex"] = "МУЖСКОЙ" if uv in {"M", "М", "МУЖ", "MALE"} else ("ЖЕНСКИЙ" if uv in {"F", "Ж", "ЖЕН", "FEMALE"} else uv)
        # Серия: не пишем для таджикского паспорта
        elif (key == "Серия" or ("серия" in kl and "паспорт" in kl)) and not is_tajik:
            if not is_missing(val) and val.strip().lower() not in {"нет"}:
                res["passport_series"] = val.upper()
        # Номер (таджикский): приоритетно пишем в passport_number
        elif "номер (таджик" in kl:
            if not is_missing(val):
                res["passport_number"] = val.upper()
        # Универсальный номер
        elif ("номер" in kl and "паспорт" in kl) or key == "Номер":
            if not is_missing(val):
                res["passport_number"] = val.upper()
        elif "дата" in kl and ("выдач" in kl or "passport" in kl):
            res["issue_date"] = val
        elif "срок действия" in kl or "действителен до" in kl:
            res["expiry_date"] = val
        elif "кем выдан" in kl or "authority" in kl:
            if "МВД" in val.upper():
                mvd_pos = val.upper().find("МВД")
                if mvd_pos != -1:
                    after_mvd = val[mvd_pos + 3:].strip()
                    nums = ''.join(filter(str.isdigit, after_mvd))
                    res["authority"] = f"МВД {nums}" if nums else "МВД"
                else:
                    res["authority"] = val.strip()
            else:
                nums = ''.join(filter(str.isdigit, val))
                res["authority"] = f"МВД {nums}" if nums else val.strip()
        elif "страна" in kl or "гражданство" in kl:
            v = val.upper().strip()
            mapping = {
                "UZBEKISTAN": "УЗБЕКИСТАН",
                "REPUBLIC OF UZBEKISTAN": "УЗБЕКИСТАН",
                "УЗБЕКИСТАН": "УЗБЕКИСТАН",
                "TAJIKISTAN": "ТАДЖИКИСТАН",
                "REPUBLIC OF TAJIKISTAN": "ТАДЖИКИСТАН",
                "ТАДЖИКИСТАН": "ТАДЖИКИСТАН",
                "ТАДЖИКСКАЯ РЕСПУБЛИКА": "ТАДЖИКИСТАН",
            }
            res["nationality"] = mapping.get(v, v)
        elif "мрз" in kl or "mrz" in kl:
            res["mrz"] = val.upper()

    # Если это таджикский паспорт — серия должна быть пустой
    if is_tajik:
        res.pop("passport_series", None)

    return res

def parse_dms_fields(text: str):
    res = {}
    lines = text.splitlines()

    # Разбор строк с двоеточием для извлечения ключевых данных
    for line in lines:
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        lk = key.lower()

        if ("email" in lk or "почта" in lk or "e-mail" in lk) or "@" in val:
            res['insurance_expiry'] = val
        elif "телефон" in lk or "phone" in lk:
            res['phone'] = val
        elif "номер" in lk and ("полис" in lk or "дмс" in lk or "страхов" in lk):
            res['dms_number'] = val
        elif "дата" in lk and ("выдач" in lk or "полис" in lk or "дмс" in lk or "страхов" in lk or "начал" in lk):
            res['insurance_date'] = val
        elif (("страховая компания" in lk or "страховщик" in lk or ("компан" in lk and "страхов" in lk) or 
              "insurance company" in lk or "insurer" in lk) and "@" not in val and "телефон" not in lk):
            # Новый формат ответа GPT: "Страховая компания: <название>" или "Insurance company: <название>"
            if val and val != "Не найдено":
                res['insurance_company'] = val

    full_text = " ".join(lines)

    # УНИВЕРСАЛЬНОЕ ИЗВЛЕЧЕНИЕ НАЗВАНИЯ СТРАХОВОЙ КОМПАНИИ
    if 'insurance_company' not in res:
        # Стратегия 1: Поиск известных страховых компаний
        known_companies = [
            r'(?:ООО\s+)?(?:Страховая\s+компания\s+)?СОГАЗ(?:\s+МЕДИЦИНА)?',
            r'(?:ООО\s+)?ИНГОССТРАХ(?:-М)?',
            r'(?:ООО\s+)?РЕСО-Гарантия',
            r'(?:ООО\s+)?(?:СК\s+)?Альфа-Страхование',
            r'(?:ПАО\s+)?Росгосстрах',
            r'(?:ООО\s+)?ВТБ\s+Страхование',
            r'(?:ООО\s+)?(?:СК\s+)?Сбербанк\s+Страхование',
            r'(?:ООО\s+)?(?:СК\s+)?АльфаСтрахование-ОМС',
            r'(?:ООО\s+)?МАКС(?:\s+М)?',
            r'(?:ООО\s+)?(?:СК\s+)?Капитал\s+Лайф\s+Страхование\s+Жизни',
            r'(?:ООО\s+)?(?:СК\s+)?ЭРГО(?:\s+Русь)?',
            r'(?:ООО\s+)?(?:СК\s+)?Гайде',
            r'(?:ООО\s+)?(?:СК\s+)?УралСиб',
            r'(?:АО\s+)?(?:СК\s+)?Энергогарант',
            r'(?:ООО\s+)?(?:СК\s+)?Медэкспресс',
            r'(?:ООО\s+)?(?:СК\s+)?Страховая\s+Группа\s+МСК',
            r'(?:ООО\s+)?(?:СК\s+)?ЖАСО',
            r'(?:ООО\s+)?(?:СК\s+)?Мед\s+Инвест',
            r'(?:ООО\s+)?(?:СК\s+)?АСКО(?:-МЕД)?(?:\s+ДМС)?',
            r'(?:ООО\s+)?(?:СК\s+)?Спасские\s+ворота(?:-М)?',
            r'(?:ООО\s+)?(?:СК\s+)?Либерти\s+Страхование',
            r'(?:ООО\s+)?(?:СК\s+)?МетЛайф',
            r'(?:ООО\s+)?(?:СК\s+)?Группа\s+Ренессанс\s+Страхование',
            r'(?:ООО\s+)?(?:СК\s+)?Открытие\s+Страхование',
            r'(?:ООО\s+)?(?:СК\s+)?Зетта\s+Страхование',
            r'(?:ООО\s+)?(?:СК\s+)?Рента',
            r'(?:ООО\s+)?(?:СК\s+)?СОСЬЕТЕ\s+ЖЕНЕРАЛЬ\s+Страхование',
            r'(?:ООО\s+)?(?:СК\s+)?Согласие',
        ]
        
        for pattern in known_companies:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                res['insurance_company'] = match.group(0).strip()
                break
        
        # Стратегия 2: Поиск организационно-правовых форм + "страх"
        if 'insurance_company' not in res:
            org_forms_pattern = r'(?:ООО|АО|ПАО|ЗАО|НПФ|ОАО)\s+["\']?(?:[А-ЯЁ][а-яё\s\-]*)*(?:страх|медицин|полис)[а-яёА-ЯЁ\s\-]*["\']?'
            match = re.search(org_forms_pattern, full_text, re.IGNORECASE)
            if match:
                candidate = match.group(0).strip().strip('"\'')
                # Проверяем, что это не содержит номера или даты
                if not re.search(r'\d{6,}|\d{2}\.\d{2}\.\d{4}', candidate):
                    res['insurance_company'] = candidate
        
        # Стратегия 3: Поиск по ключевым словам в строках без двоеточия
        if 'insurance_company' not in res:
            for line in lines:
                if ':' in line:
                    continue
                    
                line_clean = line.strip()
                if len(line_clean) < 5:  # Слишком короткая строка
                    continue
                    
                line_lower = line_clean.lower()
                
                # Проверяем наличие страховых маркеров
                insurance_markers = [
                    'страхов', 'страхование', 'insurance', 'медицин', 'дмс', 'полис',
                    'согаз', 'ингос', 'ресо', 'альфа', 'росгос', 'втб', 'сбербанк',
                    'макс', 'капитал', 'эрго', 'гайде', 'уралсиб', 'энергогарант',
                    'медэкспресс', 'мск', 'жасо', 'аско', 'спасские', 'либерти',
                    'метлайф', 'ренессанс', 'открытие', 'зетта', 'рента', 'согласие'
                ]
                
                has_insurance_marker = any(marker in line_lower for marker in insurance_markers)
                
                # Исключаем строки с явными признаками не-названий
                exclusion_patterns = [
                    r'\d{6,}',  # Длинные числа (номера полисов)
                    r'\d{2}\.\d{2}\.\d{4}',  # Даты
                    r'\+?\d[\d\-\(\) ]{8,}',  # Телефоны
                    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email
                    r'(?:номер|серия|дата|период|с\s+\d|до\s+\d)',  # Технические поля
                ]
                
                has_exclusion = any(re.search(pattern, line_clean, re.IGNORECASE) for pattern in exclusion_patterns)
                
                if has_insurance_marker and not has_exclusion:
                    # Очищаем от лишних символов
                    cleaned = re.sub(r'^[^\w]*|[^\w]*$', '', line_clean)
                    if len(cleaned) > 5:
                        res['insurance_company'] = cleaned
                        break
        
        # Стратегия 4: Поиск названий в первых строках (логотип/шапка)
        if 'insurance_company' not in res:
            for i, line in enumerate(lines[:10]):  # Первые 10 строк
                if ':' in line or len(line.strip()) < 5:
                    continue
                    
                line_clean = line.strip()
                line_upper = line_clean.upper()
                
                # Часто названия компаний написаны заглавными в шапке
                if (len([c for c in line_clean if c.isupper()]) / len(line_clean) > 0.7 and 
                    not re.search(r'\d{6,}|\d{2}\.\d{2}\.\d{4}|\+?\d[\d\-\(\) ]{8,}', line_clean)):
                    
                    # Дополнительная проверка на страховые термины
                    if any(term in line_upper for term in ['СТРАХ', 'МЕДИЦИН', 'INSURANCE', 'СОГАЗ', 'ИНГОС', 'РЕСО']):
                        res['insurance_company'] = line_clean
                        break

    # Извлечение остальных полей (номер, дата и т.д.)
    for i, line in enumerate(lines):
        # Поиск номера полиса по шаблону (если не найден выше)
        if 'dms_number' not in res:
            number_match = re.search(r'(?:№|серия\s+DMS\s*№)\s*([0-9]+)', line, re.IGNORECASE)
            if number_match:
                res['dms_number'] = number_match.group(1)
            else:
                alt_match = re.search(r'\b(?:полис|dms)\s+№?\s*([A-Za-zА-Яа-я0-9\-\/]+)', line, re.IGNORECASE)
                if alt_match:
                    res['dms_number'] = alt_match.group(1)

        if 'insurance_date' not in res:
            date_match = re.search(r'дата\s+выдачи:\s*(\d{2}\.\d{2}\.\d{4})', line, re.IGNORECASE)
            if date_match:
                res['insurance_date'] = date_match.group(1)

        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', line)
        if email_match and 'insurance_expiry' not in res:
            res['insurance_expiry'] = email_match.group(0)
            continue

    # Последняя попытка найти номер полиса в полном тексте
    if 'dms_number' not in res:
        full_number_match = re.search(r'\b(\d{10,15})\b', full_text)
        if full_number_match:
            res['dms_number'] = full_number_match.group(1)

    return res

def parse_contract_fields(text: str):
    res = {}
    lines = text.splitlines()
    
    # Ищем в тексте стандартные поля с двоеточием
    for line in lines:
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if "Номер договора" in key:
            res['contract_number'] = val
        elif "Дата договора" in key:
            res['contract_date'] = val
        elif "Должность" in key:
            res['position'] = val
        elif "Место работы" in key:
            res['work_address'] = val
        elif "Телефон" in key or "телефон" in key:
            res['phone'] = val
    
    # Ищем пункт 9 о месте работы, если он не был найден
    if 'work_address' not in res:
        for i, line in enumerate(lines):
            # Пытаемся найти "9." или "9)" или "Пункт 9" и т.п.
            if re.search(r'(?:^|\s)9[\.\)]|пункт\s*9', line.lower()):
                # Если нашли пункт 9, берем его содержимое и несколько следующих строк
                work_address = line.split(":", 1)[1].strip() if ":" in line else ""
                # Если в этой строке нет содержимого, смотрим следующие строки
                if not work_address and i+1 < len(lines):
                    # Собираем адрес из следующих строк, пока не дойдем к новому пункту
                    j = i + 1
                    while j < len(lines) and not re.search(r'(?:^|\s)10[\.\)]|пункт\s*10', lines[j].lower()):
                        work_address += " " + lines[j].strip()
                        j += 1
                res['work_address'] = work_address.strip()
                break
    
    return res