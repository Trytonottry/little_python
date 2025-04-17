# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os

class CallLogParser:
    def __init__(self, root):
        self.root = root
        self.root.title("Парсер истории звонков")
        self.root.geometry("400x300")

        self.exclude_list = set()

        self.label = tk.Label(root, text="Выберите файл с исключениями (txt):")
        self.label.pack(pady=10)

        self.browse_button = tk.Button(root, text="Обзор", command=self.load_exclude_list)
        self.browse_button.pack(pady=10)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=20)

        self.start_button = tk.Button(root, text="Начать парсинг", command=self.start_parsing)
        self.start_button.pack(pady=10)

    def load_exclude_list(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.exclude_list = set(line.strip() for line in file)
            messagebox.showinfo("Успех", "Список исключений загружен!")

    def start_parsing(self):
        self.progress['value'] = 0
        self.root.update_idletasks()

        # Получаем историю звонков через adb
        try:
            call_log = subprocess.check_output(["adb", "shell", "content", "query", "--uri", "content://call_log/calls"]).decode('utf-8')
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Ошибка", "Не удалось получить историю звонков. Убедитесь, что устройство подключено и отладка по USB включена.")
            return

        numbers = set()
        for line in call_log.splitlines():
            if "number" in line:
                number = line.split("number=")[1].split(",")[0]
                if number not in self.exclude_list:
                    numbers.add(number)

        self.progress['value'] = 50
        self.root.update_idletasks()

        # Сохраняем номера в файл
        with open("parsed_numbers.txt", "w", encoding='utf-8') as file:
            for number in numbers:
                file.write(f"{number} - мусор1\n")

        self.progress['value'] = 100
        self.root.update_idletasks()
        messagebox.showinfo("Успех", "Парсинг завершен! Номера сохранены в parsed_numbers.txt")

if __name__ == "__main__":
    root = tk.Tk()
    app = CallLogParser(root)
    root.mainloop()