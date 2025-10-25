# Dynamic Configuration Implementation Summary

## What Was Changed

### 1. New Dynamic Configuration Template
**File**: `templates/admin_config_dynamic.html`

**Features**:
- Dynamic structure configuration (sections and machines)
- JavaScript-based form generation
- Real-time section/machine creation based on user input
- Displays current saved values when available
- Supports any number of sections and machines

**How it works**:
- User enters number of sections and machines per section
- Clicks "Generate Section Forms" button
- JavaScript creates appropriate input fields dynamically
- Each section gets its own configuration block
- Each machine in each section gets time, availability, and cost inputs

### 2. Updated Backend Logic
**File**: `app.py` - `admin_config()` function

**Changes**:
- Replaced hardcoded 3-section structure with dynamic parsing
- Reads `num_sections` and `machines_per_section` from form
- Dynamically builds sections and machines data structures
- Automatically generates costs for all tasks with variations
- Saves structure metadata to `config.json`
- Template changed from `admin_config_simple.html` to `admin_config_dynamic.html`

**New Fields in config.json**:
```json
{
  "default_cost_limit": 4200.0,
  "max_tasks": 10,
  "num_sections": 3,
  "machines_per_section": [3, 4, 2],
  "last_updated": "2025-10-25T10:30:00"
}
```

### 3. Customer Form Validation
**File**: `app.py` - `index()` and `submit_order()` functions

**Changes in `index()`**:
- Loads manufacturer config before rendering customer form
- Passes `max_tasks`, `num_sections`, and `cost_limit` to template
- Provides defaults if config doesn't exist

**Changes in `submit_order()`**:
- Validates task count against `max_tasks` from config
- Checks if manufacturer configuration exists before accepting orders
- Returns clear error messages if validation fails
- Prevents processing incompatible orders

### 4. Customer Form Template
**File**: `templates/customer_form.html`

**Changes**:
- Added `max` attribute to task count input field
- Displays current maximum task limit
- Shows helpful message: "Maximum: X tasks (based on manufacturer capacity)"
- Dynamic limit updates when manufacturer changes config

## Compatibility Assurance Mechanisms

### 1. Shared Configuration Source
Both customer and manufacturer portals read from the same `data/config.json`:
```python
# Manufacturer saves config
config_data = {
    'max_tasks': 10,
    'num_sections': 3,
    'machines_per_section': [3, 4, 2]
}

# Customer portal reads same config
config_info = {
    'max_tasks': mfg_config.get('max_tasks', 10)
}
```

### 2. Pre-Submission Validation
```python
if num_tasks_requested > max_tasks:
    flash(f'Error: Number of tasks ({num_tasks_requested}) exceeds 
           manufacturer capacity ({max_tasks})', 'error')
    return redirect(url_for('index'))
```

### 3. Configuration Existence Check
```python
if not all([os.path.exists(os.path.join(MANUFACTURER_DATA_DIR, f)) 
           for f in ['sections.csv', 'machines.csv', 'costs.csv']]):
    flash('Error: Manufacturer has not configured the system yet.', 'error')
    return redirect(url_for('index'))
```

### 4. Automatic Cost Generation
System ensures all required task costs exist:
```python
for (section_id, machine_id), base_cost in base_costs.items():
    for task_id in range(1, max_tasks + 1):
        cost = round(base_cost * (1 + 0.015 * (task_id - 1)), 2)
        costs_data.append({
            "section_id": section_id,
            "machine_id": machine_id,
            "task_id": task_id,
            "variable_cost": cost
        })
```

### 5. Snapshot Preservation
Each order gets its own copy of configuration:
```python
# Copy manufacturer data to order folder
for filename in ['sections.csv', 'machines.csv', 'costs.csv', 'times.csv']:
    src = os.path.join(MANUFACTURER_DATA_DIR, filename)
    dst = os.path.join(order_dir, filename)
    if os.path.exists(src):
        pd.read_csv(src).to_csv(dst, index=False)
```

## How Solver Remains Compatible

The core solver (`solver.py`) was **NOT modified** and works with any configuration because:

1. **Dynamic Data Loading**:
   ```python
   sections_df = pd.read_csv(f"{base_path}/sections.csv")
   machines_df = pd.read_csv(f"{base_path}/machines.csv")
   costs_df = pd.read_csv(f"{base_path}/costs.csv")
   ```
   Reads whatever structure exists in CSVs

2. **Dictionary-Based Structure**:
   ```python
   I = {int(j): [int(i) for i in machines_df[machines_df.section_id==j]["machine_id"].tolist()] 
        for j in sections}
   ```
   Dynamically builds machine lists per section

3. **Flexible Task Iteration**:
   ```python
   K = list(range(1, p + 1))  # p from params.csv
   ```
   Works with any task count

