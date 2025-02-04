import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from db_conn import raw_select
from db_conn import engine 
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# ----------------------------
# FUNCIONES MODIFICADAS PARA SELECCIÓN MÚLTIPLE
# ----------------------------

def create_multi_select(parent, label_text, fetch_function, on_change_callback=None):
    frame = tk.Frame(parent)
    frame.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

    label = tk.Label(frame, text=label_text, anchor="w", font=("Arial", 14, "bold"))
    label.pack(side=tk.TOP, anchor="w")

    listbox = tk.Listbox(
        frame, 
        selectmode=tk.EXTENDED,  # Permite selección múltiple con control y shift
        width=30, 
        height=6,
        exportselection=False,
        font=("Arial", 14)  # Aumentar la fuente del Listbox
    )
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=listbox.yview)
    listbox.config(yscrollcommand=scrollbar.set)

    # Cargar opciones
    options = fetch_function()
    for item in options:
        listbox.insert(tk.END, item)

    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Vincular la acción de cambio de selección al callback
    if on_change_callback:
        listbox.bind('<<ListboxSelect>>', on_change_callback)

    return listbox, frame

# Obtener IDs seleccionados correctamente
def get_selected_ids(listbox):
    selected = [listbox.get(i).split(" - ")[0] for i in listbox.curselection()]
    return ",".join([f"'{id}'" for id in selected]) if selected else None

# ----------------------------
# FUNCIONES DE DATOS ACTUALIZADAS
# ----------------------------

def fetch_repartos():
    query = "SELECT Codigo, Descrp FROM repartos"
    data = raw_select(query)
    return [f"{row[0]} - {row[1]}" for row in data] if data else []

def fetch_productos():
    query = "SELECT idProducto, Descripcion FROM productos"
    data = raw_select(query)
    return [f"{row[0]} - {row[1]}" for row in data] if data else []

def fetch_client_data(repartos=None, productos=None):
    query = """
        SELECT IdCliente, Tipo, IdProducto, SUM(Cantidad) 
        FROM movimientos_envases 
        WHERE Tipo = 'P'
            AND idcliente <> 0
    """
    
    if productos:
        query += f" AND IdProducto IN ({productos})"
    else:
        query += " "
    
    if repartos:
        query += f"""AND IdCliente IN (
            SELECT cliente_ruteo 
            FROM clientesrutas 
            WHERE SUBSTRING(cdruta, 1, LEN(cdruta)-1) IN ({repartos})
        )"""
        # query += f" AND IdReparto IN ({repartos})"
    
    query += " GROUP BY IdCliente, Tipo, IdProducto HAVING SUM(Cantidad) <> 0 ORDER BY IdCliente,idproducto"
    
    data = raw_select(query)
    return [(row[0], row[1], row[2], row[3]) for row in data] if data else []

# ----------------------------
# FUNCIONES DE FILTRADO ACTUALIZADAS
# ----------------------------

def apply_filters(treeview, reparto_listbox, producto_listbox, btn_new):
    try:
        repartos = get_selected_ids(reparto_listbox)
        productos = get_selected_ids(producto_listbox)
        
        filtered_data = fetch_client_data(repartos, productos)
        
        treeview.delete(*treeview.get_children())
        for row in filtered_data:
            treeview.insert("", tk.END, values=row)
        
        """
        # Imprimir en consola los datos filtrados
        print("\n" + "="*50)
        print("Registros filtrados en el treeview:")
        print("-"*50)
        print(f"{'Cliente':<10} | {'Tipo':<5} | {'Producto':<10} | {'Cantidad':<10}")
        print("-"*50)
        
        for item in treeview.get_children():
            values = treeview.item(item)['values']
            print(f"{values[0]:<10} | {values[1]:<5} | {values[2]:<10} | {values[3]:<10}")
        
        print("="*50 + "\n")
        """

        # Activar el botón "Enviar Datos"
        btn_new.config(state=tk.NORMAL)
            
    except Exception as e:
        messagebox.showerror("Error", f"Error al aplicar filtros:\n{str(e)}")

