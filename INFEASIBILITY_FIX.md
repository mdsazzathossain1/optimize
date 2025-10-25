# Fix Summary: Infeasibility Handling

## Problem
Orders were failing with cryptic error: `'summary'`

## Root Cause Analysis

### Issue 1: Missing Configuration (FIXED in previous session)
- `data/costs.csv` was incomplete
- Missing `config.json`
- **Solution**: Created `fix_config.py` to regenerate complete configuration

### Issue 2: Poor Infeasibility Handling (FIXED NOW)
- Solver returns different structure when optimization is infeasible
- App was checking for `'summary'` key without handling infeasible case
- No diagnostic information provided to user

## What Happens When Infeasible

### Solver Behavior
When Stage 1 optimization fails (infeasible, unbounded, or other non-optimal status):

```python
# In solver.py line 121
return {"status1": status1, "note": "Stage 1 not optimal or infeasible."}
```

Returns dict with only `['status1', 'note']` keys - NO `'summary'` or `'assignments'`

### Why Orders Become Infeasible

An order is infeasible when constraints **cannot be simultaneously satisfied**:

1. **Time Constraint Too Tight**
   - Customer requests 6 hours delivery
   - Minimum possible time is 9.25 hours (even with fastest machines)
   - **Cannot physically complete in time**

2. **Cost Constraint Too Low**
   - Cost limit set to $1000
   - Minimum cost is $1500
   - **Cannot complete within budget**

3. **Insufficient Capacity**
   - Customer requests 15 tasks
   - Maximum section capacity is 12
   - **Not enough capacity**

4. **No Available Machines**
   - All machines in all sections marked unavailable
   - **Cannot assign tasks**

## Fixes Applied

### 1. Enhanced Error Detection (`app.py`)

**Before**:
```python
if result is None or 'summary' not in result or 'assignments' not in result:
    raise ValueError("Solver returned invalid result...")
```

**After**:
```python
if 'summary' not in result:
    status = result.get('status1', 'Unknown')
    note = result.get('note', 'No details provided')
    
    error_msg = f"Optimization infeasible (Status: {status}). "
    if 'Infeasible' in status:
        error_msg += f"Cannot satisfy constraints with current parameters. "
        error_msg += f"Try: increasing cost limit (current: {DATA['C_desired']}), "
        error_msg += f"increasing time limit (current: {DATA['T_desired']}), "
        error_msg += f"or reducing offered price (current: {DATA['Cc']})."
    else:
        error_msg += f"Details: {note}"
    
    raise ValueError(error_msg)
```

### 2. Debug Output

Added console logging:
```python
print(f"Loading data for order {order_id}...")
print(f"Running solver for {DATA['p']} tasks...")
print(f"Solver result keys: {list(result.keys())}")
print(f"✅ Order {order_id} processed successfully!")
```

### 3. Diagnostic Tools

Created helper scripts:

**`test_solver.py`** - Tests solver directly with order data
**`diagnose_order.py`** - Analyzes why order is infeasible
- Shows cost analysis per section
- Shows time analysis per section
- Identifies specific constraint violations

## Example: Order ORD-0937B623

### Customer Request
- 5 tasks
- 6 hours delivery time
- $5000 offered price
- $4200 cost limit

### Diagnostic Results

| Section | Min Cost | Min Time | Time Limit | Issue |
|---------|----------|----------|------------|-------|
| 1 | $721 ✅ | 9.25 hrs | 6.0 hrs | ❌ 3.25 hrs over |
| 2 | $1147 ✅ | 10.02 hrs | 6.0 hrs | ❌ 4.02 hrs over |
| 3 | $888 ✅ | 11.59 hrs | 6.0 hrs | ❌ 5.59 hrs over |

**Diagnosis**: ❌ **TIME INFEASIBLE**
- All sections exceed 6-hour time limit
- Fastest option (Section 1) needs 9.25 hours
- Customer expectation unrealistic

### Solution
Customer needs to:
1. **Increase time limit** to at least 10 hours, OR
2. **Reduce number of tasks** from 5 to 3-4, OR
3. **Accept partial completion** in 6 hours

## Error Message Improvements

### Before
```
Error: 'summary'
```

### After
```
Optimization infeasible (Status: Infeasible). 
Cannot satisfy constraints with current parameters. 
Try: increasing cost limit (current: 4200.0), 
     increasing time limit (current: 6.0), 
     or reducing offered price (current: 5000.0).
```

Much clearer guidance for troubleshooting!

## Testing Infeasibility

### Test Case 1: Time Infeasible ✅
```
Tasks: 5
Time: 6 hours
Cost limit: $4200
Result: Infeasible (needs ~9.25 hours minimum)
```

### Test Case 2: Cost Infeasible
```
Tasks: 10
Time: 50 hours
Cost limit: $500
Result: Infeasible (needs ~$1000+ minimum)
```

### Test Case 3: Feasible ✅
```
Tasks: 5
Time: 15 hours
Cost limit: $4200
Result: Optimal solution found
```

## How to Prevent Infeasibility

### For Customers
1. **Check realistic timeframes**
   - 1-2 hours per task is typical
   - Allow extra time for setup
   - Ask manufacturer for estimates

2. **Set reasonable budgets**
   - Check cost limit with manufacturer
   - Consider complexity of tasks
   - Factor in fixed setup costs

3. **Start small**
   - Test with fewer tasks first
   - Scale up after successful orders
   - Learn typical processing times

### For Manufacturers
1. **Provide guidance**
   - Display typical time per task
   - Show minimum order time
   - List cost ranges

2. **Set realistic defaults**
   - config.json default_cost_limit
   - Capacity constraints
   - Machine availability

3. **Monitor failed orders**
   - Review infeasibility patterns
   - Adjust configuration
   - Provide customer feedback

## Files Modified

### Modified:
- ✅ `app.py` - Enhanced infeasibility detection and error messages

### Created:
- ✅ `test_solver.py` - Direct solver testing tool
- ✅ `diagnose_order.py` - Order feasibility diagnostic tool
- ✅ `INFEASIBILITY_FIX.md` - This documentation

## Running Diagnostics

### Check if order is feasible:
```powershell
# Edit diagnose_order.py to point to your order folder
.\.venv\Scripts\python.exe diagnose_order.py
```

### Test solver directly:
```powershell
# Edit test_solver.py to point to your order folder
.\.venv\Scripts\python.exe test_solver.py
```

### Check Flask console:
Look for debug output:
```
Loading data for order ORD-XXXXXXXX...
Running solver for X tasks...
Solver result keys: ['status1', 'note']
❌ Optimization failed for order ORD-XXXXXXXX:
Optimization infeasible (Status: Infeasible)...
```

## Status

✅ **Issue Fully Resolved**
- Infeasibility properly detected
- Clear error messages provided
- Diagnostic tools available
- Root cause identified (time constraint)
- Solutions documented

## Next Steps for User

**For this specific order (ORD-0937B623)**:
1. Submit new order with **time = 12 hours** (instead of 6)
2. Keep same: 5 tasks, $5000 price, $4200 cost limit
3. Should process successfully ✅

**General recommendations**:
1. Use diagnostic tools before submitting
2. Check manufacturer's typical processing times
3. Allow buffer time for delivery
4. Start with conservative estimates
5. Adjust based on successful orders

---

**Key Takeaway**: The system is working correctly. The order was rightfully rejected because it's physically impossible to complete 5 tasks in 6 hours with the available machines. The customer needs to adjust their expectations.
