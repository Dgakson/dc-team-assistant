from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.netbox_api.services.assets import (
    AssetsService, 
    BaseService,
    AssetsServiceError,
)


class AssetsTypeListView(APIView):
    def get(self, request):
        service = AssetsService()
        types = service.get_asset_types()
        return Response(types)


class AssetsListView(APIView):
    def get(self, request):
        service = AssetsService()
        filters = {k: v for k, v in request.query_params.items() if v}
        # filters = request.query_params.dict()  # пример: ?status=active
        assets = service.get_assets(**filters)
        return Response(assets)


class AssetDetailView(APIView):
    def get(self, request, asset_id):
        service = AssetsService()
        try:
            asset = service.get_asset_by_id(asset_id)
            return Response(asset)    
        except AssetsServiceError as e:
            return Response({"detail": str(e)}, status=404)
        

class AssetsCreateView(APIView):
    def post(self, request):
        items = request.data.get("items")
        storage_location_id = request.data.get("storage_location_id")
        delivery_task = request.data.get("delivery_task")

        if not all([items, storage_location_id, delivery_task]):
            return Response(
                {"error": "Не хватает параметров"},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = AssetsService()

        try:
            assets = service.create_assets(
                items=items,
                storage_location_id=int(storage_location_id),
                delivery_task=delivery_task
            )

            return Response(
                {
                    "status": "success",
                    "created_count": len(assets),
                    "assets": assets
                },
                status=status.HTTP_201_CREATED
            )
        except AssetsServiceError as e:
            return Response({"detail": str(e)}, status=404)
        

class BaseAssetOperationView(APIView):
    """
    Базовый класс для операций с активами.
    Наследники должны определить:
        - client_method_name: имя метода сервиса AssetsService
    """

    client_method_name: str = None  # "assets_repair" или "assets_modernization"

    def post(self, request):
        if not self.client_method_name:
            return Response(
                {"detail": "client_method_name не задан"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        device_id = request.data.get("device_id")
        asset_ids = request.data.get("asset_ids")
        jira_task = request.data.get("jira_task")

        if not all([device_id, asset_ids, jira_task]):
            return Response(
                {"error": "Не хватает параметров: device_id, asset_ids, jira_task"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = AssetsService()
        client_method = getattr(service, self.client_method_name)

        try:
            result = client_method(
                asset_ids=asset_ids,
                device_id=device_id,
                jira_task=jira_task,
            )
            return Response(result, status=status.HTTP_200_OK)

        except AssetsServiceError as e:
            return Response({"detail": str(e)}, status=404)


class AssetsRepairView(BaseAssetOperationView):
    client_method_name = "assets_repair"


class AssetsModernizationView(BaseAssetOperationView):
    client_method_name = "assets_modernization"


class SitesLocationListView(APIView):
    def get(self, request):
        service = BaseService()
        site_location = service.get_site_location_map()
        return Response(site_location)