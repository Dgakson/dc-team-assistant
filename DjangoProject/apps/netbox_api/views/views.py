#### Устаревший файл. Позднее, когда будет
#### перенесен весь функционал. 
#### Подлежит удалению




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..netbox_client import NetBoxClient




# Эти вьюхи ещё надо проверять и переписывать
class DeviceRoleListView(APIView):
    def get(self, request):
        client = NetBoxClient()
        devices_role = client.dcim.get_device_role()

        if isinstance(devices_role, dict) and "error" in devices_role:
            return Response(devices_role, status=status.HTTP_400_BAD_REQUEST)

        return Response(devices_role, status=status.HTTP_200_OK)
   
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
    