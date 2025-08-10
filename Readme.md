# Disk Space Analyzer

A Python script to analyze disk space usage and generate detailed reports.

## Features

- Recursive directory analysis
- Human-readable size formatting
- Tree structure visualization
- Top largest files/directories listing
- Customizable depth and size thresholds
- Cross-platform support (Windows/Linux/macOS)

## Installation

1. Ensure you have Python 3.6+ installed
2. Clone this repository or download the script

## Usage

```bash
python main.py [DIRECTORY] [OPTIONS]
```

### Basic Options

| Option          | Description                                  | Default          |
|-----------------|----------------------------------------------|------------------|
| (no argument)   | Analyze home directory                      | Home directory   |
| `-d`, `--depth` | Tree display depth                          | 3                |
| `-m`, `--min-size` | Minimum file size (e.g. 300M, 1G)       | 300M             |
| `-f`, `--files` | Number of top files to show                 | 10               |
| `--dirs`        | Number of top directories to show           | 10               |
| `-s`, `--silent`| Silent mode (no console output)             | Off              |

### Examples

1. Analyze current directory with default settings:
   ```bash
   python main.py .
   ```

2. Analyze specific directory with depth 5:
   ```bash
   python main.py /path/to/dir --depth 5
   ```

3. Analyze with 1GB minimum file size:
   ```bash
   python main.py /path/to/dir -m 1G
   ```

4. Silent mode (report only):
   ```bash
   python main.py /path/to/dir -s
   ```

## Report Format

The script generates `report.txt` containing:
1. Tree structure of directories
2. List of largest files
3. List of largest directories

Example report:
```
/home/user/                          # 288 GB, 210 dir, 310443 files
├── Downloads/                  # 28 GB, 20 dir, 10423 files
│   └── backup.tar.gz           # 10.2 GB - gz file
└── Photos/
     ├── Vacation/              # 20 GB, 50 dir, 1000 files
     └── family.jpg             # 2GB - jpg file

Top 10 largest files:
1. /home/user/Downloads/backup.tar.gz - 10.2 GB
...

Top 10 largest directories:
1. /home/user/Downloads - 28 GB
...
```

## Configuration

You can modify default values in the script:
```python
DEFAULT_DIR = str(Path.home())    # Default directory
DEFAULT_DEPTH = 3                 # Default depth
DEFAULT_MIN_SIZE = 300 * 1024 * 1024  # 300MB minimum size
DEFAULT_TOP_FILES = 10            # Default top files count
DEFAULT_TOP_DIRS = 10             # Default top directories count
REPORT_FILE = 'report.txt'        # Report filename
```

## Limitations

- Doesn't follow symbolic links
- May skip system directories due to permission issues
- Unicode characters in filenames are supported but may affect alignment

## 🌍 Available Translations | Доступные переводы | 可用翻译
- 🇬🇧 [English](Readme.md) - English version  
- 🇷🇺 [Русский](Readme_ru.md) - Russian version  
- 🇨🇳 [中文](Readme_ch.md) - Chinese version

## License

This project is open-source and available under the MIT License.

