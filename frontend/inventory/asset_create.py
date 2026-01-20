import streamlit as st
import requests
from utils.ui import add_margin_top, set_primary_button_color
from utils.constants import DJANGO_API_URL
from utils.api import get_asset_types, get_site_location
from utils.validation import validate_serial


# === Применения стиля для кнопок и полей ввода === 
set_primary_button_color()


# ===  Инициализация состояния ===
if "inventory_items" not in st.session_state:
    st.session_state.inventory_items = [{"key": 0}]
    st.session_state.item_counter = 1

# ===  Заголовок ===
st.set_page_config(page_title="📦 Приёмка комплектующих", layout="wide")
st.title("Приёмка новых комплектующих")
st.markdown("***")

# === Загрузка данных ===
with st.spinner("Загрузка данных..."):
    asset_types = get_asset_types()
    site_location_map = get_site_location()

    # Проверка на ошибки
    if "error" in asset_types:
        st.error(f"❌ Ошибка загрузки типов: {asset_types['error']}")
        st.stop()
    if "error" in site_location_map:
        st.error(f"❌ Ошибка загрузки локаций: {site_location_map['error']}")
        st.stop()

    # Проверка на пустоту
    if not asset_types:
        st.error("❌ Список типов комплектующих пуст")
        st.stop()
    if not site_location_map:
        st.error("❌ Список локаций пуст")
        st.stop()

# ===  Общие поля: локация и задача ===
st.subheader("Общие данные")
add_margin_top(12)

cols = st.columns(3)

with cols[0]:
    delivery_task = st.text_input("🎫 Задача на доставку", placeholder="EQUIPMENT-123").strip().upper()

with cols[1]:
    location_id = None
    selected_site = st.selectbox("🏙️ Выберите город", options=[None] + list(site_location_map.keys()))

with cols[2]:
    if selected_site:   
        site_id = site_location_map[selected_site]["site_id"]

        availible_location = site_location_map[selected_site]["locations"]
        selected_location = st.selectbox("🏙️ Выберите локацию", options=list(availible_location.keys()))
        location_id = availible_location[selected_location]

st.markdown("""<hr style="border: 0; border-top: 2px dashed #aaa; margin: 20px 0;">""",unsafe_allow_html=True)

# ===  Отображение строк ввода ===
st.subheader('Комплектующие')
add_margin_top(12)

type_options = sorted(asset_types.keys())
items_to_remove = []

for idx, item in enumerate(st.session_state.inventory_items):
    
    cols = st.columns([2, 1, 3, 0.4, 1])
    with cols[0]:
        selected_type = st.selectbox("Тип",options=type_options,key=f"type_{item['key']}")
    
    with cols[1]:
        count = st.number_input("Кол-во",min_value=1,value=1,key=f"qty_{item['key']}")
    
    with cols[2]:
        label = "Серийные номера (по одному на строку, опционально)"
        serials_input = st.text_area(label=label,key=f"serials_{item['key']}",placeholder="SN001\nSN002\n...")
    
    # кнопка удаления строки
    with cols[4]:
        add_margin_top(28)
        if st.button("🗑️ Удалить", key=f"del_{item['key']}", use_container_width=True):
            items_to_remove.append(idx)

    add_margin_top(24)
    
    # Сохраняем данные
    serial_list = [s.strip() for s in serials_input.splitlines() if s.strip()]
    
    st.session_state.inventory_items[idx].update({
        "type": selected_type,
        "count": count,
        "serials": serial_list
    })

# Удаляем помеченные строки
for idx in sorted(items_to_remove, reverse=True):
    del st.session_state.inventory_items[idx]
    st.rerun()

# ===  Кнопка для добавления ещё типа ===
st.markdown(f'<div style="margin: 24px 0;"></div>', unsafe_allow_html=True)

cols = st.columns([1, 3])
with cols[0]:
    if st.button("➕ Добавить тип комплектующих", key="add_comp_btn", use_container_width=True):
        st.session_state.inventory_items.append({
            "key": st.session_state.item_counter
        })
        st.session_state.item_counter += 1
        st.rerun()

# === Кнопка отправки ===
st.markdown("""<hr style="border: 0; border-top: 2px dashed #aaa; margin: 20px 0;">""",unsafe_allow_html=True)
add_margin_top(10)

if st.button("✔ Подтвердить добавление", type="primary"):
    add_margin_top(10)
    if serials_input:
        error = validate_serial(serial_list, count)
        if error:
            st.error(f"❌ {error}")
            st.stop()

    if not st.session_state.inventory_items:
        st.error("❌ Добавьте хотя бы одну комплектующую")
    elif not delivery_task:
        st.error("❌ Укажите задачу на доставку")
    elif location_id is None:
        st.error("❌ Выберите локацию хранения")
    else:
        try:
            with st.spinner("Добавление в инвентарь..."):
                # Формируем payload
                items = []
                for item in st.session_state.inventory_items:
                    item_data = {
                        "inventoryitem_type_id": asset_types[item["type"]],
                        "count": item["count"]
                    }
                    # Добавляем serials, только если они есть
                    if item["serials"]:
                        item_data["serials"] = item["serials"]
                    items.append(item_data)

                payload = {
                    "items": items,
                    "storage_location_id": location_id,
                    "delivery_task": delivery_task
                }


                response = requests.post(
                    f"{DJANGO_API_URL}/assets/create",
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()
                st.success(f"✅ Успешно добавлено {result.get('created_count', 'несколько')} активов!")

                # Сброс формы
                st.session_state.inventory_items = [{"key": 0}]
                
        except Exception as e:
            st.error(f"❌ Ошибка: {e}")