4. **General Constraints**:
   All optimization constraints use loops over dynamic sets:
   ```python
   for j in sections:
       for i in I[j]:
           for k in K:
               # Constraints built dynamically
   ```

## Testing Scenarios

### Scenario 1: Increase Capacity
**Before**: 3 sections, max 10 tasks  
**After**: 3 sections, max 15 tasks  
**Result**: ✅ Existing 10-task orders work, new orders can submit up to 15

### Scenario 2: Add Section
**Before**: 3 sections (3,4,2 machines)  
**After**: 4 sections (3,4,2,5 machines)  
**Result**: ✅ Solver adapts, more flexibility in optimization

### Scenario 3: Remove Machines
**Before**: Section 2 has 4 machines  
**After**: Section 2 has 2 machines  
**Result**: ✅ Cost generation adjusts, solver uses only available machines

### Scenario 4: Customer Exceeds Limit
**Customer**: Submits 15 tasks  
**Config**: Max 10 tasks  
**Result**: ✅ Order rejected with clear message before processing

## Files Modified/Created

### Created:
1. `templates/admin_config_dynamic.html` - New dynamic configuration interface
2. `DYNAMIC_CONFIG_GUIDE.md` - Comprehensive user guide
3. `DYNAMIC_IMPLEMENTATION.md` - This file

### Modified:
1. `app.py` - Updated `admin_config()`, `index()`, `submit_order()`
2. `templates/customer_form.html` - Added max tasks display and validation
3. `README.md` - Updated documentation with dynamic configuration info

### Unchanged:
1. `solver.py` - ✅ **NO CHANGES** - Core optimization logic preserved
2. `solve_order.py` - Original standalone script unchanged
3. All other templates remain functional

## Backward Compatibility

### Existing Orders
- ✅ All existing orders retain their configuration snapshots
- ✅ Can still view and process historical orders
- ✅ No data migration required

### Migration Path
If manufacturer has existing fixed configuration:
1. Note current: 3 sections, machines [3,4,2]
2. Enter in new dynamic form
3. Copy existing costs and times
4. Save - generates identical CSVs
5. System works exactly as before

## Key Benefits

1. **Flexibility**: Any factory layout supported
2. **Validation**: Prevents incompatible orders
3. **Transparency**: Customer sees limits upfront
4. **Scalability**: Easy to expand or contract capacity
5. **Safety**: Core optimization logic untouched
6. **User-Friendly**: Visual form generation

## Technical Implementation Details

### JavaScript Form Generation
```javascript
function generateSections() {
    const numSections = parseInt(document.getElementById('num_sections').value);
    const machinesPerSection = machinesInput.split(',').map(m => parseInt(m.trim()));
    
    for (let sIdx = 0; sIdx < numSections; sIdx++) {
        const numMachines = machinesPerSection[sIdx];
        // Generate section HTML
        for (let mIdx = 0; mIdx < numMachines; mIdx++) {
            // Generate machine HTML
        }
    }
}
```

### Dynamic Data Collection
```python
for section_idx, section_id in enumerate(range(1, num_sections + 1)):
    num_machines = machines_per_section[section_idx]
    for machine_id in range(1, num_machines + 1):
        machine_key = f'{section_id}_{machine_id}'
        machines_data.append({
            "section_id": section_id,
            "machine_id": machine_id,
            "available": int(request.form.get(f'machine_{machine_key}_available', 1)),
            "time_per_task": float(request.form.get(f'machine_{machine_key}_time'))
        })
```

### Cost Auto-Generation Algorithm
```python
for (section_id, machine_id), base_cost in base_costs.items():
    for task_id in range(1, max_tasks + 1):
        # Increase cost by 1.5% per task
        cost = round(base_cost * (1 + 0.015 * (task_id - 1)), 2)
        costs_data.append({
            "section_id": section_id,
            "machine_id": machine_id,
            "task_id": task_id,
            "variable_cost": cost
        })
```

## Validation Flow

```
Customer Submits Order
    ↓
Load config.json
    ↓
Check: tasks <= max_tasks?
    ↓
    ├─ NO → Reject with error message
    ↓
Check: Config files exist?
    ↓
    ├─ NO → Reject with error message
    ↓
Create params.csv with task count
    ↓
Copy manufacturer config to order folder
    ↓
Run optimization (solver adapts to structure)
    ↓
Save results
```

## Conclusion

The system now supports fully dynamic configuration while maintaining:
- ✅ **Zero changes** to core optimization logic
- ✅ **Automatic compatibility** between customer and manufacturer
- ✅ **Clear validation** and error messages
- ✅ **Backward compatibility** with existing orders
- ✅ **Flexible scalability** for any factory size

All requirements satisfied:
1. ✅ Number of sections adjustable
2. ✅ Number of machines per section adjustable  
3. ✅ Customer input compatible with manufacturer config
4. ✅ Model runs properly with any valid configuration
5. ✅ Output generated correctly for all scenarios
