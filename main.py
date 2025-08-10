import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict
import time

# Конфигурационные переменные
DEFAULT_DIR = str(Path.home())  # Домашняя директория по умолчанию
DEFAULT_DEPTH = 3  # Глубина отображения по умолчанию
DEFAULT_MIN_SIZE = 300 * 1024 * 1024  # 300MB в байтах
REPORT_FILE = 'report.txt'  # Имя файла отчета
DEFAULT_TOP_FILES = 10  # Количество топ файлов по умолчанию
DEFAULT_TOP_DIRS = 10  # Количество топ директорий по умолчанию


class ProgressIndicator:
    """Класс для отображения прогресса в консоли"""

    def __init__(self, silent=False):
        self.silent = silent
        self.spinner = ['-', '\\', '|', '/']
        self.spinner_pos = 0

    def spin(self):
        if self.silent:
            return
        self.spinner_pos = (self.spinner_pos + 1) % 4
        sys.stdout.write(f"\rАнализирую {self.spinner[self.spinner_pos]}")
        sys.stdout.flush()

    def clear(self):
        if not self.silent:
            sys.stdout.write("\r")
            sys.stdout.flush()


def get_size(start_path='.'):
    """Рекурсивно вычисляет размер директории, количество поддиректорий и файлов"""
    total_size = 0
    dir_count = 0
    file_count = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        dir_count += len(dirnames)
        file_count += len(filenames)
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except (OSError, PermissionError):
                continue
    return total_size, dir_count, file_count


