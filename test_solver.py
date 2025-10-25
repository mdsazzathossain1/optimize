"""
Test the solver directly with order data to diagnose the issue
"""
import sys
sys.path.insert(0, '.')

from solver import load_data_from_csv, solve_two_stage_order_price

# Test with the failed order
order_path = 'orders/ORD-0937B623'

print("Loading data...")
DATA = load_data_from_csv(order_path)

print("\nData summary:")
print(f"  Tasks (p): {DATA['p']}")
print(f"  Order price (Cc): {DATA['Cc']}")
print(f"  Time limit: {DATA['T_desired']}")
print(f"  Cost limit: {DATA['C_desired']}")
print(f"  Sections: {DATA['sections']}")
print(f"  Machines per section: {DATA['I']}")

print("\nChecking cost data...")
C_var = DATA['C_var']
print(f"  Total cost entries: {len(C_var)}")

# Check if all required costs exist
missing_costs = []
for section in DATA['sections']:
    for machine in DATA['I'][section]:
        for task in range(1, DATA['p'] + 1):
            if (section, machine, task) not in C_var:
                missing_costs.append((section, machine, task))

if missing_costs:
    print(f"\n❌ MISSING COSTS: {len(missing_costs)} entries")
    print("  First 10 missing:")
    for entry in missing_costs[:10]:
        print(f"    Section {entry[0]}, Machine {entry[1]}, Task {entry[2]}")
else:
    print("  ✅ All costs present")

print("\nRunning solver...")
try:
    result = solve_two_stage_order_price(DATA, tiny_tie_break=1e-3, msg=True)
    print(f"\n✅ Solver succeeded!")
    print(f"  Result type: {type(result)}")
    print(f"  Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
    if isinstance(result, dict) and 'summary' in result:
        print(f"\n  Summary:")
        for key, value in result['summary'].items():
            print(f"    {key}: {value}")
except Exception as e:
    print(f"\n❌ Solver failed: {e}")
    import traceback
    traceback.print_exc()
