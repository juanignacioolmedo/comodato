import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import OperationalError
from urllib.parse import quote_plus

engine = None
Session = scoped_session(sessionmaker())  # Inicializar con una sesión vacía
def set_conn(server, user, passwd, database):
    global engine, Session
    timeout = 30  
    passwd_escaped = quote_plus(passwd)
    connection_string = f"mssql+pyodbc://{user}:{passwd_escaped}@{server}:1433/{database}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes&timeout={timeout}"
    
    print("\n" + "="*50)
    print("Cadena de conexión generada:")
    print(connection_string)
    print("="*50 + "\n")
    
    try:
        engine = create_engine(connection_string)
        Session.configure(bind=engine)  # Vincular la sesión con la engine
        with engine.connect() as conn:
            print("Conexión exitosa al servidor.")
        return True, None  # Conexión exitosa
    except OperationalError as e:
        return False, "Hubo un problema con la conexión. Verifique los datos de conexión."
    except Exception as e:
        return False, "Ocurrió un error inesperado. Verifique los datos de conexión."


def raw_select(query):
    """
    Executes a raw SQL SELECT query and returns the results.

    :param query: The SQL SELECT query.
    :return: List of results (rows).
    """
    global Session

    try:
        result = Session.execute(text(query))
        rows = result.fetchall()
        return rows
    except Exception as e:
        print(f"Error executing query: {e}")
        return []
    finally:
        Session.remove()
"""
query = "SELECT TOP 10 *FROM [dbo].[Precios]"

query_result = raw_select(query)
print(query_result)
"""

def raw_insert(table_name, column_values, where_clause=None):
    """
    Inserts data into a specified table with an optional WHERE clause.

    :param table_name: The table name where data should be inserted.
    :param column_values: Dictionary of column names and their respective values.
    :param where_clause: Optional WHERE condition to determine if the insert should proceed.
    """
    global Session

    # Construct the SQL INSERT statement dynamically
    columns = ', '.join(column_values.keys())  # Get the column names
    values = ', '.join([f"'{v}'" for v in column_values.values()])  # Get the values

    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
    
    if where_clause:
        # If a WHERE clause is provided, prepend it to the SQL query.
        sql = f"IF NOT EXISTS (SELECT 1 FROM {table_name} WHERE {where_clause}) {sql}"

    # Execute the raw SQL insert statement
    try:
        Session.execute(text(sql))
        Session.commit()
        print(f"Inserted data into {table_name}")
    except Exception as e:
        print(f"Error inserting data: {e}")
        Session.rollback()
    finally:
        Session.remove()

# Example usage:
"""
table_name = "[dbo].[Precios]"
column_values = {"IdListaPrecio": "KK", "IdProducto": 101, "Precio": 75000}

raw_insert( table_name, column_values)
"""

def raw_update(table_name, column_values, where_clause):
    """
    Updates a record in the specified table with the given values and WHERE condition.

    :param table_name: The table where the record should be updated.
    :param column_values: Dictionary of column names and their new values.
    :param where_clause: WHERE condition to specify which record(s) to update.
    """
    global Session

    # Construct the SQL UPDATE statement dynamically
    set_clause = ', '.join([f"{col} = '{val}'" for col, val in column_values.items()])
    sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

    # Execute the raw SQL update statement
    try:
        Session.execute(text(sql))
        Session.commit()
        print(f"Updated record(s) in {table_name}")
    except Exception as e:
        print(f"Error updating record(s): {e}")
        Session.rollback()
    finally:
        Session.remove()

"""
# Example usage:
table_name = "[dbo].[Precios]"
column_values = {"IdListaPrecio": "3KK"}
where_clause = "IdListaPrecio = 'KK'"  # Condition to specify which record to update

raw_update(table_name, column_values, where_clause)
"""

def raw_delete(table_name, where_clause):
    """
    Deletes records from the specified table based on a WHERE condition.

    :param table_name: The table from which the record(s) should be deleted.
    :param where_clause: WHERE condition to specify which record(s) to delete.
    """
    global Session

    # Construct the SQL DELETE statement dynamically
    sql = f"DELETE FROM {table_name} WHERE {where_clause}"

    # Execute the raw SQL delete statement
    try:
        Session.execute(text(sql))
        Session.commit()
        print(f"Deleted record(s) from {table_name}")
    except Exception as e:
        print(f"Error deleting record(s): {e}")
        Session.rollback()
    finally:
        # Close the session
        Session.remove()
"""
# Example usage:
table_name = "[dbo].[Precios]"
where_clause = "IdListaPrecio = '3KK'"  # Condition to specify which record to update

raw_delete(table_name, where_clause)
"""