import requests
from procesos import utils

REF = 'SERVICEAIRTECH.py'

def get_sql_params(bd_web):
    fn = f'{REF} get_sql_params()'
    if not bd_web:
        utils.logging(ref=fn, tipo='ERROR', msg='no existe el parametro BD_WEB')
        return []
    try:
        utils.logging(ref=fn, tipo='INFO', msg='INICIO get_sql_params()')    
        url = f"http://serviceairtech.com.ar/service1.asmx/getConfiguracionIni?BDCliente={bd_web}"
        f = requests.get(url, timeout=30)

        utils.logging(ref=fn, tipo='INFO', msg=f'SERVICEAIRTECH status_code = {f.status_code}')
        response = f.text.split(';')
        sql_host = response[8].split('=')[1]
        sql_user = response[10].split('=')[1]
        sql_pass = response[11].split('=')[1]
        sql_bd = response[18]

        utils.logging(ref=fn, tipo='INFO', msg='FIN get_sql_params()')
        utils.logging(ref=fn, tipo='INFO', msg='FIN LOG')
        return sql_host, sql_user, sql_pass, sql_bd
    
    except Exception as e:
        utils.logging(ref=fn, tipo='INFO', msg='ERROR obteniendo configuracion H2O')
        return []


