import streamlit as st
import pandas as pd
import requests
from pathlib import Path

from utils import INTERFACE_TYPE, DJANGO_API_URL, display_created_links


st.title("🔗 Создание кабельных соединений")
left_col, middle_col, right_col = st.columns(3) 

with left_col:
    # 1️⃣ Выбор режима
    mode = st.radio("Выберите способ добавления данных:", ["📂 Загрузить файл", "🧾 Заполнить вручную"])

with middle_col:
# 2️⃣ Шаблон xlsx-файла
    BASE_DIR = Path(__file__).resolve().parent.parent
    template_path = BASE_DIR / "templates" / "cable_template.xlsx"

    if template_path.exists():
        with open(template_path, "rb") as f:
            template_data = f.read()

        st.download_button(
            label="📥 Скачать шаблон XLSX",
            data=template_data,
            file_name="cable_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.error("⚠️ Шаблон не найден! Проверьте путь: templates/cable_template.xlsx")

with right_col:
    pass 

st.divider()
# -------------------------------
# 3️⃣ Режим 1: Загрузка файла
# -------------------------------
if mode == "📂 Загрузить файл":
    uploaded_file = st.file_uploader("Загрузите xlsx-файл со связями", type=["xlsx"])

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.session_state["cables"] = df.to_dict(orient="records")
            st.success("Файл успешно загружен ✅")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Ошибка при чтении файла: {e}")

# -------------------------------
# 4️⃣ Режим 2: Ручное заполнение
# -------------------------------
if mode == "🧾 Заполнить вручную":
    if "manual_data" not in st.session_state:
        st.session_state.manual_data = []

    with st.form("manual_entry"):
        col1, col2, col3, col4, col5 = st.columns(5)
        dev_a = col1.text_input("dev_a")
        port_a = col2.text_input("port_a")
        dev_b = col3.text_input("dev_b")
        port_b = col4.text_input("port_b")
        int_type = col5.selectbox("Тип интерфейса", list(INTERFACE_TYPE.keys()))

        submitted = st.form_submit_button("➕ Добавить строку")
        if submitted:
            if all([dev_a, port_a, dev_b, port_b, int_type]):
                st.session_state.manual_data.append({
                    "dev_a": dev_a.strip(),
                    "port_a": port_a.strip(),
                    "dev_b": dev_b.strip(),
                    "port_b": port_b.strip(),
                    "int_type": INTERFACE_TYPE[int_type].strip()
                })
            else:
                st.warning("Пожалуйста, заполните все поля")

    if st.session_state.manual_data:
        df = pd.DataFrame(st.session_state.manual_data)
        st.dataframe(df)
        st.session_state["cables"] = df.to_dict(orient="records")

        if st.button("🧾 Очистить таблицу"):
            st.session_state.manual_data = []

# -------------------------------
# 5️⃣ Отправка данных в Django
# -------------------------------
if "cables" in st.session_state and st.session_state["cables"]:
    st.divider()
    st.subheader("🚀 Отправка данных в Django API")

    if st.button("📤 Отправить в NetBox"):
        try:
            url = f"{DJANGO_API_URL}/cables/create"
            response = requests.post(url, json=st.session_state["cables"])
            if response.status_code == 201:
                st.success("Кабели успешно созданы ✅")
                # st.write(f"Создано соединение: ")
                # for row in st.session_state["cables"]:
                #     st.write(f"**{row['dev_a']} {row['port_a']} <--> {row['dev_b']} {row['port_b']}**")
                response_data = response.json()
                report = display_created_links(created_cables=response_data.get("created", []))
                st.markdown(report)
            else:
                st.error(f"Ошибка: {response.status_code}")
                st.json(response.json())
        except Exception as e:
            st.error(f"Ошибка при подключении к API: {e}")