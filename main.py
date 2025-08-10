import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict

# Конфигурационные переменные
DEFAULT_DIR = str(Path.home())  # Домашняя директория по умолчанию
DEFAULT_DEPTH = 3  # Глубина отображения по умолчанию
REPORT_FILE = 'report.txt'  # Имя файла отчета (в директории запуска)


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


def analyze_directory(path, max_depth=3, current_depth=0):
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
        'children': []
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
                    files.append((entry, size, os.path.splitext(entry)[1][1:].lower()))
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
            child = analyze_directory(full_path, max_depth, current_depth + 1)
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


def generate_report(structure, level=0, file=None):
    """Генерирует отчет в текстовом виде с древовидной структурой"""
    if structure is None:
        return

    indent = '    ' * level
    connector = '├── ' if level > 0 else ''

    if structure['is_file']:
        ext = structure.get('extension', 'file')
        line = f"{indent}{connector}{structure['name']}\t# {format_size(structure['size'])} - {ext} file"
    else:
        line = f"{indent}{connector}{structure['name']}/\t# {format_size(structure['size'])}, {structure['dir_count']} dir, {structure['file_count']} files"

    print(line, file=file)

    for i, child in enumerate(structure['children']):
        if i == len(structure['children']) - 1 and level > 0:
            structure['children'][i]['name'] = '└── ' + structure['children'][i]['name']
        generate_report(child, level + 1, file)


def main():
    parser = argparse.ArgumentParser(description='Анализирует размеры директорий и создает отчет')
    parser.add_argument('directory', nargs='?', default=DEFAULT_DIR,
                        help=f'Директория для анализа (по умолчанию: {DEFAULT_DIR})')
    parser.add_argument('-d', '--depth', type=int, default=DEFAULT_DEPTH,
                        help=f'Глубина отображения (по умолчанию: {DEFAULT_DEPTH})')

    args = parser.parse_args()

    target_dir = args.directory
    depth = args.depth

    if not os.path.isdir(target_dir):
        print(f"Ошибка: '{target_dir}' не является директорией или не существует", file=sys.stderr)
        sys.exit(1)

    print(f"Анализирую директорию: {target_dir} (глубина: {depth})...")
    structure = analyze_directory(target_dir, depth)

    report_path = os.path.join(os.getcwd(), REPORT_FILE)
    with open(report_path, 'w', encoding='utf-8') as f:
        generate_report(structure, file=f)

    print(f"Отчет сохранен в: {report_path}")


if __name__ == '__main__':
    main()