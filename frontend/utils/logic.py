import requests
import streamlit as st
from .constants import DJANGO_API_URL
from .api import get_assets



## Функции для фильтрации
def filter_manufacturers_with_device_types(manufacturers: list[str], device_types: list[dict]):
    # Группируем device types по имени производителя
    mfr_to_types = {}
    for dt in device_types:
        mfr_name = dt["manufacturer"]
        mfr_to_types.setdefault(mfr_name, []).append(dt)
    # Сортируем для предсказуемого порядка
    return dict(sorted(mfr_to_types.items()))

def apply_asset_filters(filters: dict):
    """
    Универсальная функция для поиска комплектующих.
    
    Args:
        filters (dict): Словарь фильтров, например:
            {
                "cf_DeliveryTask": "EQUIPMENT-123",
                "inventoryitem_type_id": [123, 456],
                "storage_location_id": 789
            }
    """
    # Сохраняем фильтры в сессию
    st.session_state.asset_filters = filters

    try:
        with st.spinner("Поиск комплектующих..."):
            filtered_assets = get_assets(**filters)
            st.session_state.filtered_assets = filtered_assets
    except Exception as e:
        st.error(f"❌ Ошибка поиска: {e}")
        st.session_state.filtered_assets = []

## Функции для создания
def assets_tag_create(start_asset_tag, count):
    if start_asset_tag:
        str_part = start_asset_tag[:5]
        int_part = int(start_asset_tag[5:])

        asset_tags = []
        for i in range(count):
            # Начинаем с текущего номера, потом увеличиваем
            asset_tag = str_part + str(int_part + i)
            asset_tags.append(asset_tag)
        return asset_tags

def create_devices(payload: list[dict]):
    """Отправка payload в Django API для создания устройств."""
    url = f"{DJANGO_API_URL}/devices/create"
    try:
        response = requests.post(url, json=payload, timeout=300)
        if response.ok:
            data = response.json()
            return {"ok": True, "devices": data if isinstance(data, list) else [data]}
        else:
            try:
                error = response.json()
            except ValueError:
                error = response.text
            return {"ok": False, "error": error}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": str(e)}