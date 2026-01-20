import streamlit as st
import json
from datetime import date
from utils import (
    get_manufacturers, 
    get_device_types, 
    filter_manufacturers_with_device_types, 
    assets_tag_create, 
    validate_asset, 
    validate_serial, 
    create_devices,
    get_site_location,
    display_created_devices,
    ROLE_MAP,
)




# Инициализация session_state, чтобы не было ошибки 
if "data" not in st.session_state:
    st.session_state.data = []  # ← ВАЖНО: инициализируем здесь!

st.title("Создание новых устройства")

# === Шаг 1: Загрузка данных ===
# КЭШ для запросов к Netbox
with st.spinner("Загрузка производителей и типов устройств..."):
    try:
        device_types = get_device_types()
        manufacturers = get_manufacturers()
        site_location = get_site_location()
    except Exception as e:
        st.error(f"❌ Ошибка загрузки типов устройств: {e}")
        st.stop()

# Константы
STATUS = "inventory"

# === Шаг 2: Форма ввода ===
st.subheader("1. Укажите параметры устройств")

count = st.number_input("Введите количество оборудования:", min_value=1, value=1) # -- Выбор количества --

# --  выбор локации --
selected_site_label = st.selectbox(
    "Выберите сайт приёмки",
    options=sorted(site_location.keys())
)
site_info = site_location[selected_site_label]
site_id = site_info["site_id"]
locations_dict = site_info["locations"]
selected_location_label = st.selectbox(
    "Выберите локацию",
    options=sorted(locations_dict.keys())
)
location_id = locations_dict[selected_location_label]


selected_role = st.selectbox("Роль устройства", options=list(ROLE_MAP.keys()), index=0) # -- Выбор роли --
role_id = ROLE_MAP[selected_role]


# Получаем маппинг: производитель → его типы (только валидные)
mfr_to_types = filter_manufacturers_with_device_types(manufacturers, device_types)

if not mfr_to_types:
    st.error("❌ Нет производителей с доступными типами устройств")
    st.stop()

manufacturer = st.selectbox("Производитель", options=list(mfr_to_types.keys()))
device_types_for_mfr = mfr_to_types[manufacturer]
device_type_options = {dt["model"]: dt["id"] for dt in device_types_for_mfr}

choose_type = st.selectbox("Тип устройства", options=sorted(device_type_options.keys()))
device_type_id = device_type_options[choose_type]


# -- Заполнение инвентарного и серийного номера --
start_asset_tag = st.text_input("Введите стартовый инвентарный номер в формате OKKOSXXXX (Например, OKKOS1234)", placeholder='OKKOS1500')
serials_input = st.text_area(f"Введите {count} серийных номеров (по одному на строку)")
# -- Заполнение кастомных полей --
delivery_task = st.text_input("Введите задачу на доставку:", placeholder='DC-1234') 
commissioning_date = st.date_input("Дата ввода в эксплуатацию", value=date.today())

# === Шаг 3: Кнопка ===
if st.button("🚀 Создать устройства"):
    try:
        # Валидация, проверка обязательных полей 
        if not manufacturer:
            raise ValueError("Нужно выбрать производителя")
        if not device_type_id:
            raise ValueError("Нужно выбрать тип устройства")
        if not delivery_task:
            raise ValueError("Нужно указать задачу на доставку")
        
        validate_asset(start_asset_tag)
        asset_tags = assets_tag_create(start_asset_tag, count)

        serial_list = [s.strip() for s in serials_input.strip().splitlines() if s.strip()]
        validate_serial(serial_list, count)

        # Формируем payload
        payload = [
            {
                "asset_tag": asset_tag,
                "serial": serial,
                "location": location_id,
                "role": role_id,
                "manufacturer": manufacturer,
                "device_type": device_type_id,
                "status": STATUS,
                "site": site_id,
                "custom_fields": {
                    "DeliveryTask": delivery_task,
                    "CommissioningDate": commissioning_date.isoformat()
                }
            }
            for asset_tag, serial in zip(asset_tags, serial_list)
        ]

        # Показываем JSON
        st.session_state["Последние данные"] = payload
        with st.expander("📋 Показать JSON ✅"):
            st.code(json.dumps(payload, indent=4, ensure_ascii=False), language="json")

        # Отправка данных
        with st.spinner("Отправка в NetBox..."):
            response = create_devices(payload)

        if response["ok"]:
            st.session_state.data = response["devices"]
            st.success("✅ Устройства успешно созданы!")
        else:
            st.error(f"❌ Ошибка: {response['error']}")
            st.session_state.data = []

    except ValueError as e:
        st.error(f"⚠️ Ошибка ввода: {e}")
    except Exception as e:
        st.error(f"💥 Непредвиденная ошибка: {e}")

# === Шаг 4: Отображение результата (если есть) ===
if st.session_state.data:
    st.divider()
    st.subheader("✅ 📋 Устройства успешно созданы:")

    display_created_devices(st.session_state.data)