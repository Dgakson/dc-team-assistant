#### Устаревший файл. Позднее, когда будет
#### перенесен весь функционал. 
#### Подлежит удалению



import pynetbox
import requests
import urllib3
import warnings
from datetime import date
from urllib3.exceptions import InsecureRequestWarning
from django.conf import settings
from pynetbox.core.query import RequestError


class NetBoxClient:
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

        # Добавляем подмодуль для inventory и DCIM
        self.inventory = self.Inventory(api=self.api, jira_url=self.jira_url, netbox_url=self.netbox_url)
        self.dcim = self.Dcim(api=self.api, netbox_url=self.netbox_url)


    class Dcim:
        """
        Подмодуль NetBoxClient для работы с плагином Inventory.
        Вызов: client.inventory.METHOD(...)
        """
        def __init__(self, api, netbox_url):
            self.api = api  
            self.netbox_url = netbox_url

        def _simplify_device(self, device):
            """Преобразует объект устройства в единый формат."""
            return {
                "url": f"{self.netbox_url}/dcim/devices/{device.id}",
                "id": device.id,
                "name": device.name,
                "asset_tag": device.asset_tag,
                "serial": device.serial,
                "custom_fields": getattr(device, 'custom_fields', {})
            }
        
        # методы для получения данных        
        def get_device_role(self):
            """
            Получить роли устройств
            Результат выполнения json {"id":id, "name":name}
            """

            try:
                return [{'id': dr.id, 'name': dr.name} for dr in self.api.dcim.device_roles.all()]
            except Exception as e:
                return {"error": str(e)}
        
        def get_device_type(self):
            """
            Получить типы устройств
            Результат выполнения json {"id":id, "model":name, "manufacturer":manufacturer.name}
            """

            try:
                return [{'id': dt.id, 'model': dt.model, 'manufacturer': dt.manufacturer.name} for dt in self.api.dcim.device_types.all()]
            except Exception as e:
                return {"error": str(e)}

        def get_manufacturer(self):
            """
            Получить список всех производителей из NetBox
            Результат выполнения name производителя
            """
            try:
                return [m.name for m in self.api.dcim.manufacturers.all()]
            except Exception as e:
                return {"error": str(e)}

        def get_devices(self):
            """
            Получаем список устройств из NetBox
            """
            try:
                devices = self.api.dcim.devices.all()
                return [self._simplify_device(d) for d in devices]
            except Exception as e:
                return {"error": str(e)}

        def get_device_by_name(self, name):
            """Получить устройство по имени"""
            try:
                device = self.api.dcim.devices.get(name=name)
                return device
            except Exception:
                return None

        def get_interface(self, device_name, interface_name):
            """Получить интерфейс устройства"""
            try:
                device = self.get_device_by_name(device_name)
                if not device:
                    raise ValueError(f"Устройство не найдено: {device_name}")
                
                interface = self.api.dcim.interfaces.get(device_id=device.id, name=interface_name)
                if not interface:
                    raise ValueError(f"Интерфейс не найден: {device_name}:{interface_name}")
                
                return interface
            except Exception as e:
                raise ValueError(f"Ошибка поиска интерфейса {device_name}:{interface_name} — {e}")
            
        def get_site_location_map(self):
            """
            Собирает карту: {site_name: {site_id, locations: {loc_name: loc_id}}}
            Учитывает, что локации принадлежат конкретному сайту.
            """
            try:
                site_location_map = {}
                # 1. Получаем все сайты
                sites = list(self.api.dcim.sites.filter(tag='dc'))
                for site in sites:
                    
                    site_location_map[site.name] = {
                        "site_id": site.id,
                        "locations": {}
                    }

                # 2. Получаем все локации и распределяем их по сайтам
                locations = self.api.dcim.locations.all()
                for loc in locations:
                    site_name = loc.site.name
                    if site_name in site_location_map:
                        site_location_map[site_name]["locations"][loc.name] = loc.id
                return site_location_map

            except Exception as e:
                return {"error": str(e)}

        # методы для создания данных 
        def create_devices(self, devices_data: list[dict]):
            """
            Cоздание устройств в NetBox (одного и более)
            Ожидает список словарей
            [
                {
                    "role": role.id, 
                    "manufacturer": name, 
                    "device_type": dt.id, 
                    "status": "inventory", 
                    "site": site.id, 
                    "location": location.id, 
                    "asset_tag": str, 
                    "serial": str, 
                    "cf_DeliveryTask": str, 
                    "cf_CommissioningDate": date
                }
            ]
            """
            try:
                created_devices = self.api.dcim.devices.create(devices_data)
                return [self._simplify_device(d) for d in created_devices]
            
            except RequestError as e:
                return {"error": f"Ошибка при массовом создании устройств: {e}"}
            except Exception as e:
                return {"error": f"Неожиданная ошибка: {e}"}

        def create_cables(self, cables_data: list[dict]):
            """
            Создание кабелей между интерфейсами.
            Ожидает список словарей формата:
            [
                {"dev_a": "SW1", "port_a": "Eth0/1", "dev_b": "SW2", "port_b": "Eth0/2", "int_type": "1000base-t"},
            ]
            """
            created, errors = [], []

            for cable in cables_data:
                dev_a = cable.get("dev_a")
                port_a = cable.get("port_a")
                dev_b = cable.get("dev_b")
                port_b = cable.get("port_b")
                int_type = cable.get("int_type")

                try:
                    # Находим интерфейсы в NetBox
                    interface_a = self.get_interface(dev_a, port_a)
                    interface_b = self.get_interface(dev_b, port_b)

                    if not interface_a or not interface_b:
                        raise ValueError(f"Не найден интерфейс: {dev_a}:{port_a} или {dev_b}:{port_b}")

                    # Формируем payload
                    payload = {
                        "a_terminations": [
                            {"object_type": "dcim.interface", "object_id": interface_a.id}
                        ],
                        "b_terminations": [
                            {"object_type": "dcim.interface", "object_id": interface_b.id}
                        ],
                    }

                    # Отправляем запрос в NetBox на изменение интерфейса
                    interface_a.update({"type": int_type}) 
                    interface_b.update({"type": int_type}) 
                    
                    # Отправляем запрос в NetBox на создание кабеля
                    cable = self.api.dcim.cables.create(payload)

                    created.append({
                        "id": cable.id,
                        "device_a": dev_a,
                        "port_a": port_a,
                        "device_b": dev_b,
                        "port_b": port_b,
                        "int_type": int_type
                    })

                except RequestError as e:
                    errors.append({"cable": cable, "error": f"NetBox API error: {e}"})
                except Exception as e:
                    errors.append({"cable": cable, "error": str(e)})

            # Возвращаем результат
            if errors and not created:
                return {"error": "Не удалось создать ни один кабель", "details": errors}
            return {"created": created, "errors": errors}



    # Методы для удаления 
    def delete_device(self, asset_tag):
        """
        Удалить устройство по asset_tag.
        Возвращает True при успехе, False при ошибке.
        """
        try:
            device = self.api.dcim.devices.filter(asset_tag=asset_tag)
            if not device:
                return {"error": f"Устройство с asset_tag {asset_tag} не найдено"}

            result = device.delete()
            if result:  # возвращает True при успешном удалении
                return {"status": "ok", "message": f"Устройство {asset_tag} удалено"}
            else:
                return {"error": f"Не удалось удалить устройство {asset_tag}"}

        except RequestError as e:
            return {"error": f"Ошибка при удалении устройства: {e}"}
        except Exception as e:
            return {"error": f"Неожиданная ошибка: {e}"}
