from django.urls import path
from apps.netbox_api.views.assets import (
    AssetsListView,
    AssetsTypeListView,
    AssetDetailView,
    AssetsCreateView,
    AssetsRepairView,
    AssetsModernizationView,
    SitesLocationListView,
)

urlpatterns = [
    ### ASSETS GET
    path('assets/', AssetsListView.as_view(), name='assets_list'),
    path('assets/<int:asset_id>/', AssetDetailView.as_view(), name='assets_detail'),
    path('asset_types/', AssetsTypeListView.as_view(), name='asset_types_list'),
    ### ASSETS POST
    path('assets/create/', AssetsCreateView.as_view(), name='assets_create'),
    path('assets/repair/', AssetsRepairView.as_view(), name='assets_repair'),
    path('assets/modernization/', AssetsModernizationView.as_view(), name='assets_modernization'),

    path('site_location/', SitesLocationListView.as_view(), name='site_location_list'),
]