def clear_filters(treeview, reparto_listbox, producto_listbox, btn_new):
    reparto_listbox.selection_clear(0, tk.END)
    producto_listbox.selection_clear(0, tk.END)
    
    original_data = fetch_client_data()
    treeview.delete(*treeview.get_children())
    for row in original_data:
        treeview.insert("", tk.END, values=row)
    
    # Desactivar el botón "Enviar Datos" al limpiar los filtros
    btn_new.config(state=tk.DISABLED)

# ----------------------------
# NUEVAS FUNCIONES PARA CONFIRMACIÓN Y ENVÍO
# ----------------------------

def confirm_and_send(treeview):
    confirmacion = messagebox.askyesno(
        "Confirmar acción",
        "¿Está seguro que desea enviar estos cambios?"
    )
    
    if confirmacion:
        loading_window = None
        try:
            # Mostrar ventana de loading
            loading_window = tk.Toplevel()
            loading_window.title("Procesando...")
            loading_window.geometry("200x60")
            tk.Label(loading_window, text="Aguarde por favor ...").pack(pady=15)
            loading_window.grab_set()
            treeview.master.update_idletasks()  # Forzar actualización de la UI
            
            execute_insert(treeview)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar datos:\n{str(e)}")
        finally:
            if loading_window:
                loading_window.destroy()

def execute_insert(treeview):
    try:
        # Crear una sesión para interactuar con la base de datos
        Session = sessionmaker(bind=engine)
        session = Session()        
        # Obtener todos los registros del treeview
        records = [treeview.item(item)['values'] for item in treeview.get_children()]
        # Validar datos antes de ejecutar
        validate_records(records)
        # Contador para verificar inserts exitosos
        total_records = len(records)
        successful_records = 0

        # Ejecutar en transacción
        for record in records:
            id_cliente = record[0]
            id_producto = record[2]
            cantidad = record[3]
            
            # Convertir a valor absoluto (opción activa)
            cantidad = abs(float(cantidad))

            # Primer INSERT (Comodato)
            session.execute(text("""
                INSERT INTO dbo.Movimientos_Envases 
                (Tipo, Clase, IdReparto, IdCliente, IdProducto, Cantidad, Fecha, Vencimiento, usuario)
                VALUES ('C','A',0,:id_cliente,:id_producto,:cantidad,
                CONVERT(varchar(10), GETDATE(), 120), CONVERT(varchar(10), GETDATE(), 120), 'AIRTECH')
            """), {
                'id_cliente': id_cliente,
                'id_producto': id_producto,
                'cantidad': cantidad  
            })

            # Segundo INSERT (Préstamo negativo)
            session.execute(text("""
                INSERT INTO dbo.Movimientos_Envases 
                (Tipo, Clase, IdReparto, IdCliente, IdProducto, Cantidad, Fecha, Vencimiento, usuario)
                VALUES ('P','A',0,:id_cliente,:id_producto,:cantidad,
                CONVERT(varchar(10), GETDATE(), 120), 
                CONVERT(varchar(10), GETDATE(), 120), 
                'AIRTECH'
            )
            """), {
                'id_cliente': int(id_cliente),  
                'id_producto': int(id_producto),
                'cantidad': cantidad  # Usamos el valor ya convertido
            })

            successful_records += 1 # Incrementar contador de registros exitosos

        session.commit()
        
        # Verificación final
        if successful_records == total_records:
            messagebox.showinfo("",f"✅ Todos los registros se insertaron correctamente ({successful_records}/{total_records})")
        else:
            messagebox.showinfo("",f"⚠️ Solo se insertaron {successful_records} de {total_records} registros")

    except Exception as e:
        session.rollback()
        raise Exception(f"Error en transacción: {str(e)}")
    finally:
        session.close()

def verify_inserts(id_cliente, id_producto):
    from db_conn import raw_select  # Importar la función de consulta
    
    # Consulta para verificar los inserts
    query = f"""
        SELECT Tipo, IdCliente, IdProducto, Cantidad, Fecha
        FROM dbo.Movimientos_Envases
        WHERE IdCliente = '{id_cliente}'
        AND IdProducto = '{id_producto}'
        AND Fecha = CONVERT(varchar(10), GETDATE(), 103)
        AND usuario = 'AIRTECH'
    """
    
    # Ejecutar la consulta
    result = raw_select(query)
    
    if result:
        print("✅ Registros insertados verificados:")
        for row in result:
            print(f"Tipo: {row[0]}, Cliente: {row[1]}, Producto: {row[2]}, Cantidad: {row[3]}, Fecha: {row[4]}")
    else:
        print("⚠️ No se encontraron registros insertados.")

