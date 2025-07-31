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
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if "ФИО (латиницей" in key:
            res["fio_latin"] = val.upper()
        elif key == "ФИО":
            res["fio"] = val.upper()
        elif "Дата рождения" in key:
            res["birthdate"] = val
        elif "Место рождения" in key:
            if "FERGANA" in val.upper():
                res["birth_place"] = "ФЕРГАНСКАЯ ОБЛАСТЬ"
            else:
                res["birth_place"] = val.upper()
        elif "Пол" in key:
            res["sex"] = "МУЖСКОЙ" if val.upper() == "M" else ("ЖЕНСКИЙ" if val.upper() == "F" else val.upper())
        elif key == "Серия":
            res["passport_series"] = val.upper()
        elif key == "Номер" and "таджикский" not in key:
            res["passport_number"] = val.upper()
        elif "Дата выдачи" in key:
            res["issue_date"] = val
        elif "Срок действия" in key:
            res["expiry_date"] = val
        elif "Кем выдан" in key:
            num = ''.join(filter(str.isdigit, val))
            res["authority"] = f"МВД {num}" if num else "МВД"
        elif "Страна" in key:
            res["nationality"] = "УЗБЕКИСТАН"
        elif "МРЗ" in key:
            res["mrz"] = val.upper()
    return res

def parse_dms_fields(text: str):
    res = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()

    return res

def parse_contract_fields(text: str):
    res = {}
    for line in text.splitlines():
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
    return res
