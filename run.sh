#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Help message
show_help() {
    echo "Usage: ./run.sh [options]"
    echo ""
    echo "Options:"
    echo "  --scan [path]    Scan directory for projects (default: current directory)"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run.sh                     # Run with default configuration"
    echo "  ./run.sh --scan              # Scan current directory for projects"
    echo "  ./run.sh --scan ~/projects   # Scan specific directory for projects"
}

# Parse command line arguments
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
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🚀 Starting CursorFocus...${NC}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check if required Python packages are installed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
pip3 install -r "$SCRIPT_DIR/requirements.txt" > /dev/null 2>&1

if [ "$SCAN_MODE" = true ]; then
    echo -e "${BLUE}🔍 Scanning for projects in: $SCAN_PATH${NC}"
    python3 "$SCRIPT_DIR/setup.py" --scan "$SCAN_PATH"
    exit $?
fi

# Get the parent directory (project root)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if config.json exists, if not create it from example
if [ ! -f "$SCRIPT_DIR/config.json" ]; then
    echo -e "${BLUE}📝 Creating configuration from template...${NC}"
    if [ -f "$SCRIPT_DIR/config.example.json" ]; then
        # Create config.json from example and replace placeholder path
        sed "s|/path/to/your/project|$PROJECT_ROOT|g" "$SCRIPT_DIR/config.example.json" > "$SCRIPT_DIR/config.json"
        echo -e "${GREEN}✅ Configuration created from template${NC}"
    else
        echo -e "${RED}❌ config.example.json not found. Please check the installation.${NC}"
        exit 1
    fi
fi

# Run CursorFocus
echo -e "${BLUE}🔍 Starting CursorFocus monitor...${NC}"
cd "$PROJECT_ROOT"
python3 "$SCRIPT_DIR/focus.py" 