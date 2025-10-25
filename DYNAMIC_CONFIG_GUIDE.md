# Dynamic Configuration Guide

## Overview
The system now supports **fully dynamic configuration** where manufacturers can adjust the number of sections and machines to match their actual factory setup. Customer inputs are automatically validated against this configuration to ensure compatibility.

## Key Features

### 1. **Flexible Structure**
- Configure **any number of sections** (1-10)
- Set **different numbers of machines per section**
- Example: Section 1 (3 machines), Section 2 (5 machines), Section 3 (2 machines)

### 2. **Automatic Compatibility**
- Customer form automatically shows maximum task limit based on manufacturer config
- System validates customer orders against manufacturer capacity
- Optimization model adapts to any configuration structure

### 3. **Cost Auto-Generation**
- Set base cost for each machine
- System automatically generates costs for all tasks with 1.5% increments
- Configure how many tasks to generate (default: 10)

## How to Use

### For Manufacturers

1. **Access Configuration**
   - Navigate to: `http://localhost:5000/admin/config`

2. **Set Structure**
   - Enter number of sections (e.g., `3`)
   - Enter machines per section as comma-separated values (e.g., `3,4,2`)
   - Click "Generate Section Forms"

3. **Configure Each Section**
   For each section, set:
   - Fixed setup cost
   - Capacity (max tasks)
   - Output score (optional)

4. **Configure Each Machine**
   For each machine in each section, set:
   - Time per task
   - Available status (1=Yes, 0=No)
   - Base variable cost

5. **Set Defaults**
   - Default cost limit for orders
   - Maximum number of tasks to support

6. **Save Configuration**
   - All data saved to `data/` folder
   - Used automatically for all new customer orders

### For Customers

1. **Submit Order**
   - Navigate to: `http://localhost:5000/`

2. **Enter Task Count**
   - System shows maximum allowed tasks
   - Based on manufacturer's current configuration
   - Cannot exceed manufacturer capacity

3. **Automatic Processing**
   - Order validated against manufacturer config
   - Rejected if tasks exceed capacity
   - Automatically processed if valid

## Technical Details

### Configuration Files Generated

```
data/
├── sections.csv          # Section configurations
├── machines.csv          # Machine configurations (all sections)
├── costs.csv            # Auto-generated costs for all tasks
├── times.csv            # Task-specific times (optional)
└── config.json          # Metadata (structure, limits)
```

### config.json Structure
```json
{
  "default_cost_limit": 4200.0,
  "max_tasks": 10,
  "num_sections": 3,
  "machines_per_section": [3, 4, 2],
  "last_updated": "2025-10-25T10:30:00"
}
```

### sections.csv Example
```csv
section_id,fixed_setup_cost,capacity,output_score_optional
1,500.0,9,100.0
2,900.0,12,130.0
3,600.0,8,110.0
```

### machines.csv Example
```csv
section_id,machine_id,available,time_per_task
1,1,1,1.7
1,2,1,1.85
1,3,1,1.95
2,1,1,2.0
2,2,0,2.1
...
```

### costs.csv Auto-Generation
For base cost of $43.00 on Machine 1, Section 1:
```csv
section_id,machine_id,task_id,variable_cost
1,1,1,43.00
1,1,2,43.65    # +1.5%
1,1,3,44.30    # +1.5%
...
1,1,10,49.13
```

## Validation Rules

### Manufacturer Side
- ✅ Must have at least 1 section
- ✅ Each section must have at least 1 machine
- ✅ Machine counts must match number of sections
- ✅ All costs, times, and capacities must be positive

### Customer Side
- ✅ Task count cannot exceed `max_tasks` from config
- ✅ Manufacturer must have saved configuration before accepting orders
- ✅ All required fields must be filled
- ✅ Order automatically validated and processed

## Compatibility Assurance

The system ensures perfect compatibility through:

1. **Shared Configuration Source**
   - Both portals read from same `config.json`
   - Customer form dynamically adjusts to manufacturer limits

2. **Pre-Submission Validation**
   - Task count checked before order processing
   - Clear error messages if limits exceeded

3. **Snapshot Preservation**
   - Each order gets copy of manufacturer config at time of submission
   - Historical orders remain valid even if config changes

4. **Solver Compatibility**
   - Core optimization logic unchanged
   - Works with any valid configuration structure
   - Adapts to variable sections and machines

## Example Scenarios

### Scenario 1: Small Workshop
```
Sections: 2
Machines per section: 2,3
Max tasks: 5
```
Customer can submit 1-5 task orders.

### Scenario 2: Large Factory
```
Sections: 5
Machines per section: 4,6,3,5,4
Max tasks: 20
```
Customer can submit 1-20 task orders.

### Scenario 3: Changing Capacity
Manufacturer increases from:
```
Max tasks: 10  →  Max tasks: 15
```
- Old orders (1-10 tasks) unaffected
- New orders can submit up to 15 tasks
- Customer form automatically updates

## Troubleshooting

### Issue: Customer sees "exceeds manufacturer capacity"
**Solution**: Manufacturer should increase `max_tasks` in config or customer should reduce task count.

### Issue: "Manufacturer has not configured the system yet"
**Solution**: Manufacturer must complete configuration at `/admin/config` first.

### Issue: Form doesn't show generated sections
**Solution**: Click "Generate Section Forms" button after entering structure values.

### Issue: Optimization fails with new config
**Solution**: Ensure all machines have valid costs and at least one available machine per section.

## Best Practices

1. **Plan Your Structure**
   - Survey actual factory layout
   - Count real sections and machines
   - Set realistic capacities

2. **Test Configuration**
   - Submit test order after configuration
   - Verify optimization runs successfully
   - Check results match expectations

3. **Document Changes**
   - Note when configuration updated
   - Keep record of capacity changes
   - Inform customers of new limits

4. **Gradual Expansion**
   - Start with smaller max_tasks
   - Increase as system proven
   - Monitor processing times

## Migration from Fixed Config

If you have existing hardcoded configuration:

1. Count your current sections (was: 3)
2. Count machines per section (was: 3,4,2)
3. Enter these values in new dynamic form
4. Copy existing cost/time values
5. Save and test with existing orders

All existing orders remain valid with their original snapshots.
