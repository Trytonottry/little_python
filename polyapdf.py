import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

def get_page_margins(pdf_path):
    try:
        # Открываем PDF-документ
        doc = fitz.open(pdf_path)
        results = []

        # Перебираем все страницы
        for page_number in range(len(doc)):
            page = doc.load_page(page_number)  # Загружаем страницу

            # Получаем размеры страницы в пунктах (1 пункт = 1/72 дюйма)
            rect = page.rect
            width_pt = rect.width
            height_pt = rect.height

            # Конвертируем размеры страницы в миллиметры
            mm_per_inch = 25.4
            width_mm = (width_pt / 72) * mm_per_inch
            height_mm = (height_pt / 72) * mm_per_inch

            # Получаем все элементы страницы (текст, изображения, формы и т.д.)
            elements = page.get_text("blocks")  # Используем "blocks" для получения всех элементов

            if not elements:
                results.append(f"Страница {page_number + 1}: Нет элементов.\n")
                continue

            # Инициализируем минимальные и максимальные координаты
            x0_min, y0_min = float('inf'), float('inf')
            x1_max, y1_max = 0, 0

            # Перебираем все элементы и находим границы
            for element in elements:
                x0, y0, x1, y1 = element[:4]  # Координаты блока
                x0_min = min(x0_min, x0)
                y0_min = min(y0_min, y0)
                x1_max = max(x1_max, x1)
                y1_max = max(y1_max, y1)

            # Вычисляем поля в пунктах
            left_margin_pt = x0_min
            right_margin_pt = width_pt - x1_max
            top_margin_pt = y0_min
            bottom_margin_pt = height_pt - y1_max

            # Конвертируем поля в миллиметры
            left_margin_mm = (left_margin_pt / 72) * mm_per_inch
            right_margin_mm = (right_margin_pt / 72) * mm_per_inch
            top_margin_mm = (top_margin_pt / 72) * mm_per_inch
            bottom_margin_mm = (bottom_margin_pt / 72) * mm_per_inch

            # Формируем результат для текущей страницы
            result = (
                f"Страница {page_number + 1}:\n"
                f"  Размеры страницы: {width_mm:.2f} мм x {height_mm:.2f} мм\n"
                f"  Левое поле: {left_margin_mm:.2f} мм\n"
                f"  Правое поле: {right_margin_mm:.2f} мм\n"
                f"  Верхнее поле: {top_margin_mm:.2f} мм\n"
                f"  Нижнее поле: {bottom_margin_mm:.2f} мм\n"
            )
            results.append(result)

        # Возвращаем результаты для всех страниц
        return "\n".join(results)

    except Exception as e:
        return f"Произошла ошибка: {str(e)}"

def select_pdf():
    # Открываем диалог выбора файла
    file_path = filedialog.askopenfilename(
        title="Выберите PDF-документ",
        filetypes=[("PDF Files", "*.pdf")]
    )
    if file_path:
        # Анализируем документ
        result = get_page_margins(file_path)
        # Выводим результат в текстовое поле
        result_text.delete(1.0, tk.END)  # Очищаем поле
        result_text.insert(tk.END, result)  # Вставляем результат
        # Сохраняем результат в файл
        with open("margins_results.txt", "w", encoding="utf-8") as file:
            file.write(result)
        messagebox.showinfo("Готово", "Результаты сохранены в margins_results.txt")

# Создаем графический интерфейс
root = tk.Tk()
root.title("Анализатор полей PDF")
root.geometry("600x400")

# Кнопка для выбора PDF
select_button = tk.Button(root, text="Выбрать PDF", command=select_pdf)
select_button.pack(pady=10)

# Текстовое поле с прокруткой для вывода результатов
result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=20)
result_text.pack(padx=10, pady=10)

# Запуск основного цикла
root.mainloop()
