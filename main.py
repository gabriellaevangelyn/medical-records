# Medicine Expiry and Stock Management System
# By the best coder in 12th CBSE, obviously.
# This project uses Python with Tkinter for the UI and MySQL for the database.

import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- Global Variables ---
# I'm keeping these global for simplicity, as per the function-based approach.
db_connection = None
db_cursor = None


# --- Database Connection ---
def connect_to_database():
    """Establishes connection to the MySQL database."""
    global db_connection, db_cursor
    try:
        # --- IMPORTANT ---
        # Replace with your own MySQL credentials before running.
        db_connection = mysql.connector.connect(
            host="localhost",
            user="root",  # <-- Change this to your MySQL username
            password="daniel",  # <-- Change this to your MySQL password
            database="pharmacy-final"
        )
        db_cursor = db_connection.cursor()
        print("Database connection successful.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        messagebox.showerror("Database Error",
                             f"Could not connect to the database: {err}\nPlease ensure MySQL is running and credentials are correct.")
        root.destroy()  # Close the app if DB connection fails


# --- UI Helper Functions ---
def clear_entry_fields(widgets):
    """Clears all provided Tkinter Entry widgets."""
    for widget in widgets:
        widget.delete(0, tk.END)


def populate_treeview(tree, records):
    """Clears and populates the treeview with new records."""
    # Clear existing items
    for item in tree.get_children():
        tree.delete(item)
    # Insert new items
    for row in records:
        tree.insert("", "end", values=row)


# --- Core Functionalities ---
def fetch_all_medicines():
    """Fetches all records from the Medicines table and displays them."""
    db_cursor.execute("SELECT * FROM Medicines")
    records = db_cursor.fetchall()
    populate_treeview(tree, records)
    # Clear any previous tags like 'expired' or 'expiring_soon'
    for item in tree.get_children():
        tree.item(item, tags=())


def add_medicine():
    """Handles the logic to add a new medicine record to the database."""
    # Retrieve data from entry fields
    name = name_entry.get()
    category = category_entry.get()
    price = price_entry.get()
    quantity = quantity_entry.get()
    mfg_date = mfg_date_entry.get()
    exp_date = exp_date_entry.get()
    supplier = supplier_entry.get()

    # Basic validation
    if not all([name, price, quantity, mfg_date, exp_date]):
        messagebox.showerror("Input Error", "Please fill all required fields (Name, Price, Qty, Mfg/Exp Date).")
        return

    try:
        # SQL query to insert a new record
        sql = "INSERT INTO Medicines (name, category, price, quantity, mfg_date, exp_date, supplier) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = (name, category, float(price), int(quantity), mfg_date, exp_date, supplier)
        db_cursor.execute(sql, values)
        db_connection.commit()
        # Also add initial stock to history
        new_med_id = db_cursor.lastrowid
        history_sql = "INSERT INTO StockHistory (medicine_id, change_date, quantity) VALUES (%s, %s, %s)"
        history_values = (new_med_id, date.today(), int(quantity))
        db_cursor.execute(history_sql, history_values)
        db_connection.commit()

        messagebox.showinfo("Success", "Medicine added successfully!")
        add_window.destroy()  # Close the add window
        fetch_all_medicines()  # Refresh the main view
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to add medicine: {err}")
    except ValueError:
        messagebox.showerror("Input Error", "Please check Price and Quantity fields for correct numeric values.")


