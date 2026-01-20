import streamlit as st
import os
from utils.api import (
    get_assets, 
    get_asset_types, 
    get_site_location
)


st.header("🏢🖥️🔌 DC Peezy - automation made easy!")
st.divider()

# Широкая левая и узкая правая колонка
cols = st.columns([2, 1])  # 2:1 соотношение

with cols[0]:
    st.write("Добро пожаловать на Home! Здесь можно разместить обзор, статистику или приветственное сообщение.")


with cols[1]:
    st.subheader("🛠 Отладка")
    with st.expander("🛠 Отладка (кликните, чтобы открыть)"):
        if st.button("🔄 Обновить устройства", use_container_width=True):
            get_assets.clear()
            st.rerun()
        if st.button("🔄 Обновить типы активов", use_container_width=True):
            get_asset_types.clear()
            st.rerun()
        if st.button("🔄 Обновить локации", use_container_width=True):
            get_site_location.clear()
            st.rerun()        
        if st.button("🗑️ Сбросить ВЕСЬ кэш", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun() 


    # st.page_link("create_device.py", label="Добавить устройство", icon="➕") 
    # st.page_link("create_links.py", label="✏️ Создание кабелей", icon="✏️")

    
    # Внешние ссылки
    st.subheader("Внешние ресурсы 🌐")
    st.markdown("""
    <a href="https://netbox.example.com" target="_blank" style='text-decoration: none;'>
        📦 NetBox Portal
    </a>
    """, unsafe_allow_html=True)


st.divider()

# Вывод последних запусков
log_file = "usage_log.txt"
st.subheader("Последние действия пользователей")
if os.path.exists(log_file):
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()[-10:]  # последние 10 записей
        for line in reversed(lines):
            st.write(line.strip())
else:
    st.write("Лог пока пуст.")