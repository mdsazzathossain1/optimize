# Quick Start Guide - Manufacturing Order Management System

## 🚀 Start the Application

```powershell
# From the project directory
cd d:\project\sazol_sir_schdl

# Activate virtual environment (if not already active)
.\.venv\Scripts\Activate.ps1

# Start the Flask application
.\.venv\Scripts\python.exe app.py
```

The application will be available at:
- **Customer Portal**: http://localhost:5000/
- **Admin Dashboard**: http://localhost:5000/admin

## 📋 First-Time Setup (Admin)

1. Open http://localhost:5000/admin
2. Click "Manage Manufacturer Configuration"
3. Configure your manufacturing infrastructure:
   - **Sections**: Factory sections with setup costs and capacities
   - **Machines**: Machines per section with availability and processing times
   - **Variable Costs**: Cost per task per machine
4. Click "Save Configuration"

### Example Configuration (Pre-filled in the form)

**Sections:**
```json
[
  {"section_id": 1, "fixed_setup_cost": 500.0, "capacity": 9, "output_score_optional": 100.0},
  {"section_id": 2, "fixed_setup_cost": 900.0, "capacity": 12, "output_score_optional": 130.0},
  {"section_id": 3, "fixed_setup_cost": 600.0, "capacity": 8, "output_score_optional": 110.0}
]
```

**Machines:**
```json
[
  {"section_id": 1, "machine_id": 1, "available": 1, "time_per_task": 1.7},
  {"section_id": 1, "machine_id": 2, "available": 1, "time_per_task": 1.85},
  {"section_id": 2, "machine_id": 1, "available": 1, "time_per_task": 2.0},
  {"section_id": 3, "machine_id": 1, "available": 1, "time_per_task": 2.3}
]
```

**Costs** (example for 6 tasks - expand as needed):
```json
[
  {"section_id": 1, "machine_id": 1, "task_id": 1, "variable_cost": 43.5},
  {"section_id": 1, "machine_id": 1, "task_id": 2, "variable_cost": 44.2},
  ...
]
```

## 👤 Customer Workflow

1. Open http://localhost:5000/
2. Fill out the order form:
   - Customer name/company
   - Number of CAD files (parts)
   - Upload CAD files
   - Product description and quantity
   - Desired delivery time (hours)
   - Offered price (total order price)
   - Technical specifications
   - Additional documents (optional)
3. Accept NDA/data-sharing terms
4. Click "Submit Order"
5. **Save your Order ID** (e.g., ORD-A1B2C3D4)
6. You'll see a success confirmation

## 🔧 Admin Workflow (Processing Orders)

1. Open http://localhost:5000/admin
2. View all submitted orders in the dashboard
3. For each pending order:
   - Enter cost limit (optional - defaults to very high)
   - Click "Process" button
   - System runs optimization and generates results
4. Click "View Results" to see:
   - Chosen section
   - Profit breakdown
   - Production time
   - Task-to-machine assignments
5. Download results:
   - JSON summary
   - CSV assignments

## 📁 File Structure After Usage

```
d:\project\sazol_sir_schdl\
├── data/                    # Manufacturer configuration (shared)
│   ├── sections.csv
│   ├── machines.csv
│   ├── costs.csv
│   └── times.csv
├── orders/                  # Customer orders (one folder per order)
│   ├── ORD-A1B2C3D4/
│   │   ├── customer_data.json         # Customer submission
│   │   ├── params.csv                 # Order parameters
│   │   ├── [uploaded CAD files]
│   │   ├── sections.csv               # Copy of manufacturer config
│   │   ├── machines.csv
│   │   ├── costs.csv
│   │   ├── solution_summary.json      # Optimization results
│   │   └── solution_assignments.csv   # Task assignments
│   └── ORD-X7Y8Z9/
│       └── ...
```

## 🎯 Key Features

### Customer Portal
✅ Web form for order submission  
✅ Multi-file CAD upload support  
✅ Specify delivery time and pricing  
✅ Technical requirements capture  
✅ Success confirmation with Order ID  
✅ **No access to results** (manufacturer only)

### Admin Portal
✅ View all customer orders  
✅ Configure manufacturer infrastructure  
✅ Process orders with optimization  
✅ View detailed results and assignments  
✅ Download JSON/CSV reports  
✅ **Separate from customer interface**

### Core Optimization (Unchanged Logic)
✅ Two-stage optimization approach preserved  
✅ Stage 1: Maximize profit  
✅ Stage 2: Minimize time (profit locked)  
✅ Handles sections, machines, capacity, costs  
✅ Respects time/cost/capacity constraints

## 🔒 Security Features

- File uploads validated by extension
- Filenames sanitized (secure_filename)
- Max upload: 100MB
- Random secret key per session
- Separate customer/admin interfaces

## 🛠️ Troubleshooting

### Port Already in Use
```powershell
# Use a different port
$env:FLASK_RUN_PORT="5001"
.\.venv\Scripts\python.exe app.py
```

### Can't Access from Browser
- Check firewall settings
- Ensure the server shows "Running on http://127.0.0.1:5000"
- Try http://127.0.0.1:5000 instead of localhost

### Optimization Fails
- Check cost_limit_Cdesired is not too low
- Verify time_limit_Tdesired is achievable
- Ensure machines are available in at least one section
- Check variable costs cover all tasks (1 to p)

### Missing Configuration
- Go to Admin Dashboard
- Click "Manage Manufacturer Configuration"
- Save configuration before processing orders

## 📞 Support

For questions or issues:
1. Check README.md for detailed documentation
2. Review error messages in terminal output
3. Verify manufacturer configuration is complete
4. Contact system administrator

## 🎉 Success!

Your Manufacturing Order Management System is now running!
- Customers can submit orders with CAD files
- Manufacturers can configure their infrastructure
- Optimization runs automatically on order processing
- Results are displayed only to admin users
