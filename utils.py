import os, shutil
from . import db
from datetime import datetime, date

PATH_H2O = 'C:/H2O/'
PATH_EXE = PATH_H2O + 'EXE/'
PATH_ARCHIVOS = PATH_H2O + 'ARCHIVOS/'
PATH_SERVICIOS = PATH_EXE + 'SERVICIOS/'
DIR_LOG = PATH_SERVICIOS + 'logs/'
ARCHIVO_LOG = DIR_LOG + 'sincro_py__VERSION__.log'
FILE_DEBUG = PATH_SERVICIOS + 'sincro_py_debug.ini'

root = PATH_ARCHIVOS
DEBUG_MODE = 0

REF = 'UTILS.py'


def set_archivo_log(version):
    global ARCHIVO_LOG
    ARCHIVO_LOG = ARCHIVO_LOG.replace('VERSION', 'v'+str(version))

def validar_args(sys_args):
    fn = f'{REF} validar_args()'
    arg_val = ['file_py','bd_web','proceso_id','debug_mode']
    arg_dic = dict(zip(arg_val, sys_args))
    arg_faltantes = [arg for arg in arg_val if not arg in arg_dic]
    arg_dic.pop('file_py')

    if len(arg_faltantes) > 0:
        arg_faltantes.remove('debug_mode')

    valido = False if len(arg_faltantes) > 0 else True

    error_log = ''
    if not valido:
        TAB = '\t'*9
        error_log += f'falta argumento de inicio:\n{TAB}{"-"*50}\n'
        for k,v in arg_dic.items():
            error_log += f'{TAB}{k} = {v}\n'
        for i in arg_faltantes:
            error_log += f'{TAB}{i} = [FALTANTE]\n'

        logging(ref=fn, tipo='ERROR', msg=error_log)


    return valido

def get_bd_web(sys_args):
    fn = f'{REF} get_bd_web()'
    if len(sys_args) >= 2:
        logging(ref=fn, tipo='INFO', msg=f'obteniendo argumento [BD_WEB] = {sys_args[1]}')
        return sys_args[1]
    logging(ref=fn, tipo='ERROR', msg='falta el primer argumento de inicio [BD_WEB]')
    return None


def date_hoy():
    return str(date.today())

def str_to_date(date_time):
    dt = str(date_time).replace('-','').replace('/','').replace(' ','')
    return dt[:8]

def get_time_now():
    return datetime.now()

def printif(*args):
    if DEBUG_MODE:
        s = ''.join([str(n)+' ' for n in args])
        t = datetime.now() if len(args) == 1 else ''
        print(s, t)

def set_debug_mode(mode):
    global DEBUG_MODE
    DEBUG_MODE = mode

'''si es booleano lo convierte a int y a str quedando True='1' o False='0'
    sino, si es nulo devuelve string vacio 
    sino, convierte el dato a string                                   '''
def is_none_to_str(strc):
    if isinstance(strc, bool):
        return str(int(strc))
    return '' if strc is None else str(strc)


def parse_dict(row):
    str_row = ''
    for key, value in row.items():
        str_row += is_none_to_str(value) 
    return str_row + '\n'

def create_if_not_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
 

def get_files(*extensiones):
    archivos = [f for f in os.listdir(root) if os.path.isfile(root+f)]
    files = []
    for f in archivos:
        for ext in extensiones:
            if f.lower().endswith(ext.lower()):
                files.append(f)
                break
    return files

def remove_bad_chars(str_bad):
    chars = ['"',"'"]
    str_bad = str(str_bad)
    for char in chars:
        str_bad = str_bad.replace(char, '')
    return str_bad

def remove_file(path_archivo):
    try:
        if os.path.exists(path_archivo):
            if os.path.isfile(path_archivo):
                os.remove(path_archivo)
    except Exception as e:
        print(e)

def remove_dir(path):
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
    except Exception as e:
        print(e)



def eliminar_archivos():
    printif('eliminando archivos')
    create_if_not_exists(root)
    for file in get_files('.txt','.zip'):
        try:
            os.remove(root+file)
        except Exception as e:
            db.auditar_err(f'Error eliminando archivo {file}, exception: {e}') 






def imprimir_archivos(ext='.txt'):
    if not DEBUG_MODE:
        return None
    archivos = get_files(ext)
    if len(archivos)>1:
        fb = sum([os.path.getsize(root+file) for file in archivos])
        printif('\t',len(archivos),'archivos', '\t\t\t', fb,'(B) - ', int(fb/1024),'(KB)\n')
    
    for file in archivos:
        size = os.path.getsize(root+file)
        printif('\t\t',file, '\t\t', size,'(B) - ', int(size/1024),'(KB)')


def get_sql_params_DEBUG():
    fn = f'{REF} get_sql_params_DEBUG()'

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
    if not os.path.exists(FILE_DEBUG) or not os.path.isfile(FILE_DEBUG):
        return []

    try:
        with open(FILE_DEBUG, 'r') as f:
            sql_params = [p.replace('\n','') for p in f.readlines() if p.strip() != '' and p.count('=') == 1]
            if len(sql_params) != 4:
                logging(ref=fn, tipo='ERROR', msg=msg)
                return []

        KEYS_ESPERADAS = ['database', 'password', 'server', 'user']
        params_dict = {p.split('=')[0].strip() : p.split('=')[1].strip() for p in sql_params}
        KEYS_VALIDAS = True

        for k in KEYS_ESPERADAS:
            if not k in params_dict:
                msg += f'\n\nATENCION: LA VARIABLE [{k}] NO EXISTE'
                KEYS_VALIDAS = False
                break


        if not KEYS_VALIDAS:
            logging(ref=fn, tipo='ERROR', msg=msg)
            return []

        PR = params_dict
        logging(ref=fn, tipo='INFO', msg=str(PR))
        return PR['server'], PR['user'], PR['password'], PR['database']

    except Exception as e:
        print(e)
        logging(ref=fn, tipo='ERROR', msg=str(e))
        return []


def logging(ref='', tipo='INI', msg=''):
    msg = str(msg)
    try:
        create_if_not_exists(DIR_LOG)
        modo = 'w' if tipo=='INI' else 'a'
        msg = 'INI LOG' if tipo=='INI' else msg
        tipo = f'{tipo} {"#"*9}' if tipo=='ERROR' else f'{tipo}{" "*(15-len(tipo))}'
        time = get_time_now()
        #input(tipo + str(time))
        with open(ARCHIVO_LOG, modo) as f:
            f.write(f'{time} - {tipo} - {ref} - {msg}\n')

    except Exception as e:
        raise e    


