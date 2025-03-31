# import requests

# REF = 'SERVICEAIRTECH.py'

# def get_sql_params(bd_web):
#     fn = f'{REF} get_sql_params()'
#     if not bd_web:
#         return []
#     try:
#         url = f"http://serviceairtech.com.ar/service1.asmx/getConfiguracionIni?BDCliente={bd_web}"
#         f = requests.get(url, timeout=60)

#         response = f.text.split(';')
#         sql_host = response[8].split('=')[1]
#         sql_user = response[10].split('=')[1]
#         sql_pass = response[11].split('=')[1]
#         sql_bd = response[18]

#         return sql_host, sql_user, sql_pass, sql_bd
    
#     except Exception as e:
#         return []
import requests

REF = 'SERVICEAIRTECH.py'

def get_sql_params(bd_web):
    fn = f'{REF} get_sql_params()'
    if not bd_web:
        return []
    try:
        url = f"http://serviceairtech.com.ar/service1.asmx/getConfiguracionIni?BDCliente={bd_web}"
        response = requests.get(url, timeout=60).text
        
        # Filtrar solo los parámetros de la sección [ENTRADA]
        params = {}
        current_section = None
        for item in response.split(';'):
            if item.strip().startswith('['):  # Detectar secciones (ej: [ENTRADA])
                current_section = item.strip().upper()
            elif current_section == '[ENTRADA]' and '=' in item:
                key, value = item.split('=', 1)
                params[key.strip().upper()] = value.strip()

        # Extraer parámetros necesarios
        sql_host = params.get('DATASOURCE', '')
        sql_user = params.get('USERID', '')
        sql_pass = params.get('PASSWORD', '')
        sql_bd = params.get('INITIALCATALOG', '')  # INITIALCATALOG es el nombre de la BD

        if not all([sql_host, sql_user, sql_pass, sql_bd]):
            return []
        
        return sql_host, sql_user, sql_pass, sql_bd
    
    except Exception as e:
        print(f"Error en {fn}: {str(e)}")
        return []