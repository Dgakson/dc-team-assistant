import streamlit as st
from utils.api import (
    get_assets, 
    get_asset_types, 
    get_site_location
)



def main():    
    # Настройка страницы
    st.set_page_config(
        page_title="DC Peezy",
        page_icon="🔌",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Создаем навигацию
    with st.sidebar:
        with st.expander("🛠 Отладка"):
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

        selected = st.navigation(
            {
                "🏠 Главная": [
                    st.Page('home.py', title="Дом", icon="🏠"),
                ],
                "🗄️ DCIM": [
                    # st.Page('device/create_devices.py', title="Добавить устройство", icon="📦"),
                    # st.Page("device/create_links.py", title="Добавить кроссировки", icon="🔗")
                ],
                "🛠️ Inventory": [
                    st.Page("inventory/asset_create.py", title="Приём на склад", icon="📦"),
                    st.Page("inventory/repair.py", title="Ремонт (из ЗИП)", icon="🔧"),
                    st.Page("inventory/modernization.py", title="Модернизация", icon="⚙️")
                ]
            }
        )
    # Показываем выбранную страницу
    selected.run()

if __name__ == "__main__":
    main()