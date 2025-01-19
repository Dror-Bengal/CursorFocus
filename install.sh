#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Installing CursorFocus...${NC}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}📚 Installing dependencies...${NC}"
pip install -e .

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${BLUE}📝 Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file. Please edit it to add your Gemini API key.${NC}"
    echo -e "   Get your API key from: ${BLUE}https://makersuite.google.com/app/apikey${NC}"
fi

# Create config.json if it doesn't exist
if [ ! -f "config.json" ]; then
    echo -e "${BLUE}⚙️ Creating config.json...${NC}"
    cp config.example.json config.json
    echo -e "${GREEN}✅ Created config.json. Please edit it to configure your project settings.${NC}"
fi

echo -e "${GREEN}✅ Installation complete!${NC}"
echo -e "\nNext steps:"
echo -e "1. Edit ${BLUE}.env${NC} to add your Gemini API key"
echo -e "2. Edit ${BLUE}config.json${NC} to configure your project settings"
echo -e "3. Run ${BLUE}cursorfocus${NC} for continuous monitoring"
echo -e "   or ${BLUE}cursorfocus-review${NC} for a one-time code review" 