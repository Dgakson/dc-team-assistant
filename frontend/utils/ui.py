import requests
import streamlit as st
from .constants import NETBOX_URL


def add_margin_top(height_px: int = 24) -> None:
    """
    Добавляет вертикальный отступ (margin) на странице Streamlit.
    
    Параметры:
        height_px (int): Высота отступа в пикселях. По умолчанию — 24px.
    """
    st.markdown(f'<div style="margin: {height_px}px 0;"></div>', unsafe_allow_html=True) 

def set_primary_button_color(
    start_color: str = "#5a4fcf", 
    end_color: str = "#6a5acd",
    hover_darken_factor: float = 0.75

):
    """
    Применяет вертикальный градиент к кнопкам с type='primary'.
    
    Параметры:
        start_color — цвет сверху
        end_color   — цвет снизу
        hover_darken_factor (float): коэффициент затемнения при hover (0.7–0.8 рекомендуется)

    """
    # Вспомогательная локальная функция для затемнения
    def _adjust_brightness(hex_col: str, factor: float) -> str:
        if not hex_col.startswith("#") or len(hex_col) != 7:
            return hex_col
        r = min(255, max(0, int(int(hex_col[1:3], 16) * factor)))
        g = min(255, max(0, int(int(hex_col[3:5], 16) * factor)))
        b = min(255, max(0, int(int(hex_col[5:7], 16) * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    hover_start = _adjust_brightness(start_color, hover_darken_factor)
    hover_end = _adjust_brightness(end_color, hover_darken_factor)

    st.html(f"""
    <style>
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(to bottom, {start_color}, {end_color}) !important;
        border: none !important;
        color: white !important;
        font-weight: bold;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: all 0.2s ease;
        border-radius: 6px;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background: linear-gradient(to bottom, {hover_start}, {hover_end}) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }}
    div.stButton > button[kind="primary"]:active {{
        transform: translateY(1px);
    }}
    </style>
    """)



## функция для вывода результата
def display_created_devices(devices: list[dict]):
    """Отображение успешно созданных устройств в виде Markdown-таблицы."""
    markdown_table = (
        "| Инвентарный номер | Серийный номер | Задача на доставку |\n"
        "|-------------------|----------------|--------------------|\n"
    )
    for dev in devices:
        url = dev.get("url", "#")
        asset_tag = dev.get("asset_tag", "—")
        serial = dev.get("serial", "—")
        delivery = dev.get("custom_fields", {}).get("DeliveryTask", "—")
        markdown_table += f"| [{asset_tag}]({url}) | {serial} | {delivery} |\n"
    st.markdown(markdown_table)

def display_created_links(created_cables: list[dict]):
    """Формирует Markdown-список созданных кабелей."""
    if not created_cables:
        return "🔌 Не создано ни одного кабеля."
    
    lines = ["**Созданы следующие линки:**"]
    for cable in created_cables:
        line = (
            f"- Между **{cable['device_a']}** (`{cable['port_a']}`) и **{cable['device_b']}** (`{cable['port_b']}`) --- \t"
            f"[Кабель ID {cable['id']}]({NETBOX_URL}/dcim/cables/{cable['id']})"
        )
        lines.append(line)
    return "\n".join(lines)

def show_asset_repair_dialog(response: list[dict]):
    """Формирует Markdown-список созданных кабелей."""
    @st.dialog("📦 Установка комплектующих", width="large")
    def _dialog():
        if response.get("status") != "success":
            st.error("❌ Операция завершилась с ошибкой.")
            st.divider()
            if st.button("Закрыть", type="primary", use_container_width=True):
                st.rerun()
            return

        device_name = response.get("device_name", "—")
        device_asset_tag = response.get("device_asset_tag","-")
        modernization_date = response.get("ModernizationDate", "")

        device_link = f"{NETBOX_URL}/dcim/devices/?asset_tag={device_asset_tag}"
        journal_link = f"{NETBOX_URL}/extras/journal-entries/?q={device_asset_tag}"

        # Основной блок
        lines = []

        # Устройство — как кликабельная ссылка
        lines.append(f"📦 Комплектующие установлены в устройство:  **[{device_name} ({device_asset_tag})]({device_link})**")
        lines.append("")
        lines.append(f"- **📅 Дата:** {modernization_date}")

        installed = response.get("installed_assets", [])
        if installed:

            for item in installed:
                asset_id, model = item[0], item[1]
                asset_link = f"{NETBOX_URL}/plugins/inventory/assets/{asset_id}/"
                lines.append(f"- [{model}]({asset_link})")

        lines.append(f"\n**[Журнал операций]({journal_link})**")
        # Отображаем
        st.markdown("\n".join(lines))
        
        st.divider()
        if st.button("Закрыть", type="primary", use_container_width=True):
            st.rerun()

    _dialog()

def show_asset_modernization_dialog(response: list[dict]):
    """
    Показывает результат модернизации в модальном окне.
    Автоматически формирует красивый отчёт с кликабельными ссылками.
    """
    
    @st.dialog("✅ Модернизация завершена", width="large")
    def _dialog():
        if response.get("status") != "success":
            st.error("❌ Операция завершилась с ошибкой.")
            st.divider()
            if st.button("Закрыть", type="primary", use_container_width=True):
                st.rerun()
            return

        device_name = response.get("device_name", "—")
        device_asset_tag = response.get("device_asset_tag", "-")
        total = response.get("total", 0)
        modernization_date = response.get("ModernizationDate", "")
        
        device_link = f"{NETBOX_URL}/dcim/devices/?asset_tag={device_asset_tag}"
        journal_link = f"{NETBOX_URL}/extras/journal-entries/?q={device_asset_tag}"

        # Основной блок
        lines = []

        # Устройство — как кликабельная ссылка
        lines.append(f"Комплектующие установлены в устройство:  **[{device_name} ({device_asset_tag})]({device_link})**")
        lines.append("")
        lines.append(f"- **Дата:** {modernization_date}")

        # Подсчёт количества по каждому уникальному типу
        installed = response.get("installed_assets", [])
        if installed:
            # Считаем: model_name → count
            model_count = {}
            model_id_map = {}  # чтобы запомнить ID для ссылки

            for item in installed:
                model_id, model_name = item[0], item[1]
                if model_name not in model_count:
                    model_count[model_name] = 0
                    model_id_map[model_name] = model_id
                model_count[model_name] += 1

            # Добавляем строки: "Ссылка на тип — N шт"
            for model_name, count in model_count.items():
                model_id = model_id_map[model_name]
                model_link = f"{NETBOX_URL}/plugins/inventory/inventory-item-types/{model_id}/"
                lines.append(f"- **[{model_name}]({model_link})** - установлено {count} шт")

        # Журнал — в конце
        lines.append(f"- **[Журнал операций]({journal_link})**")

        # Отображаем
        st.markdown("\n".join(lines))
        
        st.divider()
        if st.button("Закрыть", type="primary", use_container_width=True):
            st.rerun()

    _dialog()

def show_devices(devices: list[dict]):
    device_options = {}
    for d in devices:
        device_name = d["name"]
        device_id = d["id"]
        asset_tag = d["asset_tag"] or f"Без инв.номера"
        display_label = f"{device_name} ({asset_tag})"
        device_options[display_label] = device_id

    selected_tag = st.selectbox("Введите инв.номер",options=sorted(device_options.keys()))
    device_id = device_options[selected_tag]

    return device_id

def show_assets(assets):
    asset_ids = []
    if assets:
        asset_options = {}
        for a in assets:
            display = a.get("display", f"Asset #{a['id']}")
            serial = a.get("serial", "N/A")
            delivery_task = a.get("custom_fields").get("DeliveryTask", "N/A")
            label = f"{display} (s/n: {serial},  delivery task: {delivery_task})"
            asset_options[label] = a["id"]

        # Сортировка по id (от старого к новому)
        sorted_labels = [
            label for label, id_val in sorted(asset_options.items(), key=lambda x: x[1])
        ]
        selected_labels = st.multiselect("Комплектующие", options=sorted_labels)
        asset_ids = [asset_options[label] for label in selected_labels]
    else:
        st.warning("Нет свободных активов")

    return asset_ids