def update_medicine():
    """Handles the logic to update a selected medicine record."""
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select a medicine to update.")
        return

    # Retrieve new data from entry fields in the update window
    name = update_name_entry.get()
    category = update_category_entry.get()
    price = update_price_entry.get()
    quantity = update_quantity_entry.get()
    mfg_date = update_mfg_date_entry.get()
    exp_date = update_exp_date_entry.get()
    supplier = update_supplier_entry.get()

    selected_values = tree.item(selected_item, 'values')
    medicine_id = selected_values[0]
    original_quantity = selected_values[4]

    try:
        sql = """
            UPDATE Medicines 
            SET name=%s, category=%s, price=%s, quantity=%s, mfg_date=%s, exp_date=%s, supplier=%s 
            WHERE id=%s
        """
        values = (name, category, float(price), int(quantity), mfg_date, exp_date, supplier, medicine_id)
        db_cursor.execute(sql, values)
        db_connection.commit()

        # If quantity changed, add a record to history
        if int(quantity) != int(original_quantity):
            history_sql = "INSERT INTO StockHistory (medicine_id, change_date, quantity) VALUES (%s, %s, %s)"
            history_values = (medicine_id, date.today(), int(quantity))
            db_cursor.execute(history_sql, history_values)
            db_connection.commit()

        messagebox.showinfo("Success", "Medicine updated successfully!")
        update_window.destroy()
        fetch_all_medicines()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to update medicine: {err}")
    except ValueError:
        messagebox.showerror("Input Error", "Please ensure Price and Quantity are valid numbers.")


def delete_medicine():
    """Deletes the selected medicine record from the database."""
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select a medicine to delete.")
        return

    if not messagebox.askyesno("Confirm Delete",
                               "Are you sure you want to delete this medicine? This will also delete its stock history."):
        return

    try:
        selected_values = tree.item(selected_item, 'values')
        medicine_id = selected_values[0]
        # ON DELETE CASCADE will handle the StockHistory table
        sql = "DELETE FROM Medicines WHERE id = %s"
        db_cursor.execute(sql, (medicine_id,))
        db_connection.commit()
        messagebox.showinfo("Success", "Medicine deleted successfully!")
        fetch_all_medicines()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to delete medicine: {err}")


def search_medicine():
    """Searches for medicines based on the query in the search bar."""
    query = search_entry.get()
    if not query:
        fetch_all_medicines()
        return

    try:
        sql = "SELECT * FROM Medicines WHERE name LIKE %s OR category LIKE %s OR supplier LIKE %s"
        search_term = f"%{query}%"
        db_cursor.execute(sql, (search_term, search_term, search_term))
        records = db_cursor.fetchall()
        if not records:
            messagebox.showinfo("Not Found", "No medicines found matching your search.")
        populate_treeview(tree, records)
    except mysql.connector.Error as err:
        messagebox.showerror("Search Error", f"An error occurred during search: {err}")


def check_expiry_status():
    """Checks and highlights medicines that are expired or expiring soon."""
    fetch_all_medicines()  # Start with a clean slate
    today = date.today()
    thirty_days_later = today + timedelta(days=30)

    for item in tree.get_children():
        values = tree.item(item, 'values')
        exp_date_str = values[6]  # exp_date is the 7th column (index 6)
        try:
            # Handle both date objects from DB and string objects
            if isinstance(exp_date_str, str):
                exp_date_obj = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
            else:
                exp_date_obj = exp_date_str

            if exp_date_obj < today:
                tree.item(item, tags=('expired',))
            elif today <= exp_date_obj <= thirty_days_later:
                tree.item(item, tags=('expiring_soon',))
        except (ValueError, IndexError, TypeError) as e:
            print(f"Could not parse date for item: {values}. Error: {e}")
            continue

    messagebox.showinfo("Expiry Check",
                        "Expiry status has been updated.\nRed: Expired\nOrange: Expiring within 30 days")


def view_low_stock():
    """Filters the view to show only medicines with low stock."""
    try:
        threshold = 10  # Setting a default threshold
        sql = "SELECT * FROM Medicines WHERE quantity < %s"
        db_cursor.execute(sql, (threshold,))
        records = db_cursor.fetchall()
        if not records:
            messagebox.showinfo("Low Stock", f"No medicines are below the stock threshold of {threshold}.")
        populate_treeview(tree, records)
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Failed to fetch low stock items: {err}")


