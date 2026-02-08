def build_assets_repair_journal(
    *,
    device,
    assets,
    jira_task: str,
    netbox_url: str,
    jira_url: str,
):
    device_link = f"{netbox_url}/dcim/devices/{device.id}/"
    jira_link = jira_url

    lines = []
    for asset in assets:
        asset_url = f"{netbox_url}/plugins/inventory/assets/{asset.id}/"
        delivery_task = asset.custom_fields.get("DeliveryTask")

        lines.append(
            f"- [{asset.inventoryitem_type['model']}]({asset_url}) "
            f"(s/n: {asset.serial}, "
            f"поставка: [{delivery_task}]({jira_link}/{delivery_task}))"
        )

    return (
        f"**🔧 Ремонт из ЗИП**\n\n"
        f"По задаче [{jira_task}]({jira_link}/{jira_task}) "
        f"в устройство [{device.asset_tag}]({device_link}) "
        f"установлены комплектующие:\n\n"
        + "\n".join(lines)
    )

def build_assets_modernization_journal(
    *,
    device,
    assets,
    jira_task: str,
    netbox_url: str,
    jira_url: str,
):
    """Формирует красивую запись для модернизации"""
    device_link = f"{netbox_url}/dcim/devices/{device.id}/"
    jira_link = jira_url

    # группируем активы для компактного отображения
    groups = {}
    type_info = {}

    for asset in assets:
        model = asset.inventoryitem_type.model
        it_id = asset.inventoryitem_type.id
        delivery = asset.custom_fields.get("DeliveryTask") or "Без задачи"
        key = (model, delivery)

        if key not in groups:
            groups[key] = 0
            type_info[model] = it_id
        groups[key] += 1

    lines = []
    for (model, delivery), count in groups.items():
        it_url = f"{netbox_url}/plugins/inventory/inventory-item-types/{type_info[model]}/"
        delivery_url = f"{jira_link}/{delivery}"
        lines.append(
            f"- {count} шт. [{model}]({it_url}) (доставка: [{delivery}]({delivery_url}))"
        )

    return (
        f"**⚙️ Модернизация оборудования**\n\n"
        f"По задаче [{jira_task}]({jira_link}/{jira_task}) в устройство [{device.asset_tag}]({device_link}) "
        f"установлены комплектующие:\n\n"
        + "\n".join(lines)
    )