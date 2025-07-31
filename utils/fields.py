def get_field_description(doc_type: str, field_name: str) -> str:
    descriptions = {
        'passport': {
            'fio': "ФИО сотрудника (русскими буквами, ЗАГЛАВНЫМИ)",
            'fio_latin': "ФИО сотрудника (латиницей, ЗАГЛАВНЫМИ)",
            'birthdate': "дату рождения (в формате ДД.ММ.ГГГГ)",
            'birth_place': "место рождения",
            'passport_series': "серию паспорта",
            'passport_number': "номер паспорта",
            'doc_number': "номер документа",
            'issue_date': "дату выдачи паспорта",
            'passport_until': "срок действия паспорта",
            'issuer': "кем выдан паспорт",
            'issuer_country': "страну паспорта",
        },
        'migration': {
            'migration_card_series': "серию миграционной карты",
            'migration_card_number': "номер миграционной карты",
            'migration_card_date': "дату выдачи миграционной карты",
            'migration_card_purpose': "цель визита",
        },
        'patent': {
            'patent_series': "серию патента",
            'patent_number': "номер патента",
            'patent_date': "дату выдачи патента (в формате ДД.ММ.ГГГГ)",
            'patent_issuer': "кем выдан патент",
            'fio': "ФИО владельца (русскими буквами)",
            'patent_blank': "серию и номер бланка патента (например, ПР4744675)",
            'inn': "ИНН сотрудника",
        },
        'dms': {
            'policy_number': "номер полиса ДМС",
            'policy_series': "серию полиса ДМС",
            'start_date': "дату начала действия",
            'end_date': "дату окончания действия",
            'dms_insurer_phone': "контактный телефон страховщика",
            'dms_insurer_email': "адрес электронной почты страховщика",
        },
        'contract': {
            'contract_number': "номер трудового договора",
            'contract_date': "дату заключения трудового договора (в формате ДД.ММ.ГГГГ)",
            'position': "должность сотрудника",
        }
    }
    return descriptions.get(doc_type, {}).get(field_name, f'значение для "{field_name}"')
