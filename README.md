# CoderAgentFocus

一款 Fork from CursorFocus 的轻量级工具，保持项目结构和环境的聚焦视图。CursorFocus 会自动追踪项目文件、函数和环境变量，并每 60 秒更新一次，以便让您时刻了解项目的变化。
并根据检测项目 codebase 的实际技术栈，框架, 全局函数地图的定义, 全局关键变量等实际情况, 让 AI 对代码库进行深入分析 自动生成项目适配的 .cursorrules 文件。(目前 cursorrules 生成功能还是基于规则的, AI 生成功能正在开发中)


## 功能

- 🔄 实时项目结构追踪
- 📝 自动文件和函数文档生成
- 🌳 层级目录可视化
- 📏 文件长度标准和警报
- 🎯 项目特定信息检测
- 🔍 项目类型检测（Chrome 扩展、Node.js、Python）
- 🧩 模块化和可扩展设计
- 🎛️ 自动生成 .cursorrules 和项目适配

## 快速开始

1. 克隆 CursorFocus 项目：

   ```bash
   git clone https://github.com/Dror-Bengal/CursorFocus.git
   ```

2. 添加运行脚本权限：

   ```bash
   chmod +x CursorFocus/run.sh
   ```

3. 启动 CursorFocus：

   ```bash
   ./CursorFocus/run.sh
   ```

完成！CursorFocus 会自动：
- 创建必要的配置
- 安装依赖
- 开始监控项目
- 生成 Focus.md 文档

## 多项目支持

CursorFocus 可以同时监控多个项目。设置有两种方式：

### 1. 自动项目检测

使用扫描选项运行 CursorFocus 自动检测项目：

```bash
python3 CursorFocus/setup.py --scan /path/to/projects/directory
```

这将：
- 扫描目录中的受支持项目类型
- 列出所有检测到的项目
- 让您选择要监控的项目

### 2. 手动配置

编辑 `config.json` 以添加多个项目：

```json
{
    "projects": [
        {
            "name": "Project 1",
            "project_path": "/path/to/project1",
            "type": "node_js",
            "watch": true
        },
        {
            "name": "Project 2",
            "project_path": "/path/to/project2",
            "type": "chrome_extension",
            "watch": true
        }
    ]
}
```

每个项目可以有自己的：
- 自定义更新间隔
- 忽略的模式
- 文件长度标准
- 项目特定规则

### 支持的项目类型：

- Chrome 扩展（通过 manifest.json 检测）
- Node.js 项目（通过 package.json 检测）
- Python 项目（通过 setup.py 或 pyproject.toml 检测）
- React 应用（通过 src/App.js 检测）
- 通用项目（基本结构）

## 替代设置方法

### 手动设置

如果您更喜欢手动设置：

1. 安装依赖（需要 Python 3.6+）：

   ```bash
   cd CursorFocus
   pip install -r requirements.txt
   ```

2. 创建/编辑 config.json（可选）
3. 运行脚本：

   ```bash
   python3 focus.py
   ```

## 生成的文件

CursorFocus 会自动生成并维护三个关键文件：

1. **Focus.md**：项目文档和分析
   - 项目概述和结构
   - 文件描述和指标
   - 函数文档

2. **.cursorrules**：项目特定的 Cursor 设置
   - 根据项目类型自动生成
   - 针对项目结构定制
   - 随着项目的发展更新


## 设置

1. 将 CursorFocus 目录克隆或复制到您的项目中：

   ```bash
   git clone https://github.com/Dror-Bengal/CursorFocus.git CursorFocus
   ```

2. 安装依赖（需要 Python 3.6+）：

   ```bash
   cd CursorFocus
   pip install -r requirements.txt
   ```

3. 运行脚本：

   ```bash
   python3 focus.py
   ```

## 自动启动（macOS）

要在登录时自动启动 CursorFocus：

1. 创建 LaunchAgent 配置：

   ```bash
   mkdir -p ~/Library/LaunchAgents
   ```

2. 创建文件 `~/Library/LaunchAgents/com.cursorfocus.plist`，内容为：

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.cursorfocus</string>
       <key>ProgramArguments</key>
       <array>
           <string>/usr/local/bin/python3</string>
           <string>/path/to/your/CursorFocus/focus.py</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>StandardOutPath</key>
       <string>/tmp/cursorfocus.log</string>
       <key>StandardErrorPath</key>
       <string>/tmp/cursorfocus.err</string>
       <key>KeepAlive</key>
       <true/>
   </dict>
   </plist>
   ```

   将 `/path/to/your/CursorFocus/focus.py` 替换为实际路径。

3. 加载 LaunchAgent：

   ```bash
   launchctl load ~/Library/LaunchAgents/com.cursorfocus.plist
   ```

4. 要停止自动启动：

   ```bash
   launchctl unload ~/Library/LaunchAgents/com.cursorfocus.plist
   ```

## 输出

CursorFocus 会在项目根目录生成一个 `Focus.md` 文件，包含：

1. 项目概述
   - 项目名称和描述
   - 关键功能和版本
   - 项目类型检测

2. 项目结构
   - 目录层级
   - 文件描述
   - 函数列表及详细描述
   - 文件类型检测
   - 根据语言标准的文件长度警报

3. 代码分析
   - 关键函数识别
   - 详细的函数描述
   - 文件长度标准合规性

## 配置

编辑 `config.json` 来定制：

```json
{
    "project_path": "",
    "update_interval": 60,
    "max_depth": 3,
    "ignored_directories": [
        "__pycache__",
        "node_modules",
        "venv",
        ".git",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "coverage"
    ],
    "ignored_files": [
        ".DS_Store",
        "Thumbs.db",
        "*.pyc",
        "*.pyo",
        "package-lock.json",
        "yarn.lock"
    ]
}
```

## 文件长度标准

CursorFocus 为不同类型的文件提供内置文件长度标准：

- JavaScript/TypeScript：
  - 常规文件：300 行
  - React 组件（.jsx/.tsx）：250 行

- Python 文件：400 行

- 样式文件：
  - CSS/SCSS/LESS/SASS：400 行

- 模板文件：
  - HTML：300 行
  - Vue/Svelte 组件：250 行

- 配置文件：
  - JSON/YAML/TOML：100 行

- 文档文件：
  - Markdown/RST：500 行

当文件超过这些推荐的行数时，工具会发出警报。

## 项目结构

```
CursorFocus/
├── focus.py           # 主入口文件
├── analyzers.py       # 文件和代码分析
├── config.py          # 配置管理
├── content_generator.py # Focus 文件生成
├── project_detector.py # 项目类型检测
├── config.json        # 用户配置
└── requirements.txt   # 依赖
```

## 支持的项目类型

CursorFocus 会自动检测并提供以下项目的专用信息：

- Chrome 扩展（manifest.json）
- Node.js Projects (package.json)
- Python Projects (setup.py, pyproject.toml)
- Generic Projects (basic structure)

## 贡献

欢迎贡献！请随时提交拉取请求或创建错误和功能请求。

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 LICENSE 文件。