# --- Graphing Functionality (Corrected for Time-Series) ---
def generate_timeline_graph(selection_window, listbox, all_medicines):
    """Generates and displays a line plot of stock quantity over time."""
    selected_indices = listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Selection Error", "Please select at least one medicine to plot.",
                               parent=selection_window)
        return

    selected_med_tuples = [all_medicines[i] for i in selected_indices]

    selection_window.destroy()

    plt.figure(figsize=(12, 7))
    ax = plt.gca()  # Get current axes

    for med_id, med_name in selected_med_tuples:
        try:
            sql = "SELECT change_date, quantity FROM StockHistory WHERE medicine_id = %s ORDER BY change_date ASC"
            db_cursor.execute(sql, (med_id,))
            history = db_cursor.fetchall()

            if history:
                dates = [row[0] for row in history]
                quantities = [row[1] for row in history]
                plt.plot(dates, quantities, marker='o', linestyle='-', label=med_name)

        except mysql.connector.Error as err:
            messagebox.showerror("Graph Error", f"Could not fetch history for {med_name}: {err}")
            return

    # Formatting the plot
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gcf().autofmt_xdate()  # Auto-formats the x-axis labels to fit

    plt.ylabel('Stock Quantity')
    plt.xlabel('Date')
    plt.title('Medicine Stock Quantity Over Time')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    plt.show()


def open_timeline_graph_selection_window():
    """Opens a Toplevel window to select medicines for time-series graphing."""
    try:
        db_cursor.execute("SELECT id, name FROM Medicines")
        all_medicines = db_cursor.fetchall()
        if not all_medicines:
            messagebox.showinfo("No Data", "There are no medicines in the database to graph.")
            return
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to fetch medicines for graph: {err}")
        return

    graph_window = tk.Toplevel(root)
    graph_window.title("Select Medicines to Plot")
    graph_window.geometry("400x450")
    graph_window.configure(bg='#eaf2f8')
    graph_window.resizable(False, False)

    label = tk.Label(graph_window, text="Select medicines (use Ctrl or Shift to select multiple):",
                     font=('Segoe UI', 10), bg='#eaf2f8')
    label.pack(pady=10)

    list_frame = tk.Frame(graph_window)
    list_frame.pack(padx=10, pady=5, fill="both", expand=True)

    listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, font=('Segoe UI', 10))
    for med in all_medicines:
        listbox.insert(tk.END, med[1])  # Insert medicine name

    scrollbar = tk.Scrollbar(list_frame, orient="vertical")
    scrollbar.config(command=listbox.yview)
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)
    listbox.pack(side="left", fill="both", expand=True)

    plot_button = tk.Button(graph_window, text="Generate Graph",
                            command=lambda: generate_timeline_graph(graph_window, listbox, all_medicines),
                            font=('Segoe UI', 10, 'bold'), bg='#16a085', fg='white', relief='flat')
    plot_button.pack(pady=15)


# --- UI Window Functions ---
def open_add_window():
    """Opens a new Toplevel window for adding a medicine."""
    global add_window, name_entry, category_entry, price_entry, quantity_entry, mfg_date_entry, exp_date_entry, supplier_entry

    add_window = tk.Toplevel(root)
    add_window.title("Add New Medicine")
    add_window.geometry("400x350")
    add_window.configure(bg='#eaf2f8')
    add_window.resizable(False, False)

    frame = tk.Frame(add_window, bg='#eaf2f8')
    frame.pack(pady=20, padx=20, fill="both", expand=True)

    labels = ["Name:", "Category:", "Price (₹):", "Quantity:", "Mfg Date (YYYY-MM-DD):", "Exp Date (YYYY-MM-DD):",
              "Supplier:"]
    entries = []

    for i, text in enumerate(labels):
        label = tk.Label(frame, text=text, font=('Segoe UI', 10), bg='#eaf2f8')
        label.grid(row=i, column=0, sticky='w', pady=5)
        entry = tk.Entry(frame, font=('Segoe UI', 10), width=30)
        entry.grid(row=i, column=1, pady=5, padx=5)
        entries.append(entry)

    name_entry, category_entry, price_entry, quantity_entry, mfg_date_entry, exp_date_entry, supplier_entry = entries

    add_button = tk.Button(frame, text="Add Medicine", command=add_medicine, font=('Segoe UI', 10, 'bold'),
                           bg='#2874a6', fg='white', relief='flat')
    add_button.grid(row=len(labels), columnspan=2, pady=20)


