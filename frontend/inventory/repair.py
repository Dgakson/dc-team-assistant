import streamlit as st
import requests
from utils.constants import DJANGO_API_URL
from utils.logic import apply_asset_filters
from utils.ui import (
    show_devices, 
    show_assets, 
    show_asset_repair_dialog, 
    set_primary_button_color,
    add_margin_top
)
from utils.api import (
    get_devices, 
    get_assets_by_id,
    get_site_location,
    get_asset_types
)




# ===  Заголовок ===
st.set_page_config(page_title="🔧 Ремонт оборудования", layout="wide")
st.title("Ремонт оборудования")
st.markdown("***")

# === Загрузка данных ===
with st.spinner("Загрузка устройств..."):
    devices = get_devices()
    asset_types = get_asset_types()

    # Проверка на ошибки
    if "error" in asset_types:
        st.error(f"❌ Ошибка загрузки устройств: {devices['error']}")
        st.stop()
    if "error" in asset_types:
        st.error(f"❌ Ошибка загрузки типов комплектующих: {asset_types['error']}")
        st.stop()

    # Проверка на пустоту
    if not devices:
        st.error("❌ Список устройств пуст")
        st.stop()
    if not asset_types:
        st.error("❌ Список типов комплектующих пуст")
        st.stop()


# ===  Выбор устройства и задачи ===
st.subheader("Выбор устройства и задачи")

cols = st.columns([2,1,1,1])

with cols[0]:
    device_id = show_devices(devices)

with cols[1]:
    jira_task = st.text_input("Номер задачи Jira на работы", placeholder="DC-2345")

add_margin_top(12)

# === Выбор комплектующих ===
st.subheader("Фильтрация")

# Фильтрация
cols = st.columns([2,1,1,1])

with cols[0]:
    selected_type_names = st.multiselect(
        "🔍 Тип комплектующей",
        options=sorted(asset_types.keys())
    )

with cols[1]:
    delivery_task_input = st.text_input("🎫 Номер задачи Jira на доставку", 
                              placeholder="DC-123"
    )
    delivery_task = delivery_task_input.strip().upper()

with cols[2]:
    site_location_map = get_site_location()  
    location_id = None
    selected_site = st.selectbox("🏙️ Выберите город", options=[None] + list(site_location_map.keys()))

with cols[3]:
    if selected_site:   
        site_id = site_location_map[selected_site]["site_id"]

        availible_location = site_location_map[selected_site]["locations"]
        selected_location = st.selectbox("🏙️ Выберите локацию", options=list(availible_location.keys()))
        location_id = availible_location[selected_location]

add_margin_top(10)

### Вывод активов в зависимости от фильтров

# --- Кнопка поиска ---
cols = st.columns([2,1,1,1])
with cols[0]:
    if st.button("🔍 Найти комплектующие",  use_container_width=True):
        # Формируем параметры фильтрации
        filters = {}
        if selected_type_names:
            filters["inventoryitem_type_id"] = [asset_types[name] for name in selected_type_names]
        if delivery_task:
            filters["cf_DeliveryTask"] = delivery_task
        if location_id != None:
            filters["storage_location_id"] = location_id

        apply_asset_filters(filters)


# === Отображение результатов ===
# Формат отображения: "display (serial, delivery_task)"
if "filtered_assets" in st.session_state:
    add_margin_top(12)
    st.subheader("Выбор комплектующих")

    assets = st.session_state.filtered_assets
    st.session_state.asset_ids_for_submit = show_assets(assets)

## Кнопка
asset_ids = st.session_state.get("asset_ids_for_submit", [])

st.markdown("""<hr style="border: 0; border-top: 2px dashed #aaa; margin: 20px 0;">""",unsafe_allow_html=True)
add_margin_top(10)
set_primary_button_color()

if st.button("✔ Подтвердить ремонт", type="primary"):
    if not asset_ids:
        st.error("❌ Выберите хотя бы одну комплектующую")
    elif not jira_task.strip():
        st.error("❌ Укажите номер задачи Jira")
    elif not device_id:
        st.error("❌ Выберите устройство")
    else:
        try:
            # === 🔍 Проверка актуального статуса активов ===
            for aid in asset_ids:
                if get_assets_by_id(asset_id=aid).get("status") != "stored":
                    st.error("❌ Комплектующая уже установлена (имеет статус used)")
                    st.stop()

            with st.spinner("Отправка в NetBox..."):
                # Формируем данные
                payload = {
                    "device_id": device_id,
                    "asset_ids": asset_ids,
                    "jira_task": jira_task.strip()
                }

                # Отправляем POST-запрос
                response = requests.post(
                    f"{DJANGO_API_URL}/assets/repair", 
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()  # вызовет исключение при 4xx/5xx
                response_data = response.json()
                
                show_asset_repair_dialog(response_data)

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Ошибка сети или сервера: {e}")
        except Exception as e:
            st.error(f"❌ Непредвиденная ошибка: {e}")    