def format_size(size):
    """Форматирует размер в удобочитаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def find_large_items(path, min_size=0, top_files=10, top_dirs=10, progress=None):
    """Находит самые большие файлы и директории"""
    large_files = []
    large_dirs = []

    for dirpath, dirnames, filenames in os.walk(path):
        if progress:
            progress.spin()

        # Проверяем файлы
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                size = os.path.getsize(filepath)
                if size >= min_size:
                    large_files.append((filepath, size))
            except (OSError, PermissionError):
                continue

        # Проверяем директории
        try:
            dir_size, _, _ = get_size(dirpath)
            large_dirs.append((dirpath, dir_size))
        except (PermissionError, OSError):
            continue

    # Сортируем и выбираем топ
    large_files.sort(key=lambda x: x[1], reverse=True)
    large_dirs.sort(key=lambda x: x[1], reverse=True)

    return large_files[:top_files], large_dirs[:top_dirs]


def analyze_directory(path, max_depth=3, current_depth=0, min_size=DEFAULT_MIN_SIZE):
    """Рекурсивно анализирует директорию и возвращает структуру"""
    if current_depth > max_depth:
        return None

    try:
        total_size, dir_count, file_count = get_size(path)
    except (PermissionError, OSError):
        return None

    name = os.path.basename(path) if current_depth > 0 else path
    result = {
        'name': name,
        'size': total_size,
        'dir_count': dir_count,
        'file_count': file_count,
        'is_file': False,
        'children': []  # Всегда инициализируем пустой список children
    }

    if current_depth < max_depth:
        try:
            entries = os.listdir(path)
        except (PermissionError, OSError):
            entries = []

        dirs = []
        files = []
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                dirs.append((entry, full_path))
            else:
                try:
                    size = os.path.getsize(full_path)
                    if size >= min_size:
                        ext = os.path.splitext(entry)[1][1:].lower()
                        files.append((entry, size, ext))
                except (OSError, PermissionError):
                    continue

        # Сортируем директории по размеру (убывание)
        dirs_sizes = []
        for name, full_path in dirs:
            try:
                size, _, _ = get_size(full_path)
                dirs_sizes.append((name, full_path, size))
            except (PermissionError, OSError):
                continue

        dirs_sizes.sort(key=lambda x: x[2], reverse=True)

        # Добавляем только первые 5 самых больших директорий
        for name, full_path, size in dirs_sizes[:5]:
            child = analyze_directory(full_path, max_depth, current_depth + 1, min_size)
            if child:
                result['children'].append(child)

        # Сортируем файлы по размеру (убывание) и добавляем первые 5 самых больших
        files.sort(key=lambda x: x[1], reverse=True)
        for name, size, ext in files[:5]:
            result['children'].append({
                'name': name,
                'size': size,
                'is_file': True,
                'extension': ext
            })

    return result


def generate_report(structure, large_files, large_dirs, file=None):
    """Генерирует полный отчет"""
    # Древовидная структура
    generate_tree_report(structure, file=file)

    # Топ файлов
    print("\n\nТоп 10 самых больших файлов:", file=file)
    for i, (path, size) in enumerate(large_files, 1):
        print(f"{i}. {path} - {format_size(size)}", file=file)

    # Топ директорий
    print("\nТоп 10 самых больших директорий:", file=file)
    for i, (path, size) in enumerate(large_dirs, 1):
        print(f"{i}. {path} - {format_size(size)}", file=file)


def generate_tree_report(structure, level=0, is_last=False, file=None):
    """Генерирует древовидную часть отчета с правильными символами ветвления"""
    if structure is None:
        return

    # Получаем список детей или пустой список, если ключа нет
    children = structure.get('children', [])

    # Определяем отступы и символы соединения
    indent = '    ' * (level - 1) if level > 0 else ''
    connector = '└── ' if is_last else '├── '

    if level == 0:
        # Корневая директория
        line = f"{structure['name']}/\t# {format_size(structure['size'])}, {structure['dir_count']} dir, {structure['file_count']} files"
    else:
        if structure.get('is_file', False):
            # Это файл
            ext = structure.get('extension', 'file')
            line = f"{indent}{connector}{structure['name']}\t# {format_size(structure['size'])} - {ext} file"
        else:
            # Это директория
            line = f"{indent}{connector}{structure['name']}/\t# {format_size(structure['size'])}, {structure['dir_count']} dir, {structure['file_count']} files"

    print(line, file=file)

    # Рекурсивно обрабатываем детей
    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        new_indent = '    ' * level if level > 0 else ''
        generate_tree_report(child, level + 1, is_last_child, file)

def parse_size(size_str):
    """Парсит строку с размером (например, '300M', '1G') в байты"""
    size_str = size_str.upper()
    if 'K' in size_str:
        return int(float(size_str.replace('K', '')) * 1024)
    elif 'M' in size_str:
        return int(float(size_str.replace('M', '')) * 1024 * 1024)
    elif 'G' in size_str:
        return int(float(size_str.replace('G', '')) * 1024 * 1024 * 1024)
    elif 'T' in size_str:
        return int(float(size_str.replace('T', '')) * 1024 * 1024 * 1024 * 1024)
    else:
        return int(size_str)  # Байты по умолчанию


def print_large_items(large_files, large_dirs, top_files, top_dirs):
    """Выводит топ файлов и директорий в консоль"""
    print("\nТоп самых больших файлов:")
    for i, (path, size) in enumerate(large_files[:top_files], 1):
        print(f"{i}. {path} - {format_size(size)}")

    print("\nТоп самых больших директорий:")
    for i, (path, size) in enumerate(large_dirs[:top_dirs], 1):
        print(f"{i}. {path} - {format_size(size)}")


def main():
    parser = argparse.ArgumentParser(description='Анализирует размеры директорий и создает отчет')
    parser.add_argument('directory', nargs='?', default=DEFAULT_DIR,
                        help=f'Директория для анализа (по умолчанию: {DEFAULT_DIR})')
    parser.add_argument('--depth', type=int, default=DEFAULT_DEPTH,
                        help=f'Глубина отображения дерева (по умолчанию: {DEFAULT_DEPTH})')
    parser.add_argument('-m', '--min-size', type=str, default='300M',
                        help='Минимальный размер файлов для отображения (например, 300M, 1G) (по умолчанию: 300M)')
    parser.add_argument('-f', '--files', type=int, default=DEFAULT_TOP_FILES,
                        help=f'Количество топ файлов для отображения (по умолчанию: {DEFAULT_TOP_FILES})')
    parser.add_argument('--dirs', type=int, default=DEFAULT_TOP_DIRS,
                        help=f'Количество топ директорий для отображения (по умолчанию: {DEFAULT_TOP_DIRS})')
    parser.add_argument('-s', '--silent', action='store_true',
                        help='Тихий режим (не выводить прогресс и результаты в консоль)')

    args = parser.parse_args()

    target_dir = args.directory
    depth = args.depth
    silent = args.silent
    top_files = args.files
    top_dirs = args.dirs

    # Парсим минимальный размер
    try:
        min_size = parse_size(args.min_size)
    except ValueError:
        print("Ошибка: неверный формат минимального размера. Используйте например '300M' или '1G'", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(target_dir):
        print(f"Ошибка: '{target_dir}' не является директорией или не существует", file=sys.stderr)
        sys.exit(1)

    progress = ProgressIndicator(silent)

    if not silent:
        print(f"Анализирую директорию: {target_dir}")
        print(f"Глубина анализа: {depth}, мин. размер файлов: {format_size(min_size)}")
        print(f"Количество топ файлов: {top_files}, топ директорий: {top_dirs}")

    # Находим самые большие файлы и директории
    large_files, large_dirs = find_large_items(target_dir, min_size, top_files, top_dirs, progress)
    progress.clear()

    # Анализируем структуру директории
    structure = analyze_directory(target_dir, depth, min_size=min_size)

    # Генерируем отчет
    report_path = os.path.join(os.getcwd(), REPORT_FILE)
    with open(report_path, 'w', encoding='utf-8') as f:
        generate_report(structure, large_files, large_dirs, file=f)

    if not silent:
        # Выводим топ файлов и директорий в консоль
        print_large_items(large_files, large_dirs, top_files, top_dirs)
        print(f"\nОтчет сохранен в: {report_path}")


if __name__ == '__main__':
    main()