import os, pymssql
from . import utils


db_proceso_id = 0
db_conn = None

REF = 'DB.py'

def get_conn():
  return db_conn

def set_conn(server, user, password, database):
  fn = f'{REF} set_conn()'
  try:
    global db_conn
    db_conn = pymssql.connect(server, user, password, database)
    utils.printif('conectando bd')
  except Exception as e:
    error_log = f'''Error conectando bd:
                    args[
                        server="{server}"
                        user="{user}"
                        password="{password}"
                        database="{database}"
                    ]
                    Exception: {e}'''
    utils.logging(ref=fn, tipo='ERROR', msg=error_log)
    utils.printif(error_log) 
    auditar_err(f"Error: {e}")

def close_conn():
  try:
    db_conn.close()
  except Exception as e:
      pass


def set_proceso_id(proceso_id):
	global db_proceso_id
	db_proceso_id = proceso_id


def auditar(msg, error, fin):
  try:
    msg = utils.remove_bad_chars(msg)
    sql = f"""INSERT INTO sincro_proceso_resultado 
        (idproceso, fecha, resultado, error, fin_proceso)
        VALUES ({db_proceso_id},GETDATE(),'{msg}',{error},{fin})"""

    conn = get_conn()
    cursor = conn.cursor(as_dict=True)
    cursor.execute(sql)
    conn.commit()

    TIPO = 'ERROR' if error == 1 else 'INFO'
    utils.logging(ref='__BD__', tipo=TIPO, msg=msg)

  except Exception as e:
    utils.logging(ref='__BD_Exception__', tipo='ERROR', msg=e)


def auditar_ok(info):
    auditar(msg=info, error=0, fin=0)

def auditar_fin(info):
    auditar(msg=info, error=0, fin=1)

def auditar_err(info):
    auditar(msg=info, error=1, fin=0)

def sp_commit(sp, param_sp=[]):
  try:
    conn = get_conn()
    cursor = conn.cursor(as_dict=True)
    cursor.callproc(sp, param_sp)
    conn.commit()
  except Exception as e:
    auditar_err(f"Error: {e}")
    utils.logging(ref='__BD_Exception__', tipo='ERROR', msg=e)

def sp_fetch(sp, param_sp=[]):
  try:
    conn = get_conn()
    cursor = conn.cursor(as_dict=True)
    cursor.callproc(sp, param_sp)
    return cursor
  except Exception as e:
    auditar_err(f"Error: {e}")
    utils.logging(ref='__BD_Exception__', tipo='ERROR', msg=e)


def qry_fetch(query):
  try:
    conn = get_conn()
    cursor = conn.cursor(as_dict=True)
    cursor.execute(query)
    return cursor
  except Exception as e:
    auditar_err(f"Error: {e}")
    utils.logging(ref='__BD_Exception__', tipo='ERROR', msg=e)


def get_sincro_parametros(column):
  try:
    query = f'select {column} from sincro_proceso_parametros where id = {db_proceso_id}' 
    cursor = qry_fetch(query)
    return cursor.fetchone()
  except Exception as e:
    auditar_err(f"Error: {e}")
    utils.logging(ref='__BD_Exception__', tipo='ERROR', msg=e)

def get_data_sincro(column):
  try:
    row = get_sincro_parametros(column)
    if row != None:
      if column in row:
        return utils.is_none_to_str(row[column])
    return ''
  except Exception as e:
    auditar_err(f"Error: {e}")
    utils.logging(ref='__BD_Exception__', tipo='ERROR', msg=e)

########################################################################################
def sincronizacion_calculacuota(temporada, bultos_o_litros, continuar):
  try:
    sp = 'sincronizacion_calculacuota'
    continuar(f'ANTES DE {sp}')
    auditar_ok(f'inicio proceso {sp}')
    sp_commit(sp, [temporada, bultos_o_litros])
    auditar_ok(f'fin proceso {sp}')
  except Exception as e:
    auditar_err(f"Error: {e}")
    utils.logging(ref='__BD_Exception__', tipo='ERROR', msg=e)

def sincro_proceso_parametros(continuar):
  try:
    proceso = 'consulta sincro_proceso_parametros'
    utils.printif(proceso)
    auditar_ok(f'inicio {proceso}')
    '''
    sql = f"""select clientes = isnull(clientes_comodatos, 1),
                  productos = isnull(productos, 1),
                  precios = isnull(precios, 1),
                  impuestos = isnull(impuestos, 1),
                  novedades = isnull(novedades, 1),
                  stock_sincro = isnull(stock, 1),
                  rutas = isnull(rutas, 1), 
                  alertas = isnull(alertas, 1), 
                  fecha_reparto, 
                  ajuste_prestamo_desde, 
                  ajuste_prestamo_hasta, 
                  fecha_novedades = novedades_desde, 
                  alertas_deuda = isnull(antiguedad_deuda, 1), 
                  alertas_improductivos = isnull(improductivos, 1), 
                  alertas_prestamos_vencidos = isnull(prestamos_vencidos, 1), 
                  antiguedad_deuda_importe = isnull(antiguedad_deuda_deuda_importe, 1), 
                  antiguedad_deuda_dias = isnull(antiguedad_deuda_deuda_dias, 30), 
                  improductivos_dias_consumo = isnull(improductivos_dias_consumo, 0), 
                  improductivos_incluye_prestados = isnull(improductivos_incluye_prestados, 0), 
                  improductivos_dias_vencimiento_prestamo = isnull(improductivos_dias_vencimiento_prestamo, 30), 
                  prestamos_vencidos_prestamos_dias = isnull(prestamos_vencidos_prestamos_dias, 0), 
                  temporada = isnull(temporada_activa, (select top 1 idTemporada from Temporadas)), 
                  bultos_o_litros = isnull(bultos_o_litros, 1), 
                  precios_clering_fc = isnull(precios_clering_fc, 1), 
                  precios_servicios_cuentas_hijas = isnull(precios_servicios_cuentas_hijas, 0),
                  jurisdiccion_multiple = isnull(jurisdiccion_multiple, 0),
                  percep_iva_alcanzado = isnull(percep_iva_alcanzado,0),
                  percep_iva_vigencia_desde,
                  percep_iva_basecalculo = isnull(percep_iva_basecalculo,999999)
          from sincro_proceso_parametros where id = {proceso_id}"""
    '''
    cursor = sp_fetch('sincro_proceso_parametros_PY', [db_proceso_id])
    c_next = cursor.nextset()
    if c_next != None:
        rows = cursor.fetchall()
    rc = cursor.rowcount

    if rc == 0:
        auditar_err(f'Error en {proceso}, id:{db_proceso_id}')
        continuar(False)

    auditar_ok(f'fin {proceso}, cantidad registros: {rc}')
    return rows[0]
  except Exception as e:
    auditar_err(f"Error: {e}")
    utils.logging(ref='__BD_Exception__', tipo='ERROR', msg=e)
