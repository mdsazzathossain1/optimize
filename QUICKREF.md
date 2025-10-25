# 🚀 Quick Reference: Dynamic Configuration

## For Manufacturers

### Initial Setup
1. Go to: **http://localhost:5000/admin/config**
2. Enter structure:
   - Number of sections: `3`
   - Machines per section: `3,4,2`
3. Click **"Generate Section Forms"**
4. Fill in for each section:
   - Fixed setup cost
   - Capacity
   - Output score (optional)
5. Fill in for each machine:
   - Time per task
   - Available (1=Yes, 0=No)
   - Base cost
6. Set global defaults:
   - Default cost limit: `4200`
   - Max tasks: `10`
7. Click **"Save Configuration"**

### Update Configuration
- Same process as setup
- Current values shown in form
- New orders use updated config
- Old orders keep original snapshots

## For Customers

### Submit Order
1. Go to: **http://localhost:5000/**
2. Fill required fields:
   - Customer name
   - **Number of tasks** (see max limit)
   - Upload CAD files
   - Delivery time
   - Offered price
3. Check NDA box
4. Click **"Submit Order"**
5. Order processes automatically ✅

### Max Tasks Limit
- Shown on form: "Maximum: X tasks"
- Cannot exceed manufacturer capacity
- Changes when manufacturer updates config

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Sections** | Manufacturing departments (e.g., cutting, welding, assembly) |
| **Machines** | Equipment within each section |
| **Tasks** | Individual jobs from customer order (CAD files) |
| **Base Cost** | Starting cost per machine (auto-increments per task) |
| **Max Tasks** | Maximum number of tasks system can handle |
| **Capacity** | Max tasks a section can process |

## File Structure

```
data/
├── sections.csv          # Section configs (setup costs, capacities)
├── machines.csv          # Machine specs (times, availability)
├── costs.csv            # Auto-generated task costs
├── times.csv            # Task-specific times (optional)
└── config.json          # Structure metadata (sections, max_tasks)

orders/
└── ORD-XXXXXXXX/
    ├── customer_data.json      # Order details
    ├── params.csv              # Order parameters
    ├── [CAD files]             # Uploaded files
    ├── [config snapshots]      # Config at submission time
    ├── solution_summary.json   # Optimization results
    └── solution_assignments.csv # Task assignments
```

## Common Scenarios

### Scenario: Add a New Section
1. Go to config page
2. Change sections from `3` to `4`
3. Update machines: `3,4,2,5` (add 5 machines for new section)
4. Generate forms
5. Configure new Section 4
6. Save

### Scenario: Machine Breakdown
1. Go to config page
2. Find broken machine
3. Set Available to `0`
4. Save
5. Future orders won't use that machine

### Scenario: Increase Capacity
1. Go to config page
2. Change Max tasks from `10` to `15`
3. Optionally add more machines
4. Save
5. Customers can now submit up to 15 tasks

## Validation Rules

| Check | Error Message |
|-------|---------------|
| Tasks > max_tasks | "Number of tasks exceeds manufacturer capacity" |
| No config exists | "Manufacturer has not configured the system yet" |
| Missing machines | Form prevents submission |

## URLs

| Portal | URL |
|--------|-----|
| Customer | http://localhost:5000/ |
| Admin Dashboard | http://localhost:5000/admin |
| Configuration | http://localhost:5000/admin/config |
| View Results | http://localhost:5000/admin/results/ORD-XXXX |

## Cost Auto-Generation

System automatically creates costs for all tasks based on your base cost:

```
Machine Base Cost: $50.00
Task 1:  $50.00
Task 2:  $50.75  (+1.5%)
Task 3:  $51.51  (+1.5%)
Task 4:  $52.28  (+1.5%)
Task 5:  $53.06  (+1.5%)
...
Task 10: $57.19
```

## Tips

- ✅ **Test first**: Configure with small numbers, test, then scale up
- ✅ **Check availability**: Set machines to 0 if down for maintenance
- ✅ **Monitor capacity**: Adjust max_tasks based on order volume
- ✅ **Use snapshots**: Each order preserves config at submission time
- ✅ **Update gradually**: Small changes easier to validate than big jumps

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Form not generating | Click "Generate Section Forms" button |
| Customer can't submit | Check manufacturer has saved config |
| Optimization fails | Verify at least one available machine per section |
| Old values not showing | Generate forms after page loads |

## Documentation Files

- **README.md** - Complete system documentation
- **QUICKSTART.md** - Quick setup guide
- **DYNAMIC_CONFIG_GUIDE.md** - Detailed configuration instructions
- **DYNAMIC_IMPLEMENTATION.md** - Technical details
- **CHANGES.md** - Modification history
- **QUICKREF.md** - This file

## Support Commands

```powershell
# Start Flask app
.\.venv\Scripts\python.exe app.py

# Check configuration
type data\config.json

# View sections
type data\sections.csv

# View machines
type data\machines.csv

# Check orders
dir orders\
```

---

**Remember**: The system ensures compatibility automatically. Just configure your factory correctly, and customer orders will always match your capacity! 🎯
