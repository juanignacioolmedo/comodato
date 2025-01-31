import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from db_conn import raw_select

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
        SELECT IdCliente, Tipo, SUM(Cantidad) 
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
    
    query += " GROUP BY IdCliente, Tipo HAVING SUM(Cantidad) <> 0"
    
    data = raw_select(query)
    return [(row[0], row[1], row[2]) for row in data] if data else []

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
        
        # Activar el botón "Nuevo Botón" después de aplicar los filtros
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
    
    # Desactivar el botón "Nuevo Botón" al limpiar los filtros
    btn_new.config(state=tk.DISABLED)

# ----------------------------
# NUEVA FUNCIÓN PARA MOSTRAR EL MENSAJE
# ----------------------------

def show_message():
    messagebox.showinfo("Información", "BOTON ACTIVADO")

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
        text="Nuevo Botón", 
        state=tk.DISABLED,  # Inicialmente deshabilitado
        width=20,
        command=lambda: show_message()  # Acción cuando se hace clic
    )
    btn_new.pack(side=tk.LEFT, padx=10)

    tree_frame = tk.Frame(main_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True)
    
    treeview = ttk.Treeview(tree_frame, columns=("Cliente", "Tipo", "Cantidad"), show="headings")
    
    treeview.heading("Cliente", text="Cliente", anchor=tk.W)
    treeview.heading("Tipo", text="Tipo", anchor=tk.CENTER)
    treeview.heading("Cantidad", text="Cantidad", anchor=tk.E)
    
    treeview.column("Cliente", width=500, stretch=tk.YES)
    treeview.column("Tipo", width=250, stretch=tk.YES)
    treeview.column("Cantidad", width=250, stretch=tk.YES)
    
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
