import os
import shutil
import json
import logging
from datetime import datetime
import requests
import subprocess
import sys
import re

# Настройка кодировки для логирования и файловых операций
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("organize_projects.log", encoding='utf-8'),  # Логи записываются в файл с кодировкой UTF-8
        logging.StreamHandler(),  # Логи выводятся в консоль
    ],
)

# Конфигурационный файл
CONFIG_FILE = "config.json"

# GitHub API
GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = "ваш_токен_github"  # Замените на ваш GitHub токен
GITHUB_USERNAME = "ваш_username_github"  # Замените на ваш GitHub username

# Список необходимых библиотек
REQUIRED_LIBRARIES = ["requests"]

def sanitize_project_name(project_name):
    """
    Очищает имя проекта от недопустимых символов для создания репозитория на GitHub.
    Заменяет пробелы и специальные символы на дефисы.
    """
    # Удаляем все символы, кроме букв, цифр, дефисов и подчеркиваний
    sanitized_name = re.sub(r'[^a-zA-Z0-9-_]', '-', project_name)
    # Убираем множественные дефисы
    sanitized_name = re.sub(r'-+', '-', sanitized_name)
    # Убираем дефисы в начале и конце
    sanitized_name = sanitized_name.strip('-')
    return sanitized_name

def install_dependencies():
    """
    Проверяет и устанавливает необходимые библиотеки, если они отсутствуют.
    """
    for library in REQUIRED_LIBRARIES:
        try:
            __import__(library)
            logging.info(f"Библиотека {library} уже установлена.")
        except ImportError:
            logging.warning(f"Библиотека {library} не найдена. Устанавливаем...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", library])
                logging.info(f"Библиотека {library} успешно установлена.")
            except subprocess.CalledProcessError as e:
                logging.error(f"Ошибка при установке библиотеки {library}: {e}")
                sys.exit(1)

