# Manufacturing Order Management System

A Flask web application for managing manufacturing orders with optimization capabilities. Built with separate customer and manufacturer portals and **dynamic configuration support**.

## Features

### Customer Portal
- Submit manufacturing orders with CAD file uploads
- Specify delivery timeframes and pricing
- Provide technical specifications and requirements
- Secure file handling and order tracking
- **Automatic validation** against manufacturer capacity

### Manufacturer Admin Portal
- View and manage all customer orders
- **Dynamically configure** manufacturing infrastructure (sections, machines, costs)
- Adjust number of sections and machines to match factory layout
- Automatic order processing using two-stage optimization model
- View detailed optimization results and assignments
- Download solution reports (JSON, CSV)

### Core Optimization Engine
- **Preserved original logic**: Two-stage optimization approach
- Stage 1: Maximize profit given constraints
- Stage 2: Minimize production time while maintaining optimal profit
- Handles **variable numbers** of sections, machines, and task assignments
- Considers fixed setup costs, variable costs, capacities, and availability
- **Adapts automatically** to any configuration structure

## Project Structure

```
d:\project\sazol_sir_schdl\
├── app.py                      # Main Flask application
├── solver.py                   # Core optimization logic (unchanged)
├── solve_order.py              # Original standalone script
├── requirements_app.txt        # Dependencies for Flask app
├── templates/                  # HTML templates
│   ├── base.html
│   ├── customer_form.html
│   ├── customer_success.html
│   ├── admin_dashboard.html
│   ├── admin_config.html
│   └── admin_results.html
├── data/                       # Default manufacturer configuration
│   ├── sections.csv
│   ├── machines.csv
│   ├── costs.csv
│   └── times.csv
└── orders/                     # Customer order submissions (auto-created)
    └── ORD-XXXXXXXX/
        ├── customer_data.json
        ├── params.csv
        ├── [uploaded CAD files]
        ├── solution_summary.json
        └── solution_assignments.csv
```

## Installation

1. **Activate virtual environment** (if not already activated):
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install Flask and dependencies**:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements_app.txt
   ```

## Usage

### Starting the Application

```powershell
.\.venv\Scripts\python.exe app.py
```

The application will start on `http://localhost:5000`

### Access Points

- **Customer Portal**: http://localhost:5000/
- **Admin Dashboard**: http://localhost:5000/admin

### Workflow

1. **Configure Manufacturer Data** (Admin - first time setup)
   - Navigate to Admin Dashboard → "Manage Manufacturer Configuration"
   - **Set structure**: Choose number of sections and machines per section
   - Click "Generate Section Forms" to create dynamic configuration
   - Configure each section: fixed costs, capacity, output score
   - Configure each machine: time per task, availability, base cost
   - Set default cost limit and maximum tasks
   - Save configuration (creates CSVs in `data/` folder)
   - See [DYNAMIC_CONFIG_GUIDE.md](DYNAMIC_CONFIG_GUIDE.md) for detailed instructions

2. **Customer Submits Order**
   - Fill out order form with all required fields
   - System shows maximum task limit based on manufacturer config
   - Upload CAD files and any additional documents
   - Specify delivery time and offered price
   - Submit order (generates unique Order ID)
   - **Automatic validation** against manufacturer capacity
   - **Automatic processing** - optimization runs immediately

3. **Manufacturer Views Results** (Admin)
   - Order automatically appears as "Processed" in Admin Dashboard
   - Click "View Results" to see optimization output
   - Financial breakdown, chosen section, task assignments displayed
   - Download JSON summary and CSV assignments
   - Original order data and CAD files accessible

4. **Update Configuration** (Admin - anytime)
   - Modify number of sections/machines as factory changes
   - Adjust costs, times, capacities
   - New orders automatically use updated config
   - Old orders retain their original configuration snapshot

## Input Requirements

