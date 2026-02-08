from datetime import date

from apps.netbox_api.services.journal import build_assets_repair_journal, build_assets_modernization_journal
from apps.netbox_api.netbox_client import NetBoxClient
from pynetbox.core.query import RequestError



class AssetsServiceError(Exception):
    pass

class BaseService:
    """Инициализация и общие методы"""

    def __init__(self):
        self.client = NetBoxClient()
        
    def get_site_location_map(self):
        """
        Формирует карту: {site_name: {site_id, locations: {loc_name: loc_id}}}
        """
        site_location_map = {}
        sites = self.client.general.get_sites()
        for site in sites:
            site_location_map[site.name] = {
                "site_id": site.id,
                "locations": {}
            }

        locations = self.client.general.get_locations()
        for loc in locations:
            site_name = loc.site.name
            if site_name in site_location_map:
                site_location_map[site_name]["locations"][loc.name] = loc.id

        return site_location_map


class AssetsService(BaseService):
    """Методы для работы с Assets"""

    def _simplify_asset(self, asset):
        """Преобразует объект NetBox в простой словарь для frontend"""
        it = getattr(asset, "inventoryitem_type", None)
        model_info = {"id": it.id, "model": it.model} if it else {"id": None, "model": "N/A"}

        loc = getattr(asset, "storage_location", None)
        location_info = {"id": loc.id, "name": loc.name} if loc else {"id": None, "name": "N/A"}

        return {
            "id": asset.id,
            "display": getattr(asset, "display", None),
            "serial": getattr(asset, "serial", None),
            "status": getattr(asset, "status", None),
            "model": model_info,
            "storage_location": location_info,
            "custom_fields": getattr(asset, "custom_fields", {}),
        }

    def get_assets(self, **filters):
        """Возвращает список упрощённых активов с применением фильтров"""
        raw_assets = self.client.assets.get_assets(**filters)
        return [self._simplify_asset(a) for a in raw_assets]

    def get_asset_by_id(self, asset_id):
        """Возвращает один актив по id"""
        asset = self.client.assets.get_asset_by_id(asset_id)
        if not asset:
            raise AssetsServiceError(f"Asset with id={asset_id} not found")
        return self._simplify_asset(asset)

    def get_asset_types(self):
        return {at.model: at.id for at in self.client.assets.get_asset_types()}
    
    def create_assets(
        self,
        items: list[dict],
        storage_location_id: int,
        delivery_task: str
    ) -> list[dict]:

        if not items:
            raise AssetsServiceError("items не переданы")

        assets_to_create = []

        for item in items:
            inventoryitem_type_id = item.get("inventoryitem_type_id")
            count = item.get("count")
            serials = item.get("serials", [])

            if not inventoryitem_type_id or not count:
                raise AssetsServiceError(f"Некорректный item: {item}")

            # Случай 1 — с серийниками
            if serials:
                if len(serials) != count:
                    raise AssetsServiceError(
                        f"Количество серийников ({len(serials)}) "
                        f"не совпадает с count ({count})"
                    )

                for sn in serials:
                    assets_to_create.append({
                        "inventoryitem_type": inventoryitem_type_id,
                        "serial": sn.strip() or None,
                        "status": "stored",
                        "storage_location": storage_location_id,
                        "custom_fields": {
                            "DeliveryTask": delivery_task
                        }
                    })

            # Случай 2 — без серийников
            else:
                for _ in range(count):
                    assets_to_create.append({
                        "inventoryitem_type": inventoryitem_type_id,
                        "status": "stored",
                        "storage_location": storage_location_id,
                        "custom_fields": {
                            "DeliveryTask": delivery_task
                        }
                    })

        try:
            created_assets = self.client.assets.create_assets(assets_to_create)
            return [self._simplify_asset(a) for a in created_assets]

        except RequestError as e:
            raise AssetsServiceError(f"Ошибка NetBox: {e}")
        
    def assets_repair(
        self,
        asset_ids: list[int],
        device_id: int,
        jira_task: str,
    ) -> dict:

        device = self.client.devices.get_device(device_id)
        if not device:
            raise AssetsServiceError(f"Устройства device_id-{device_id} не найдено")

        assets = []
        for asset_id in asset_ids:
            asset = self.client.assets.get_asset_by_id(asset_id)
            if not asset:
                raise AssetsServiceError(f"Комплектующая asset_id-{asset_id} не найдена")
            if asset.status == "used":
                raise AssetsServiceError(f"Комплектующая asset_id = {asset_id} уже используется")
            assets.append(asset)

        # ---- формируем journal ----
        journal_comment = build_assets_repair_journal(
            device=device,
            assets=assets,
            jira_task=jira_task,
            netbox_url=self.client.netbox_url,
            jira_url=self.client.jira_url,
        )

        # ---- обновляем assets ----

        for asset in assets:
            self.client.assets.update_asset(
                asset,
                {
                    "custom_fields": {
                        "Install_in": device_id
                    },
                    "storage_site": None,
                    "storage_location": None,
                    "status": "used",
                },
            )

        # ---- обновляем device ----

        modernization_date = date.today().isoformat()

        self.client.devices.update_device(
            device,
            {
                "custom_fields": {
                    "ModernizationDate": modernization_date
                }
            },
        )

        # ---- journal ----

        self.client.general.create_journal_entry(
            {
                "assigned_object_type": "dcim.device",
                "assigned_object_id": device_id,
                "kind": "info",
                "comments": journal_comment,
            }
        )

        # ---- ответ API (упрощённый) ----

        return {
            "status": "success",
            "device": {
                "id": device.id,
                "name": device.name,
                "asset_tag": device.asset_tag,
                "ModernizationDate": modernization_date,
            },
            "installed_assets": [
                {
                    "id": a.id,
                    "model": a.inventoryitem_type["model"],
                    "serial": a.serial,
                }
                for a in assets
            ],
            "total": len(assets),
        }
    
    def assets_modernization(
        self,
        asset_ids: list[int],
        device_id: int,
        jira_task: str,
    ) -> dict:

        device = self.client.devices.get_device(device_id)
        if not device:
            raise AssetsServiceError(f"Устройства device_id = {device_id} не найдено")
    
        assets = []
        for asset_id in asset_ids:
            asset = self.client.assets.get_asset_by_id(asset_id)
            if not asset:
                raise AssetsServiceError(f"Комплектующая asset_id = {asset_id} не найдена")
            if asset.status == "used":
                raise AssetsServiceError(f"Комплектующая asset_id = {asset_id} уже используется")
            assets.append(asset)

        # ---- формируем journal ----
        journal_comment = build_assets_modernization_journal(
            device=device,
            assets=assets,
            jira_task=jira_task,
            netbox_url=self.client.netbox_url,
            jira_url=self.client.jira_url,
        )

        # ---- удаляем активы из NetBox ----
        for asset in assets:
            self.client.assets.delete_asset(asset)

        # ---- обновляем device ----
        modernization_date = date.today().isoformat()
        self.client.devices.update_device(
            device,
            {"custom_fields": {"ModernizationDate": modernization_date}},
        )

        # ---- создаём journal entry ----
        self.client.general.create_journal_entry(
            {
                "assigned_object_type": "dcim.device",
                "assigned_object_id": device_id,
                "kind": "info",
                "comments": journal_comment,
            }
        )

        # ---- упрощённый ответ ----
        return {
            "status": "success",
            "device": {
                "id": device.id,
                "name": device.name,
                "asset_tag": device.asset_tag,
                "ModernizationDate": modernization_date,
            },
            "removed_assets": [
                {
                    "id": a.id,
                    "model": a.inventoryitem_type["model"],
                    "serial": a.serial,
                }
                for a in assets
            ],
            "total": len(assets),
        }