def open_update_window():
    """Opens a Toplevel window to update the selected medicine, pre-filled with its data."""
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select a medicine to update.")
        return

    global update_window, update_name_entry, update_category_entry, update_price_entry, update_quantity_entry, update_mfg_date_entry, update_exp_date_entry, update_supplier_entry

    update_window = tk.Toplevel(root)
    update_window.title("Update Medicine Details")
    update_window.geometry("400x350")
    update_window.configure(bg='#eaf2f8')
    update_window.resizable(False, False)

    frame = tk.Frame(update_window, bg='#eaf2f8')
    frame.pack(pady=20, padx=20, fill="both", expand=True)

    labels = ["Name:", "Category:", "Price (₹):", "Quantity:", "Mfg Date (YYYY-MM-DD):", "Exp Date (YYYY-MM-DD):",
              "Supplier:"]
    entries = []

    for i, text in enumerate(labels):
        label = tk.Label(frame, text=text, font=('Segoe UI', 10), bg='#eaf2f8')
        label.grid(row=i, column=0, sticky='w', pady=5)
        entry = tk.Entry(frame, font=('Segoe UI', 10), width=30)
        entry.grid(row=i, column=1, pady=5, padx=5)
        entries.append(entry)

    update_name_entry, update_category_entry, update_price_entry, update_quantity_entry, update_mfg_date_entry, update_exp_date_entry, update_supplier_entry = entries

    # Pre-fill the form with data from the selected treeview item
    selected_values = tree.item(selected_item, 'values')
    for entry, value in zip(entries, selected_values[1:]):  # Skip ID
        entry.insert(0, value)

    update_btn = tk.Button(frame, text="Update Details", command=update_medicine, font=('Segoe UI', 10, 'bold'),
                           bg='#2874a6', fg='white', relief='flat')
    update_btn.grid(row=len(labels), columnspan=2, pady=20)


# --- Main Application Window Setup ---
root = tk.Tk()
root.title("Medicine Expiry and Stock Management System")
root.geometry("1200x600")  # Increased width for the new button
root.configure(bg='#f0f0f0')

# --- Style Configuration ---
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview",
                background="#ffffff",
                foreground="#333333",
                rowheight=25,
                fieldbackground="#ffffff",
                font=('Segoe UI', 10))
style.map('Treeview', background=[('selected', '#3498db')])
style.configure("Treeview.Heading", font=('Segoe UI', 11, 'bold'), background='#d3d3d3', relief='flat')
style.map("Treeview.Heading",
          background=[('active', '#c1c1c1')])

# --- Top Frame for Controls ---
control_frame = tk.Frame(root, bg='#d6eaf8', pady=10, padx=10)
control_frame.pack(fill='x')

# --- Search Bar ---
search_label = tk.Label(control_frame, text="Search:", font=('Segoe UI', 10), bg='#d6eaf8')
search_label.pack(side='left', padx=(0, 5))
search_entry = tk.Entry(control_frame, font=('Segoe UI', 10), width=30)
search_entry.pack(side='left', padx=5, ipady=4)
search_button = tk.Button(control_frame, text="Search", command=search_medicine, font=('Segoe UI', 9, 'bold'),
                          bg='#5dade2', fg='white', relief='flat', padx=10)
search_button.pack(side='left', padx=5)
clear_button = tk.Button(control_frame, text="View All", command=fetch_all_medicines, font=('Segoe UI', 9, 'bold'),
                         bg='#a9a9a9', fg='white', relief='flat', padx=10)
