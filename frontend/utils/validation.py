## Функции для валидации

# Перепроверить, чтобы нули дорисовывал
def validate_asset(asset_tag):
    """
    Валидация asset tag для Streamlit форм.
    """ 
    if not asset_tag.startswith("OKKOS"):
        raise ValueError("Инвентарный номер должен начинаться с 'OKKOS'")
    if not asset_tag[5:].isdigit():
        raise ValueError("После 'OKKOS' должны быть только цифры")
    if len(asset_tag) != 9:
        raise ValueError(f"❌ Должно быть 9 символов. Получено: {len(asset_tag)}")
    
def validate_serial(serials, count):
    if len(serials) != count:
        # raise ValueError(f"Должно быть {count} серийных номеров, а введено {len(serials)}")
        return f"Должно быть {count} серийных номеров, а введено {len(serials)}"
    for s in serials:
        if len(s) < 3:
            # raise ValueError("Серийный номер слишком короткий")
            return "Серийный номер слишком короткий (минимум 3 символа)"
        
    return None
