import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from db_conn import raw_select
from db_conn import engine 

# ----------------------------
# FUNCIONES MODIFICADAS PARA SELECCIÓN MÚLTIPLE
# ----------------------------

def create_multi_select(parent, label_text, fetch_function, on_change_callback=None):
    frame = tk.Frame(parent)
    frame.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

    label = tk.Label(frame, text=label_text, anchor="w")
    label.pack(side=tk.TOP, anchor="w")

    listbox = tk.Listbox(
        frame, 
        selectmode=tk.MULTIPLE,  # Permite selección múltiple solo con clics
        width=30, 
        height=6,
        exportselection=False
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
        WHERE IdCliente IN (
            SELECT cliente_ruteo 
            FROM clientesrutas 
            WHERE SUBSTRING(cdruta, 1, LEN(cdruta)-1) IN (1,2,3,4,5,6)
        )
        AND Tipo = 'P'
    """
    
    if productos:
        query += f" AND IdProducto IN ({productos})"
    else:
        query += " AND IdProducto IN ('401','105','500')"
    
    if repartos:
        query += f" AND IdReparto IN ({repartos})"
    
    query += " GROUP BY IdCliente, Tipo, IdProducto HAVING SUM(Cantidad) <> 0"
    
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
        
        # Activar el botón "Nuevo Botón"
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

def confirm_and_send():
    # Mostrar diálogo de confirmación
    confirmacion = messagebox.askyesno(
        "Confirmar acción",
        "¿Está seguro que desea enviar estos cambios?"
    )
    
    if confirmacion:
        try:
            # Lógica para enviar datos (aquí irá el INSERT futuro)
            execute_insert()
            messagebox.showinfo("Éxito", "Datos enviados correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar datos:\n{str(e)}")

def execute_insert():
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener todos los registros del treeview
        records = [treeview.item(item)['values'] for item in treeview.get_children()]
        
        # Validar datos antes de ejecutar
        validate_records(records)
        
        # Ejecutar en transacción
        for record in records:
            id_cliente = record[0]
            id_producto = record[2]  # Asumiendo estructura: (Cliente, Tipo, Producto, Cantidad)
            cantidad = record[3]
            
            # Primer INSERT (Comodato)
            session.execute(text("""
                INSERT INTO dbo.Movimientos_Envases 
                (Tipo, Clase, IdReparto, IdCliente, IdProducto, Cantidad, Fecha, Vencimiento, usuario)
                VALUES ('C','A',0,:id_cliente,:id_producto,:cantidad,
                CONVERT(varchar(10),GETDATE(),103),CONVERT(varchar(10),GETDATE(),103), 'AIRTECH')
            """), {
                'id_cliente': id_cliente,
                'id_producto': id_producto,
                'cantidad': cantidad
            })
            
            # Segundo INSERT (Prestamo negativo)
            session.execute(text("""
                INSERT INTO dbo.Movimientos_Envases 
                (Tipo, Clase, IdReparto, IdCliente, IdProducto, Cantidad, Fecha, Vencimiento, usuario)
                VALUES ('P','A',0,:id_cliente,:id_producto,:cantidad_negativa,
                CONVERT(varchar(10),GETDATE(),103),CONVERT(varchar(10),GETDATE(),103), 'AIRTECH')
            """), {
                'id_cliente': id_cliente,
                'id_producto': id_producto,
                'cantidad_negativa': -1 * cantidad
            })
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise Exception(f"Error en transacción: {str(e)}")
    finally:
        session.close()
def validate_records(records):
    if not records:
        raise ValueError("No hay registros para procesar")
        
    for idx, record in enumerate(records, 1):
        try:
            if len(record) < 4:
                raise ValueError(f"Registro {idx}: Formato incorrecto")
                
            # Validar ID Cliente
            if not str(record[0]).isdigit():
                raise ValueError(f"Registro {idx}: ID Cliente inválido")
                
            # Validar ID Producto
            if not str(record[2]).isdigit():
                raise ValueError(f"Registro {idx}: ID Producto inválido")
                
            # Validar Cantidad
            if not isinstance(record[3], (int, float)) or record[3] <= 0:
                raise ValueError(f"Registro {idx}: Cantidad debe ser un número positivo")
                
        except IndexError as e:
            raise ValueError(f"Registro {idx}: Campos incompletos") from e

# ----------------------------
# FUNCIONES PARA DETECTAR CAMBIOS EN LOS FILTROS
# ----------------------------

def on_filter_change(event, reparto_listbox, producto_listbox, btn_new):
    # Deshabilitar el botón "Nuevo Botón" si las opciones de filtros cambiaron
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
    
    button_frame = tk.Frame(main_frame)
    button_frame.pack(pady=10)
    
    btn_apply = tk.Button(
        button_frame, 
        text="Aplicar Filtros", 
        command=lambda: apply_filters(treeview, reparto_listbox, producto_listbox, btn_new),
        width=20
    )
    btn_apply.pack(side=tk.LEFT, padx=10)
    
    btn_clear = tk.Button(
        button_frame, 
        text="Limpiar Filtros", 
        command=lambda: clear_filters(treeview, reparto_listbox, producto_listbox, btn_new),
        width=20
    )
    btn_clear.pack(side=tk.LEFT, padx=10)
    
    btn_new = tk.Button(
        button_frame, 
        text="Enviar Datos", 
        state=tk.DISABLED,
        width=20,
        command=confirm_and_send  # Cambiamos aquí a la nueva función
    )
    btn_new.pack(side=tk.LEFT, padx=10)

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