clear_button.pack(side='left', padx=5)

# --- Treeview Frame for Data Display ---
tree_frame = tk.Frame(root, bg='#f0f0f0')
tree_frame.pack(pady=10, padx=10, fill='both', expand=True)

# Scrollbars
tree_scroll_y = tk.Scrollbar(tree_frame)
tree_scroll_y.pack(side='right', fill='y')
tree_scroll_x = tk.Scrollbar(tree_frame, orient='horizontal')
tree_scroll_x.pack(side='bottom', fill='x')

# Treeview Widget
columns = ("id", "name", "category", "price", "quantity", "mfg_date", "exp_date", "supplier")
tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=tree_scroll_y.set,
                    xscrollcommand=tree_scroll_x.set)
tree_scroll_y.config(command=tree.yview)
tree_scroll_x.config(command=tree.xview)

# Define Headings
tree.heading("id", text="ID")
tree.heading("name", text="Name")
tree.heading("category", text="Category")
tree.heading("price", text="Price (₹)")
tree.heading("quantity", text="Quantity")
tree.heading("mfg_date", text="Mfg Date")
tree.heading("exp_date", text="Exp Date")
tree.heading("supplier", text="Supplier")

# Define Column widths
tree.column("id", width=40, anchor='center')
tree.column("name", width=200)
tree.column("category", width=120)
tree.column("price", width=80, anchor='center')
tree.column("quantity", width=80, anchor='center')
tree.column("mfg_date", width=100, anchor='center')
tree.column("exp_date", width=100, anchor='center')
tree.column("supplier", width=150)

tree.pack(fill='both', expand=True)

# Add tags for coloring rows
tree.tag_configure('expired', background='#ffdddd', foreground='red')
tree.tag_configure('expiring_soon', background='#fff8dc', foreground='#e67e22')

# --- Bottom Frame for Action Buttons ---
action_frame = tk.Frame(root, bg='#f0f0f0', pady=10)
action_frame.pack(fill='x', padx=10)

button_font = ('Segoe UI', 10, 'bold')
btn_style = {'fg': 'white', 'relief': 'flat', 'padx': 15, 'pady': 5, 'width': 18}  # Adjusted width

add_btn = tk.Button(action_frame, text="Add Medicine", command=open_add_window, font=button_font, bg='#27ae60',
                    **btn_style)
update_btn = tk.Button(action_frame, text="Update Selected", command=open_update_window, font=button_font, bg='#2980b9',
                       **btn_style)
delete_btn = tk.Button(action_frame, text="Delete Selected", command=delete_medicine, font=button_font, bg='#c0392b',
                       **btn_style)
expiry_btn = tk.Button(action_frame, text="Check Expiry", command=check_expiry_status, font=button_font, bg='#f39c12',
                       **btn_style)
low_stock_btn = tk.Button(action_frame, text="View Low Stock", command=view_low_stock, font=button_font, bg='#8e44ad',
                          **btn_style)
graph_btn = tk.Button(action_frame, text="View Graph", command=open_timeline_graph_selection_window, font=button_font,
                      bg='#16a085', **btn_style)

# Pack buttons with space in between
action_frame.pack_propagate(False)
action_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
add_btn.grid(row=0, column=0, padx=5)
update_btn.grid(row=0, column=1, padx=5)
delete_btn.grid(row=0, column=2, padx=5)
expiry_btn.grid(row=0, column=3, padx=5)
low_stock_btn.grid(row=0, column=4, padx=5)
graph_btn.grid(row=0, column=5, padx=5)

# --- Start Application ---
# It's better to connect to DB after setting up the main window.
root.after(100, connect_to_database)  # Delay connection slightly
root.after(200, fetch_all_medicines)  # Populate tree after connection
root.mainloop()

# Close database connection when the application is closed
if db_connection and db_connection.is_connected():
    db_cursor.close()
    db_connection.close()
    print("Database connection closed.")