### Customer Inputs (via web form)
- Customer name/company
- Order reference number (optional)
- **Number of CAD files (p)** - automatically validated against max_tasks
- CAD file uploads
- Product description
- Quantity/batch size
- Desired delivery time (Tdesired, hours)
- Offered order price (Cc, total)
- Material specifications
- Surface finish/tolerances
- Testing requirements
- Certifications
- Additional documents
- Special instructions

### Manufacturer Inputs (via admin config)
- **Structure Configuration**:
  - Number of sections (1-10)
  - Machines per section (comma-separated list)
  - Maximum tasks to support
- **Per Section**: section_id, fixed_setup_cost, capacity, output_score_optional
- **Per Machine**: section_id, machine_id, available (0/1), time_per_task, base_cost
- **Global Settings**: default_cost_limit
- **Auto-Generated**: Variable costs for all tasks (1.5% increments per task)

## Optimization Model

The core solver (`solver.py`) implements a two-stage mixed-integer linear program:

### Stage 1: Profit Maximization
- **Objective**: Maximize (Revenue - Variable Costs - Fixed Setup Costs)
- **Constraints**:
  - Select exactly one section
  - Assign each task to exactly one machine in the chosen section
  - Respect time limits, cost limits, and capacity constraints
  - Honor machine availability

### Stage 2: Time Minimization
- **Objective**: Minimize total production time
- **Constraints**:
  - All Stage 1 constraints
  - **Lock profit to Stage 1 optimum** (maintain profitability)
  - Find fastest schedule among equally profitable solutions

## File Formats

### sections.csv
```csv
section_id,fixed_setup_cost,capacity,output_score_optional
1,500.0,9,100.0
2,900.0,12,130.0
3,600.0,8,110.0
```

### machines.csv
```csv
section_id,machine_id,available,time_per_task
1,1,1,1.7
1,2,1,1.85
2,1,1,2.0
```

### costs.csv
```csv
section_id,machine_id,task_id,variable_cost
1,1,1,43.5
1,1,2,44.2
1,2,1,46.2
```

### params.csv (auto-generated per order)
```csv
param,value
num_tasks_p,6
order_price_Cc,6000.0
time_limit_Tdesired,24.0
cost_limit_Cdesired,4200.0
```

## Security Notes

- File uploads are validated by extension
- Filenames are sanitized using `secure_filename()`
- Maximum upload size: 100MB
- Secret key generated randomly on each app start
- For production: set permanent secret key, use HTTPS, add authentication

## Troubleshooting

### "No module named 'flask'"
```powershell
.\.venv\Scripts\python.exe -m pip install Flask
```

### "Number of tasks exceeds manufacturer capacity"
- Customer requested more tasks than manufacturer configured
- **Solution**: Manufacturer should increase `max_tasks` in configuration, or customer should reduce task count
- See customer form for current maximum task limit

### "Manufacturer has not configured the system yet"
- Configuration files missing in `data/` folder
- **Solution**: Complete configuration at `/admin/config` before accepting orders

### "Optimization infeasible"
- Check that cost_limit_Cdesired is not too restrictive
- Verify time_limit_Tdesired is achievable
- Ensure at least one section has available machines
- Check that variable costs are properly defined for all tasks

### Form doesn't show generated sections
- **Solution**: Click "Generate Section Forms" button after entering structure values
- Ensure number of machine counts matches number of sections

### Dynamic configuration not working
- See detailed guide: [DYNAMIC_CONFIG_GUIDE.md](DYNAMIC_CONFIG_GUIDE.md)
- Verify JavaScript is enabled in browser
- Check console for errors

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup and basic usage
- **[DYNAMIC_CONFIG_GUIDE.md](DYNAMIC_CONFIG_GUIDE.md)** - Complete guide to dynamic configuration
- **[CHANGES.md](CHANGES.md)** - Summary of all modifications from original script

## Original Script

The original standalone script `solve_order.py` still works independently:

```powershell
.\.venv\Scripts\python.exe solve_order.py
```

It generates sample data and runs the optimization, saving results to the root directory.

## License

Internal use only. Contains proprietary optimization logic.

## Contact

For questions or support, contact the system administrator.
