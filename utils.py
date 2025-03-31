import os, shutil
from datetime import datetime, date

# PATH_H2O = 'C:/H2O/'
# PATH_EXE = PATH_H2O + 'EXE/'
PATH_H2O = './'
PATH_EXE = os.path.join(PATH_H2O, 'EXE')
ini_path = os.path.join(PATH_EXE, 'H2O.ini')

# root = PATH_ARCHIVOS
DEBUG_MODE = 0

REF = 'UTILS.py'


def get_bdweb_h2o_ini():
    fn = f'{REF} get_bdweb_h2o_ini()'

    msg = """ERROR en algun parametro SQL
            el nombre de las variables deben estar en minusculas
            \nrevisar ARCHIVO: sincro_py_debug.ini
            ------------------------------------------
            database = ......
            password = ......
            server = ......
            user = ......
            ------------------------------------------
            """
    msg = msg.replace('  ','')
    sql_params = []
    try:
        if not os.path.exists(PATH_EXE) or not os.path.isfile(ini_path):
            raise FileNotFoundError(f"El archivo {PATH_EXE}/H2O.ini no existe.")
    
        with open(PATH_EXE+'/H2O.ini', 'r') as f:
            sql_params = [p.replace('\n','') for p in f.readlines() if p.strip() != '' and p.count('=') == 1]

        KEYS_ESPERADAS = ['BD_WEB']
        params_dict = {p.split('=')[0].strip() : p.split('=')[1].strip() for p in sql_params}
        KEYS_VALIDAS = True

        for k in KEYS_ESPERADAS:
            if not k in params_dict:
                msg += f'\n\nATENCION: LA VARIABLE [{k}] NO EXISTE'
                KEYS_VALIDAS = False
                print(msg)
                break


        if not KEYS_VALIDAS:
            print(msg)
            return ''

        PR = params_dict
        return PR['BD_WEB']

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return ''
    except Exception as e:
        print(f"Error inesperado al leer el archivo H2O.ini: {e}")
        return ''

if __name__ == "__main__":
    print(get_bdweb_h2o_ini())