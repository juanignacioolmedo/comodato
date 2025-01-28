import tkinter as tk
from tkinter import ttk
from db_conn import raw_select


# Function to create the Treeview widget
def create_treeview(parent):
    treeview = ttk.Treeview(parent, columns=("idproducto", "abreviatura", "descripcion"), show="headings")
    treeview.heading("idproducto", text="idproducto")
    treeview.heading("abreviatura", text="abreviatura")
    treeview.heading("descripcion", text="descripcion")
    
    treeview.column("idproducto", width=150, anchor="w")
    treeview.column("abreviatura", width=100, anchor="center")
    treeview.column("descripcion", width=150, anchor="w")
    
    treeview.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    return treeview


# Function to populate the Treeview with data
def populate_treeview(treeview, data):
    for row in treeview.get_children():
        treeview.delete(row)
    
    for item in data:
        try:
            formatted_value_1 = f"{int(item[0]):,}"
        except ValueError:
            formatted_value_1 = item[0]
        formatted_value_2 = item[1]
        formatted_value_3 = item[2]
        treeview.insert("", tk.END, values=(formatted_value_1, formatted_value_2, formatted_value_3))


# Function to fetch products based on selected repartos and update the Treeview
def fetch_products_by_repartos(treeview, reparto_codigos=None):
    query = "SELECT idproducto, abreviatura, descripcion FROM productos"
    if reparto_codigos:
        # Create a SQL IN clause with the selected reparto codes
        reparto_filter = ", ".join(f"'{codigo}'" for codigo in reparto_codigos)
        query += f" WHERE reparto_codigo IN ({reparto_filter})"
    
    data = raw_select(query)
    populate_treeview(treeview, data if data else [])


# Function to fetch repartos and populate the Listbox
def fetch_and_populate_repartos(listbox):
    query = "SELECT codigo, descrp FROM repartos"
    data = raw_select(query)
    
    if data:
        reparto_map = {row[1]: row[0] for row in data}  # Map description to code
        listbox.reparto_map = reparto_map  # Store the map in the Listbox for later reference
        
        # Insert descriptions into the Listbox
        for descrp in reparto_map.keys():
            listbox.insert(tk.END, descrp)
    else:
        listbox.reparto_map = {}


# Function to create reparto selector
def create_reparto_selector(root, treeview):
    frame = tk.Frame(root)
    frame.pack(pady=10, padx=10, fill=tk.X)
    
    tk.Label(frame, text="Seleccione Repartos:").pack(side=tk.LEFT, padx=5)
    
    reparto_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=8, exportselection=0)
    reparto_listbox.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
    
    # Fetch and populate repartos
    fetch_and_populate_repartos(reparto_listbox)
    
    # Button to apply filter
    def apply_filter():
        selected_indices = reparto_listbox.curselection()
        selected_descriptions = [reparto_listbox.get(i) for i in selected_indices]
        selected_codes = [reparto_listbox.reparto_map[desc] for desc in selected_descriptions]
        
        if selected_codes:
            fetch_products_by_repartos(treeview, reparto_codigos=selected_codes)
        else:
            print("Debe seleccionar al menos un reparto.")
    
    filter_button = tk.Button(frame, text="Filtrar", command=apply_filter)
    filter_button.pack(side=tk.LEFT, padx=5)
    
    # Button to clear filters
    def clear_filter():
        reparto_listbox.selection_clear(0, tk.END)  # Clear selections in Listbox
        fetch_products_by_repartos(treeview)  # Fetch all products
    
    clear_button = tk.Button(frame, text="Eliminar Filtros", command=clear_filter)
    clear_button.pack(side=tk.LEFT, padx=5)
    
    return reparto_listbox


# Function to set up the main window
def setup_window():
    root = tk.Tk()
    root.title("Database Grid Example")
    
    # Create Treeview widget
    treeview = create_treeview(root)
    
    # Create reparto selector
    create_reparto_selector(root, treeview)
    
    # Fetch initial data for the grid
    fetch_products_by_repartos(treeview)
    
    return root


# Main function to run the application
def main():
    root = setup_window()
    root.mainloop()


# Entry point
if __name__ == "__main__":
    main()
