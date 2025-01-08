#!/bin/bash

# 输出色彩配置
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 帮助信息
show_help() {
    echo "用法: ./run.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --scan [路径]   扫描目录中的项目（默认：当前目录）"
    echo "  --help          显示帮助信息"
    echo ""
    echo "示例:"
    echo "  ./run.sh                    # 使用默认配置运行"
    echo "  ./run.sh --scan             # 扫描当前目录中的项目"
    echo "  ./run.sh --scan ~/projects  # 扫描指定目录中的项目"
}

# 解析命令行参数
SCAN_MODE=false
SCAN_PATH="."

while [[ $# -gt 0 ]]; do
    case $1 in
        --scan)
            SCAN_MODE=true
            if [ ! -z "$2" ] && [ ${2:0:1} != "-" ]; then
                SCAN_PATH="$2"
                shift
            fi
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🚀 启动 CursorFocus...${NC}"

# 检查是否安装了 Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未安装 Python 3。请安装 Python 3 后再试。${NC}"
    exit 1
fi

# 检查所需的 Python 包是否已安装
echo -e "${BLUE}📦 正在检查依赖项...${NC}"
pip3 install -r "$SCRIPT_DIR/requirements.txt" > /dev/null 2>&1

if [ "$SCAN_MODE" = true ]; then
    echo -e "${BLUE}🔍 正在扫描项目目录: $SCAN_PATH${NC}"
    python3 "$SCRIPT_DIR/setup.py" --scan "$SCAN_PATH"
    exit $?
fi

# 获取父目录（项目根目录）
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 检查 config.json 是否存在，如果不存在则从示例文件创建
if [ ! -f "$SCRIPT_DIR/config.json" ]; then
    echo -e "${BLUE}📝 正在从模板创建配置文件...${NC}"
    if [ -f "$SCRIPT_DIR/config.example.json" ]; then
        # 从示例文件创建 config.json 并替换占位符路径
        sed "s|/path/to/your/project|$PROJECT_ROOT|g" "$SCRIPT_DIR/config.example.json" > "$SCRIPT_DIR/config.json"
        echo -e "${GREEN}✅ 已从模板创建配置文件${NC}"
    else
        echo -e "${RED}❌ 未找到 config.example.json 文件。请检查安装。${NC}"
        exit 1
    fi
fi

# 启动 CursorFocus
echo -e "${BLUE}🔍 启动 CursorFocus 监视器...${NC}"
cd "$PROJECT_ROOT"
python3 "$SCRIPT_DIR/focus.py"
