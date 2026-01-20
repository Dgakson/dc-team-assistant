# Справочники. Константы
DJANGO_API_URL = "http://localhost:8000"
NETBOX_URL = "https://192.168.56.102"
ROLE_MAP = {'Network': 1, 'Server': 2, 'Disk': 3}

INTERFACE_TYPE = {
    '1GE': '1000base-t',	
    'SFP (1GE)': '1000base-x-sfp',	
    'SFP+ (10G)':'10gbase-x-sfpp',	
    'SFP28 (25GE)': '25gbase-x-sfp28',	
    'QSFP28 (100GE)': '100gbase-x-qsfp28'
}