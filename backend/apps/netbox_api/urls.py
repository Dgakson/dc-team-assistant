from django.urls import path
from .views import (
    DeviceListView, 
    DeviceCreateView, 
    DeviceDeleteView, 
    ManufacturerListView, 
    DeviceTypesListView, 
    CableCreateView, 
    AssetsListView,
    AssetsRepair,
    AssetsModernization,
    SitesLocationListView,
    DeviceRoleListView,
    AssetTypeListView,
    AssetsDetailView,
    AssetsCreate,
    # InterfaceListView
)

urlpatterns = [
    path('devices/', DeviceListView.as_view(), name='devices_list'),
    path('device_types/', DeviceTypesListView.as_view(), name='device_types_list'),
    path('device_role/', DeviceRoleListView.as_view(), name='device_role_list'),
    path('manufacturers/', ManufacturerListView.as_view(), name='manufacturers_list'),
    path('site_location/', SitesLocationListView.as_view(), name='site_location_list'),

    path('assets/', AssetsListView.as_view(), name='assets_list'),
    path('assets/<int:asset_id>/', AssetsDetailView.as_view(), name='assets_detail'),
    path('asset_types/', AssetTypeListView.as_view(), name='asset_types_list'),
    path('assets/create', AssetsCreate.as_view(), name='assets_create'),
    path('assets/repair', AssetsRepair.as_view(), name='assets_repair'),
    path('assets/modernization', AssetsModernization.as_view(), name='assets_modernization'),

    # path('interface/', InterfaceListView.as_view(), name='interface_list'),

    

# Эти надо ещё проверять
    path('devices/create', DeviceCreateView.as_view(), name='device_create'),
    path('devices/delete', DeviceDeleteView.as_view(), name='devices_delete'),
    path('cables/create', CableCreateView.as_view(), name='create_cables'),
]