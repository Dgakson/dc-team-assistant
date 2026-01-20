### Получение данных из netbox 
import requests
import streamlit as st
from .constants import DJANGO_API_URL




# Возможно, переделать, чтобы не грузить все устройства
@st.cache_data(ttl=600)
def get_devices():
    try:
        response = requests.get(f"{DJANGO_API_URL}/devices")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=600)
def get_assets(**kwargs):
    if "status" not in kwargs:
        kwargs["status"] = "stored"
    try:
        response = requests.get(f"{DJANGO_API_URL}/assets/", params=kwargs)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_assets_by_id(asset_id: int):
    try:
        response = requests.get(f"{DJANGO_API_URL}/assets/{asset_id}/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600*24*7)
def get_asset_types():
    try:
        response = requests.get(f"{DJANGO_API_URL}/asset_types")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600*24*7)
def get_manufacturers():
    try:
        response = requests.get(f"{DJANGO_API_URL}/manufacturers")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600*24*7)
def get_device_types():
    try:
        response = requests.get(f"{DJANGO_API_URL}/device_types/")
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600*24*7)
def get_site_location():
    try:
        response = requests.get(f"{DJANGO_API_URL}/site_location")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}   

