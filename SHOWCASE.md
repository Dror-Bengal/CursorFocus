# CursorFocus Showcase

This showcase demonstrates the key features and capabilities of CursorFocus using real examples.

## Example Output

Below is an example of a Focus.md file generated for a React project:

```markdown
# Project Focus: E-commerce Dashboard

**Current Goal:** Build a modern e-commerce dashboard with real-time analytics and inventory management.

**Key Components:**
📁 src/
  ├── components/
  │   ├── Dashboard/
  │   ├── Analytics/
  │   └── Inventory/
  ├── services/
  │   └── api/
  └── utils/

**Project Context:**
Type: React Application
Target Users: E-commerce store managers and administrators
Main Functionality: Real-time sales tracking and inventory management

Key Requirements:
- Real-time sales dashboard
- Inventory management system
- Analytics visualization
- User authentication

**Development Guidelines:**
- Keep code modular and reusable
- Follow React best practices
- Maintain clean separation of concerns

# File Analysis

`src/components/Dashboard/SalesOverview.tsx` (280 lines)
**Main Responsibilities:** Main dashboard component displaying sales metrics and KPIs
**Key Functions:**
<useSalesData>: Custom hook for fetching and processing real-time sales data from the API
<SalesChart>: Renders an interactive chart showing daily/monthly sales trends with customizable date ranges
<KPIGrid>: Displays key performance indicators in a responsive grid layout with real-time updates

`src/services/api/salesApi.ts` (180 lines)
**Main Responsibilities:** API service for sales-related operations
**Key Functions:**
<fetchSalesData>: Retrieves sales data with support for filtering and date ranges
<processSalesMetrics>: Processes raw sales data to calculate various business metrics
<aggregateByPeriod>: Aggregates sales data by day, week, or month for trend analysis

`src/components/Inventory/ProductList.tsx` (320 lines)
**Main Responsibilities:** Product inventory management interface
**Key Functions:**
<useInventoryData>: Manages inventory data state and operations
<ProductTable>: Renders a sortable and filterable table of products
<StockAlerts>: Displays alerts for low stock items and inventory issues
**📄 Long-file Alert: File exceeds the recommended 250 lines for .tsx files (320 lines)**

Last updated: December 28, 2023 at 11:45 PM
```

## Feature Highlights

### 1. Smart Project Type Detection
CursorFocus automatically detects your project type and provides relevant information:
- React/Node.js projects: Component structure, hooks, and API endpoints
- Python projects: Classes, functions, and module relationships
- Chrome Extensions: Manifest details and extension components

### 2. File Length Standards
The tool provides customized alerts based on file type:
```markdown
**📄 Long-file Alert: File exceeds the recommended 250 lines for .tsx files (320 lines)**
```

### 3. Detailed Function Analysis
Functions are analyzed with context-aware descriptions:
```markdown
<useSalesData>: Custom hook for fetching and processing real-time sales data from the API
<ProductTable>: Renders a sortable and filterable table of products with pagination
```

### 4. Directory Visualization
Clear, hierarchical representation of your project structure:
```markdown
📁 src/
  ├── components/
  │   ├── Dashboard/
  │   ├── Analytics/
  │   └── Inventory/
  ├── services/
  │   └── api/
  └── utils/
```

### 5. Project Context
Comprehensive project overview with key information:
```markdown
Type: React Application
Target Users: E-commerce store managers
Main Functionality: Real-time sales tracking
```

## Real-World Use Cases

### 1. Onboarding New Developers
- Quick project overview and structure understanding
- Identification of key components and their responsibilities
- Clear view of coding standards and file organization

### 2. Code Review and Maintenance
- File length monitoring for maintainability
- Function documentation for better understanding
- Project structure visualization for navigation

### 3. Technical Documentation
- Automated documentation generation
- Real-time updates as code changes
- Consistent format across projects

### 4. Project Management
- Progress tracking through file and function analysis
- Code organization oversight
- Standards compliance monitoring

## Tips for Best Results

1. **File Organization:**
   - Keep related files in appropriate directories
   - Use meaningful file names
   - Maintain a clean project structure

2. **Function Documentation:**
   - Write clear function names
   - Add descriptive comments
   - Follow consistent documentation patterns

3. **Configuration:**
   - Customize ignored directories for your needs
   - Adjust file length standards if needed
   - Set appropriate scan depth for your project

4. **Regular Updates:**
   - Keep CursorFocus running for real-time updates
   - Review the Focus.md file periodically
   - Use alerts to maintain code quality 