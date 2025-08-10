# 磁盘空间分析工具  

一个用于分析磁盘空间使用情况并生成详细报告的Python脚本。  

## 功能  

- 递归目录分析  
- 人类可读的文件大小格式化  
- 树状结构可视化  
- 列出最大的文件/目录  
- 可自定义深度和大小阈值  
- 跨平台支持（Windows/Linux/macOS）  

## 安装  

1. 确保已安装 Python 3.6 或更高版本  
2. 克隆本仓库或直接下载脚本  

## 使用方法  

```bash  
python main.py [目录] [选项]  
```  

### 基本选项  

| 选项             | 描述                                   | 默认值          |  
|------------------|----------------------------------------|----------------|  
| (无参数)         | 分析用户主目录                        | 用户主目录      |  
| `-d`, `--depth`  | 树状结构显示深度                      | 3              |  
| `-m`, `--min-size` | 最小文件大小（例如 300M, 1G）       | 300M           |  
| `-f`, `--files`  | 显示最大的文件数量                    | 10             |  
| `--dirs`         | 显示最大的目录数量                    | 10             |  
| `-s`, `--silent` | 静默模式（不输出到控制台）            | 关闭            |  

### 示例  

1. 使用默认设置分析当前目录：  
   ```bash  
   python main.py .  
   ```  

2. 分析指定目录，深度为5：  
   ```bash  
   python main.py /路径/到/目录 --depth 5  
   ```  

3. 分析时设置最小文件大小为1GB：  
   ```bash  
   python main.py /路径/到/目录 -m 1G  
   ```  

4. 静默模式（仅生成报告）：  
   ```bash  
   python main.py /路径/到/目录 -s  
   ```  

## 报告格式  

脚本会生成 `report.txt` 文件，包含以下内容：  
1. 目录的树状结构  
2. 最大的文件列表  
3. 最大的目录列表  

示例报告：  
```  
/home/user/                          # 288 GB, 210 目录, 310443 文件  
├── Downloads/                  # 28 GB, 20 目录, 10423 文件  
│   └── backup.tar.gz           # 10.2 GB - gz 文件  
└── Photos/  
     ├── Vacation/              # 20 GB, 50 目录, 1000 文件  
     └── family.jpg             # 2GB - jpg 文件  

最大的10个文件：  
1. /home/user/Downloads/backup.tar.gz - 10.2 GB  
...  

最大的10个目录：  
1. /home/user/Downloads - 28 GB  
...  
```  

## 配置  

可以在脚本中修改默认值：  
```python  
DEFAULT_DIR = str(Path.home())    # 默认目录  
DEFAULT_DEPTH = 3                 # 默认深度  
DEFAULT_MIN_SIZE = 300 * 1024 * 1024  # 300MB 最小大小  
DEFAULT_TOP_FILES = 10            # 默认最大文件数量  
DEFAULT_TOP_DIRS = 10             # 默认最大目录数量  
REPORT_FILE = 'report.txt'        # 报告文件名  
```  

## 限制  

- 不追踪符号链接  
- 可能因权限问题跳过系统目录  
- 支持文件名中的Unicode字符，但可能影响对齐  

## 🌍 Доступные переводы | Available Translations | 可用翻译
- 🇬🇧 [English](Readme.md) - Английская версия  
- 🇷🇺 [Русский](Readme_ru.md) - Русская версия  
- 🇨🇳 [中文](Readme_ch.md) - Китайская версия

## 许可证  

本项目开源，基于 MIT 许可证。  