def validate_records(records):
    for idx, record in enumerate(records, 1):
        try:
            # Convertir a tipos correctos
            id_cliente = int(record[0])
            id_producto = int(record[2])
            cantidad = float(record[3])
               
        except ValueError as e:
            raise ValueError(f"Registro {idx}: Dato inválido - {str(e)}")
        except IndexError:
            raise ValueError(f"Registro {idx}: Campos incompletos")
# ----------------------------
# FUNCIONES PARA DETECTAR CAMBIOS EN LOS FILTROS
# ----------------------------

def on_filter_change(event, reparto_listbox, producto_listbox, btn_new):
    # Deshabilitar el botón "Enviar Datos" si las opciones de filtros cambiaron
    btn_new.config(state=tk.DISABLED)

# ----------------------------
# INTERFAZ ACTUALIZADA
# ----------------------------

def setup_window():
    root = tk.Tk()
    root.title("Comodato")
    root.geometry("1400x750")  
    
    main_frame = tk.Frame(root)
    main_frame.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
    
    filter_container = tk.Frame(main_frame)
    filter_container.pack(fill=tk.X, pady=10)
    
    # Crear los filtros con el callback para detectar cambios
    reparto_listbox, _ = create_multi_select(filter_container, "Repartos:", fetch_repartos, 
                                             lambda event: on_filter_change(event, reparto_listbox, producto_listbox, btn_new))
    producto_listbox, _ = create_multi_select(filter_container, "Productos:", fetch_productos, 
                                              lambda event: on_filter_change(event, reparto_listbox, producto_listbox, btn_new))
    
    # Aplicar estilos con fuente más grande
    button_font = ("Arial", 14, "bold")  # Definir un estilo de fuente para los botones


    button_frame = tk.Frame(main_frame)
    button_frame.pack(pady=10)
    
    btn_apply = tk.Button(
        button_frame, 
        text="Aplicar Filtros", 
        command=lambda: apply_filters(treeview, reparto_listbox, producto_listbox, btn_new),
        width=20,
        font=button_font  # Aplicar el tamaño de fuente
    )
    btn_apply.pack(side=tk.LEFT, padx=10)
    
    btn_clear = tk.Button(
        button_frame, 
        text="Limpiar Filtros", 
        command=lambda: clear_filters(treeview, reparto_listbox, producto_listbox, btn_new),
        width=20,
        font=button_font
    )
    btn_clear.pack(side=tk.LEFT, padx=10)
    
    btn_new = tk.Button(
        button_frame, 
        text="Enviar Datos", 
        state=tk.DISABLED,
        width=20,
        font=button_font,
        command=lambda: confirm_and_send(treeview)
    )
    btn_new.pack(side=tk.LEFT, padx=10)

    # Crear un estilo para personalizar el Treeview
    style = ttk.Style()
    style.configure("Treeview", font=("Arial", 14))
    style.configure("Treeview.Heading", font=("Arial", 16, "bold"))

    tree_frame = tk.Frame(main_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True)
    
    treeview = ttk.Treeview(tree_frame, columns=("Cliente", "Tipo", "Producto", "Cantidad"), show="headings")
    
    # Configurar los encabezados
    treeview.heading("Cliente", text="Cliente", anchor=tk.W)
    treeview.heading("Tipo", text="Tipo", anchor=tk.CENTER)
    treeview.heading("Producto", text="Producto", anchor=tk.CENTER)
    treeview.heading("Cantidad", text="Cantidad", anchor=tk.E)

    # Configurar las columnas
    treeview.column("Cliente", width=400, stretch=tk.YES)
    treeview.column("Tipo", width=200, stretch=tk.YES)
    treeview.column("Producto", width=200, stretch=tk.YES)
    treeview.column("Cantidad", width=200, stretch=tk.YES)
    
    # Configurar la barra de desplazamiento
    vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=treeview.yview)
    hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=treeview.xview)
    treeview.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    
    treeview.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)
    
    clear_filters(treeview, reparto_listbox, producto_listbox, btn_new)
    
    return root

if __name__ == "__main__":
    app = setup_window()
    app.mainloop()