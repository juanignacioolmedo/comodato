import requests

REF = 'SERVICEAIRTECH.py'

def get_sql_params(bd_web):
    fn = f'{REF} get_sql_params()'
    if not bd_web:
        return []
    try:
        url = f"http://serviceairtech.com.ar/service1.asmx/getConfiguracionIni?BDCliente={bd_web}"
        f = requests.get(url, timeout=60)

        response = f.text.split(';')
        sql_host = response[8].split('=')[1]
        sql_user = response[10].split('=')[1]
        sql_pass = response[11].split('=')[1]
        sql_bd = response[18]

        return sql_host, sql_user, sql_pass, sql_bd
    
    except Exception as e:
        return []