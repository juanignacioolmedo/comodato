import tkinter as tk
from tkinter import ttk
from db_conn import raw_select

# Function to create the Treeview widget with checkboxes
def create_checkbox_treeview(parent, data):
    treeview = ttk.Treeview(parent, columns=("cliente", "tipo", "cantidad"), show="headings")
    treeview.heading("cliente", text="Cliente")
    treeview.heading("tipo", text="Tipo")
    treeview.heading("cantidad", text="Cantidad")
    
    treeview.column("cliente", width=100, anchor="w")
    treeview.column("tipo", width=100, anchor="w")
    treeview.column("cantidad", width=100, anchor="w")

    # Insert the data into the treeview
    for row in data:
        treeview.insert("", "end", values=row)

    treeview.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    return treeview

# Function to fetch data for the checkbox Treeview
def fetch_client_data():
    query = """
        SELECT idcliente, tipo, SUM(cantidad) 
        FROM movimientos_envases 
        WHERE idcliente IN (
            SELECT cliente_ruteo 
            FROM clientesrutas 
            WHERE SUBSTRING(cdruta, 1, LEN(cdruta)-1) IN (1,2,3,4,5,6)
        )
        AND idproducto IN ('401','105','500')
        AND tipo = 'P'
        GROUP BY idcliente, tipo
        HAVING SUM(cantidad) <> 0
    """
    data = raw_select(query)
    return [(row[0], row[1], row[2]) for row in data] if data else []

# Function to create filter selectors with dropdown menus
def create_filter_selector(root, label_text, fetch_function):
    frame = tk.Frame(root)
    frame.pack(pady=5, padx=5, fill=tk.X)

    label = tk.Label(frame, text=label_text, anchor="w")
    label.pack(side=tk.LEFT, padx=(0, 5))

    selected_value = tk.StringVar()
    dropdown = ttk.Combobox(frame, textvariable=selected_value, state="readonly", width=25)
    dropdown.pack(side=tk.LEFT, padx=(0, 10))

    options = fetch_function()
    dropdown["values"] = options

    return selected_value, dropdown, frame

# Function to fetch repartos
def fetch_repartos():
    query = "SELECT descrp FROM repartos"
    data = raw_select(query)
    return [row[0] for row in data] if data else []

# Function to fetch productos
def fetch_productos():
    query = "SELECT descripcion FROM productos"
    data = raw_select(query)
    return [row[0] for row in data] if data else []

# Function to apply filters
def apply_filters():
    print("Aplicar filtros")

# Function to clear filters
def clear_filters(reparto_var, producto_var):
    reparto_var.set("")
    producto_var.set("")
    print("Filtros borrados")

# Function to set up the main window
def setup_window():
    root = tk.Tk()
    root.title("Clientes y Filtros")
    root.geometry("500x400")

    # Create top frame for filters and buttons
    top_frame = tk.Frame(root)
    top_frame.pack(pady=10, padx=10, fill=tk.X)

    # Create filters for Repartos and Productos in the same line
    filter_frame = tk.Frame(top_frame)
    filter_frame.pack(side=tk.TOP, fill=tk.X)

    reparto_var, reparto_dropdown, reparto_frame = create_filter_selector(filter_frame, "Seleccione Reparto:", fetch_repartos)
    producto_var, producto_dropdown, producto_frame = create_filter_selector(filter_frame, "Seleccione Producto:", fetch_productos)

    # Create buttons to apply and clear filters
    button_frame = tk.Frame(top_frame)
    button_frame.pack(side=tk.TOP, fill=tk.X)

    apply_button = tk.Button(button_frame, text="Aplicar Filtros", command=apply_filters, width=15)
    apply_button.pack(side=tk.LEFT, padx=5)

    clear_button = tk.Button(button_frame, text="Borrar Filtros", command=lambda: clear_filters(reparto_var, producto_var), width=15)
    clear_button.pack(side=tk.LEFT, padx=5)

    # Fetch client data and create Treeview with checkboxes
    client_data = fetch_client_data()
    treeview = create_checkbox_treeview(root, client_data)

    return root

# Main function to run the application
def main():
    root = setup_window()
    root.mainloop()

# Entry point
if __name__ == "__main__":
    main()
