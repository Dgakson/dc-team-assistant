from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .netbox_client import NetBoxClient




# Inventory    
class AssetsListView(APIView):
    def get(self, request):
        # Извлекаем фильтры из query-параметров
        filters = {}
        type_ids = request.GET.getlist("inventoryitem_type_id")
        if type_ids:
            try:
                filters["inventoryitem_type_id"] = [int(x) for x in type_ids if x.isdigit()]
            except (ValueError, TypeError):
                pass

        if request.GET.get("storage_location_id", "").isdigit():
            filters["storage_location_id"] = int(request.GET["storage_location_id"])

        if request.GET.get("cf_DeliveryTask"):
            filters["cf_DeliveryTask"] = request.GET["cf_DeliveryTask"]
        
        filters["status"] = "stored"

        client = NetBoxClient()
        assets = client.inventory.get_assets(**filters)

        if isinstance(assets, dict) and "error" in assets:
            return Response(assets, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(assets, status=status.HTTP_200_OK)

class AssetsDetailView(APIView):
    def get(self, request, asset_id):
        client = NetBoxClient()
        asset = client.inventory.get_assets_by_id(asset_id)
        if isinstance(asset, dict) and "error" in asset:
            return Response(asset, status=status.HTTP_404_NOT_FOUND)
        return Response(asset, status=status.HTTP_200_OK)    

class AssetTypeListView(APIView):
    def get(self, request):
        client = NetBoxClient()
        assets = client.inventory.get_asset_types()
        if isinstance(assets, dict) and "error" in assets:
            return Response(assets, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(assets, status=status.HTTP_200_OK)

class BaseAssetOperationView(APIView):
    # Метод, который будет переопределяться
    client_method_name = None  # "assets_repair" или "assets_modernization"

    def post(self, request):
        try:
            device_id = request.data.get("device_id")
            asset_ids = request.data.get("asset_ids")
            jira_task = request.data.get("jira_task")

            if not all([device_id, asset_ids, jira_task]):
                return Response({"error": "Не хватает параметров"}, status=status.HTTP_400_BAD_REQUEST)            

            client = NetBoxClient()
            
            client_method = getattr(client.inventory, self.client_method_name)
            result = client_method(asset_ids, device_id, jira_task)

            if isinstance(result, dict) and "error" in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=500) 

class AssetsRepair(BaseAssetOperationView):
    client_method_name = "assets_repair"

class AssetsModernization(BaseAssetOperationView):
    client_method_name = "assets_modernization"

class AssetsCreate(APIView):
    def post(self, request):
        items = request.data.get("items")
        storage_location_id = request.data.get("storage_location_id")
        delivery_task = request.data.get("delivery_task")

        if not all([items, storage_location_id, delivery_task]):
            return Response({"error": "Не хватает параметров"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Преобразуем входные данные в список активов для NetBox
        assets_to_create = []

        for item in items:
            inventoryitem_type_id = item.get("inventoryitem_type_id")
            count = item.get("count")
            serials = item.get("serials", [])

            # Случай 1: указаны серийники
            if serials:
                if len(serials) != count:
                    return Response(
                        {
                            "error": f"Количество серийных номеров ({len(serials)}) "
                                     f"не совпадает с количеством ({count})",
                            "item": item
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                for sn in serials:
                    assets_to_create.append({
                        "inventoryitem_type": inventoryitem_type_id,
                        "serial": sn.strip() or None,
                        "status": "stored",
                        "storage_location": storage_location_id,
                        "custom_fields": {"DeliveryTask": delivery_task}
                    })
            else:
                # Случай 2: без серийников — создаём quantity штук без serial
                for _ in range(count):
                    assets_to_create.append({
                        "inventoryitem_type": inventoryitem_type_id,
                        "status": "stored",
                        "storage_location": storage_location_id,
                        "custom_fields": {"DeliveryTask": delivery_task}
                    })

        # Вызываем NetBox-клиент
        client = NetBoxClient()
        result = client.inventory.assets_create(assets_to_create)

        # Проверяем, не вернулась ли ошибка
        if isinstance(result, dict) and "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "status": "success",
            "created_count": len(result),
            "assets": result 
        }, status=status.HTTP_201_CREATED)


# Эти вьюхи ещё надо проверять и переписывать
class DeviceRoleListView(APIView):
    def get(self, request):
        client = NetBoxClient()
        devices_role = client.dcim.get_device_role()

        if isinstance(devices_role, dict) and "error" in devices_role:
            return Response(devices_role, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
   
class DeviceDeleteView(APIView):
    def delete(self, request):
        client = NetBoxClient()
        result = client.delete_device(request.data.get("asset_tag"))

        if isinstance(result, dict) and "error" in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)

        return Response(result, status=status.HTTP_204_NO_CONTENT)
    


# DCIM GET
class DeviceListView(APIView):
    def get(self, request):
        client = NetBoxClient()
        devices = client.dcim.get_devices()

        if isinstance(devices, dict) and "error" in devices:
            return Response(devices, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(devices, status=status.HTTP_200_OK)

class ManufacturerListView(APIView):
    def get(self, request):
        client = NetBoxClient()
        manufacturers = client.dcim.get_manufacturer()

        if isinstance(manufacturers, dict) and "error" in manufacturers:
            return Response(manufacturers, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(manufacturers, status=status.HTTP_200_OK)
   
class DeviceTypesListView(APIView):
    def get(self, request):
        client = NetBoxClient()
        device_types = client.dcim.get_device_type()

        if isinstance(device_types, dict) and "error" in device_types:
            return Response(device_types, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(device_types, status=status.HTTP_200_OK)

class SitesLocationListView(APIView):
    def get(self, request):
        client = NetBoxClient()
        site_location = client.dcim.get_site_location_map()

        if isinstance(site_location, dict) and "error" in site_location:
            return Response(site_location, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(site_location, status=status.HTTP_200_OK)
    

# DCIM POST 
# Create
class DeviceCreateView(APIView):
    def post(self,request):
        client = NetBoxClient()
        new_devices = client.dcim.create_devices(request.data)

        if isinstance(new_devices, dict) and "error" in new_devices:
            return Response(new_devices, status=status.HTTP_400_BAD_REQUEST)

        return Response(new_devices, status=status.HTTP_201_CREATED)
 
class CableCreateView(APIView):
    def post(self, request):
        client = NetBoxClient()
        new_cables = client.dcim.create_cables(request.data)

        if isinstance(new_cables, dict) and "error" in new_cables:
            return Response(new_cables, status=status.HTTP_400_BAD_REQUEST)

        return Response(new_cables, status=status.HTTP_201_CREATED)
    