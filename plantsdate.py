import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry  # Импортируем виджет календаря

# Автоустановка зависимостей
def install_dependencies():
    try:
        import sqlite3
        import tkinter
        from tkcalendar import DateEntry
    except ImportError:
        print("Устанавливаю зависимости...")
        os.system(f"{sys.executable} -m pip install requests beautifulsoup4 tkcalendar")
        print("Зависимости установлены, перезапустите скрипт.")
        sys.exit()

install_dependencies()

# Создание базы данных
def setup_database():
    conn = sqlite3.connect("plants.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        seedling_days INTEGER,
        vegetation_days INTEGER,
        flowering_days INTEGER,
        fruiting_days INTEGER
    )
    """)

    conn.commit()
    conn.close()

# Функция расчёта дат
def calculate_growth_stages():
    for row in tree.get_children():
        values = tree.item(row, "values")
        plant_name = values[0]
        planting_date_str = values[1]

        if not planting_date_str:
            continue

        try:
            planting_date = datetime.strptime(planting_date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", f"Неверный формат даты для {plant_name} (должно быть YYYY-MM-DD)")
            return

        conn = sqlite3.connect("plants.db")
        cursor = conn.cursor()
        cursor.execute("SELECT seedling_days, vegetation_days, flowering_days, fruiting_days FROM plants WHERE name = ?", (plant_name,))
        plant_data = cursor.fetchone()
        conn.close()

        if not plant_data:
            continue

        seedling_days, vegetation_days, flowering_days, fruiting_days = plant_data

        seedling_date = planting_date + timedelta(days=seedling_days)
        vegetation_date = seedling_date + timedelta(days=vegetation_days)
        flowering_date = vegetation_date + timedelta(days=flowering_days)
        fruiting_date = flowering_date + timedelta(days=fruiting_days)

        tree.item(row, values=(plant_name, planting_date_str,
                               seedling_date.strftime("%Y-%m-%d"),
                               vegetation_date.strftime("%Y-%m-%d"),
                               flowering_date.strftime("%Y-%m-%d"),
                               fruiting_date.strftime("%Y-%m-%d")))

# Добавление нового растения вручную
def add_new_plant():
    def save_new_plant():
        plant_name = entry_name.get()
        seedling_days = entry_seedling.get()
        vegetation_days = entry_vegetation.get()
        flowering_days = entry_flowering.get()
        fruiting_days = entry_fruiting.get()

        if not plant_name or not seedling_days or not vegetation_days or not flowering_days or not fruiting_days:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return

        try:
            seedling_days = int(seedling_days)
            vegetation_days = int(vegetation_days)
            flowering_days = int(flowering_days)
            fruiting_days = int(fruiting_days)
        except ValueError:
            messagebox.showerror("Ошибка", "Все сроки должны быть числами")
            return

        conn = sqlite3.connect("plants.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO plants (name, seedling_days, vegetation_days, flowering_days, fruiting_days) VALUES (?, ?, ?, ?, ?)",
                       (plant_name, seedling_days, vegetation_days, flowering_days, fruiting_days))
        conn.commit()
        conn.close()

        load_plant_list()
        add_window.destroy()
        messagebox.showinfo("Успех", f"{plant_name} добавлен в базу")

    add_window = tk.Toplevel(root)
    add_window.title("Добавить новое растение")
    add_window.geometry("300x250")

    tk.Label(add_window, text="Название растения:").pack()
    entry_name = tk.Entry(add_window)
    entry_name.pack()

    tk.Label(add_window, text="Дни до рассады:").pack()
    entry_seedling = tk.Entry(add_window)
    entry_seedling.pack()

    tk.Label(add_window, text="Дни до вегетации:").pack()
    entry_vegetation = tk.Entry(add_window)
    entry_vegetation.pack()

    tk.Label(add_window, text="Дни до цветения:").pack()
    entry_flowering = tk.Entry(add_window)
    entry_flowering.pack()

    tk.Label(add_window, text="Дни до плодоношения:").pack()
    entry_fruiting = tk.Entry(add_window)
    entry_fruiting.pack()

    tk.Button(add_window, text="Сохранить", command=save_new_plant).pack()

# Загрузка списка растений
def load_plant_list():
    conn = sqlite3.connect("plants.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM plants")
    plants = [row[0] for row in cursor.fetchall()]
    conn.close()

    for row in tree.get_children():
        tree.delete(row)

    for plant in plants:
        tree.insert("", "end", values=(plant, "Введите дату", "", "", "", ""))

# Функция для выбора даты
def select_planting_date(row):
    def on_date_select():
        selected_date = cal.get_date()
        tree.item(row, values=(tree.item(row, "values")[0], selected_date, "", "", "", ""))
        date_window.destroy()

    date_window = tk.Toplevel(root)
    date_window.title("Выберите дату посадки")
    cal = DateEntry(date_window, date_pattern="y-mm-dd")
    cal.pack(padx=10, pady=10)
    tk.Button(date_window, text="Выбрать", command=on_date_select).pack()

# Интерфейс
setup_database()
root = tk.Tk()
root.title("Калькулятор роста растений")
root.geometry("800x400")

# Таблица
tree = ttk.Treeview(root, columns=("name", "planting_date", "seedling", "vegetation", "flowering", "fruiting"), show="headings")
tree.heading("name", text="Растение")
tree.heading("planting_date", text="Дата посадки")
tree.heading("seedling", text="Дата рассады")
tree.heading("vegetation", text="Дата вегетации")
tree.heading("flowering", text="Дата цветения")
tree.heading("fruiting", text="Дата плодоношения")
tree.pack(fill="both", expand=True)

# Добавляем кнопку для выбора даты
tree.bind("<Double-1>", lambda event: select_planting_date(tree.identify_row(event.y)))

# Кнопка расчёта
btn_calculate = tk.Button(root, text="Рассчитать даты", command=calculate_growth_stages)
btn_calculate.pack()

# Кнопка добавления нового растения
btn_add_plant = tk.Button(root, text="Добавить растение", command=add_new_plant)
btn_add_plant.pack()

# Загрузка данных в таблицу
load_plant_list()

root.mainloop()
