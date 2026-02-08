import pynetbox
import requests
import urllib3
import warnings
from urllib3.exceptions import InsecureRequestWarning
from django.conf import settings


class NetBoxClient:
    """
    Отвечает за инициализацию api + общие настройки сессии.
    Дальше раздаёт доступ к под-клиентам: general / assets / devices.
    """
    def __init__(self):
        # убираем ssl warning, если используется самоподписанный сертификат
        urllib3.disable_warnings(InsecureRequestWarning)
        warnings.filterwarnings("ignore", category=InsecureRequestWarning)

        # создаём сессию
        session = requests.Session()
        session.verify = False  # ⚠️ лучше использовать нормальный SSL
        
        # создаём клиент NetBox
        self.api = pynetbox.api(
            settings.NETBOX_URL,
            token=settings.NETBOX_TOKEN
        )
        self.api.http_session = session

        self.jira_url = settings.JIRA_URL
        self.netbox_url = settings.NETBOX_URL

        
    
    ### SITES GET
    def get_sites(self):
        return self.api.dcim.sites.filter(tag="dc")

    def get_locations(self):
        return self.api.dcim.locations.all()

    ### ASSET GET
    def get_assets(self, **filters):
        return self.api.plugins.inventory.assets.filter(**filters)
        
    def get_asset_by_id(self, asset_id):
        return self.api.plugins.inventory.assets.get(id=asset_id)
    
    def get_asset_types(self):
        return self.api.plugins.inventory.inventory_item_types.all()

    ### ASSET POST
    def delete_asset(self, asset):
         asset.delete()

    def create_assets(self, assets_data: list[dict]):
        """Массовое создание assets в NetBox"""
        return self.api.plugins.inventory.assets.create(assets_data)

    def update_asset(self, asset, data: dict):
        asset.update(data)
    
    ### JOURNAL POST
    def create_journal_entry(self, data: dict):
        return self.api.extras.journal_entries.create(data)
    
    ### DEVICE GET
    def get_device(self, device_id: int):
        return self.api.dcim.devices.get(id=device_id)
    
    ### DEVICE POST
    def update_device(self, device, data: dict):
        device.update(data)


    