def load_config():
    """
    Загружает конфигурацию из файла config.json.
    Если файл отсутствует, возвращает пустой словарь.
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    return {"projects": {}}

def save_config(config):
    """
    Сохраняет конфигурацию в файл config.json.
    """
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def create_project_structure(base_path, project_name):
    """
    Создает структуру директорий для проекта:
    - scripts/ для скриптов
    - data/ для данных
    - README.md с описанием проекта
    """
    try:
        os.makedirs(os.path.join(base_path, project_name, "scripts"), exist_ok=True)
        os.makedirs(os.path.join(base_path, project_name, "data"), exist_ok=True)
        with open(os.path.join(base_path, project_name, "README.md"), "w", encoding='utf-8') as readme:
            readme.write(f"# {project_name}\n\nОписание проекта.")
        logging.info(f"Структура проекта {project_name} создана.")
    except Exception as e:
        logging.error(f"Ошибка при создании структуры проекта: {e}")

def backup_file(file_path, backup_dir):
    """
    Создает резервную копию файла в папке Backup.
    """
    try:
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        shutil.copy2(file_path, backup_dir)
        logging.info(f"Резервная копия файла {os.path.basename(file_path)} создана в {backup_dir}.")
    except Exception as e:
        logging.error(f"Ошибка при создании резервной копии файла {file_path}: {e}")

def check_github_repo_exists(repo_name):
    """
    Проверяет, существует ли репозиторий на GitHub.
    Возвращает True, если репозиторий существует, иначе False.
    """
    url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}".encode('ascii').decode('latin-1'),
        "Accept": "application/vnd.github.v3+json",
    }
    try:
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при проверке репозитория на GitHub: {e}")
        return False

def create_github_repo(repo_name):
    """
    Создает новый репозиторий на GitHub.
    Возвращает True, если репозиторий успешно создан, иначе False.
    """
    url = f"{GITHUB_API_URL}/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}".encode('ascii').decode('latin-1'),
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "name": repo_name,
        "private": False,  # Можете изменить на True, если нужен приватный репозиторий
        "auto_init": False,
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            logging.info(f"Репозиторий {repo_name} создан на GitHub.")
            return True
        else:
            logging.error(f"Ошибка при создании репозитория: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при создании репозитория: {e}")
        return False

def init_git_repo(project_path, repo_name):
    """
    Инициализирует Git в локальной папке проекта и привязывает её к удаленному репозиторию на GitHub.
    """
    try:
        # Переходим в папку проекта
        os.chdir(project_path)
        
        # Инициализация Git
        os.system("git init")
        os.system("git add .")
        os.system('git commit -m "Initial commit"')
        
        # Привязка к удаленному репозиторию
        os.system(f"git remote add origin https://github.com/{GITHUB_USERNAME}/{repo_name}.git")
        os.system("git branch -M main")
        os.system("git push -u origin main")
        
        logging.info(f"Git репозиторий для проекта {repo_name} инициализирован и привязан к GitHub.")
    except Exception as e:
        logging.error(f"Ошибка при инициализации Git: {e}")

def organize_scripts(base_path, config):
    """
    Организует файлы в папке base_path:
    - Создает структуру для каждого проекта.
    - Перемещает файлы в соответствующие папки (scripts или data).
    - Создает резервные копии файлов.
    - Проверяет и создает репозитории на GitHub.
    """
    backup_dir = os.path.join(base_path, "Backup")
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        
        # Пропускаем директории (уже организованные проекты и папку Backup)
        if os.path.isdir(item_path) or item == "Backup":
            continue
        
        # Определяем имя проекта (например, по имени файла)
        project_name = os.path.splitext(item)[0]
        project_path = os.path.join(base_path, project_name)
        
        # Очищаем имя проекта для GitHub
        sanitized_project_name = sanitize_project_name(project_name)
        
        # Создаем структуру проекта, если она еще не существует
        if project_name not in config["projects"]:
            create_project_structure(base_path, project_name)
            config["projects"][project_name] = {
                "created_at": datetime.now().isoformat(),
                "files": [],
            }
        
        # Создаем резервную копию файла
        backup_file(item_path, backup_dir)
        
        # Определяем тип файла и перемещаем его в соответствующую директорию
        try:
            if item.endswith((".py", ".sh")):
                shutil.move(item_path, os.path.join(project_path, "scripts", item))
                config["projects"][project_name]["files"].append({"name": item, "type": "script", "moved_at": datetime.now().isoformat()})
                logging.info(f"Файл {item} перемещен в папку scripts проекта {project_name}.")
            elif item.endswith((".csv", ".json", ".xlsx", ".db")):
                shutil.move(item_path, os.path.join(project_path, "data", item))
                config["projects"][project_name]["files"].append({"name": item, "type": "data", "moved_at": datetime.now().isoformat()})
                logging.info(f"Файл {item} перемещен в папку data проекта {project_name}.")
            else:
                logging.warning(f"Файл {item} не был перемещен, так как его тип не определен.")
        except Exception as e:
            logging.error(f"Ошибка при перемещении файла {item}: {e}")
        
        # Проверяем и создаем репозиторий на GitHub
        if not check_github_repo_exists(sanitized_project_name):
            if create_github_repo(sanitized_project_name):
                init_git_repo(project_path, sanitized_project_name)
        else:
            logging.info(f"Репозиторий {sanitized_project_name} уже существует на GitHub.")

def main():
    """
    Основная функция скрипта.
    """
    # Устанавливаем зависимости при первом запуске
    install_dependencies()
    
    # Укажите путь к папке с вашими скриптами и проектами
    scripts_folder = input("Введите путь к папке с вашими скриптами и проектами: ")
    
    if not os.path.exists(scripts_folder):
        print(f"Папка {scripts_folder} не существует.")
        return
    
    # Загружаем конфигурацию
    config = load_config()
    
    # Организуем файлы в папке
    organize_scripts(scripts_folder, config)
    
    # Сохраняем обновленную конфигурацию
    save_config(config)
    print("Организация проектов завершена.")

if __name__ == "__main__":
    main()