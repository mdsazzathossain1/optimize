"""
Diagnose why order ORD-0937B623 is infeasible
"""
import pandas as pd

order_path = 'orders/ORD-0937B623'

# Load order data
params = pd.read_csv(f'{order_path}/params.csv')
costs = pd.read_csv(f'{order_path}/costs.csv')
machines = pd.read_csv(f'{order_path}/machines.csv')
sections = pd.read_csv(f'{order_path}/sections.csv')

print("=" * 60)
print("ORDER PARAMETERS")
print("=" * 60)
for _, row in params.iterrows():
    print(f"  {row['param']}: {row['value']}")

num_tasks = int(params[params['param'] == 'num_tasks_p']['value'].values[0])
cost_limit = float(params[params['param'] == 'cost_limit_Cdesired']['value'].values[0])
time_limit = float(params[params['param'] == 'time_limit_Tdesired']['value'].values[0])
order_price = float(params[params['param'] == 'order_price_Cc']['value'].values[0])

print("\n" + "=" * 60)
print("COST ANALYSIS")
print("=" * 60)

# For each section, calculate minimum cost
for section_id in sections['section_id']:
    print(f"\nSection {section_id}:")
    section_fixed = sections[sections['section_id'] == section_id]['fixed_setup_cost'].values[0]
    print(f"  Fixed setup cost: ${section_fixed}")
    
    # Get machines in this section
    section_machines = machines[machines['section_id'] == section_id]
    available_machines = section_machines[section_machines['available'] == 1]
    
    print(f"  Machines: {len(section_machines)} total, {len(available_machines)} available")
    
    if len(available_machines) == 0:
        print(f"  ❌ NO AVAILABLE MACHINES - Cannot use this section!")
        continue
    
    # Calculate minimum variable cost for this section
    min_var_cost = 0
    for task_id in range(1, num_tasks + 1):
        # Find minimum cost across available machines for this task
        task_costs = []
        for _, machine in available_machines.iterrows():
            machine_id = machine['machine_id']
            cost_row = costs[(costs['section_id'] == section_id) & 
                           (costs['machine_id'] == machine_id) & 
                           (costs['task_id'] == task_id)]
            if not cost_row.empty:
                task_costs.append(cost_row['variable_cost'].values[0])
        
        if task_costs:
            min_task_cost = min(task_costs)
            min_var_cost += min_task_cost
            print(f"    Task {task_id}: min cost = ${min_task_cost:.2f}")
    
    total_min_cost = section_fixed + min_var_cost
    print(f"  Total minimum cost: ${total_min_cost:.2f} (fixed ${section_fixed} + variable ${min_var_cost:.2f})")
    
    if total_min_cost <= cost_limit:
        print(f"  ✅ Within cost limit (${cost_limit})")
    else:
        print(f"  ❌ EXCEEDS cost limit by ${total_min_cost - cost_limit:.2f}")
    
    # Check profitability
    profit = order_price - total_min_cost
    print(f"  Profit potential: ${profit:.2f} (revenue ${order_price} - cost ${total_min_cost:.2f})")
    if profit < 0:
        print(f"  ❌ UNPROFITABLE!")

print("\n" + "=" * 60)
print("TIME ANALYSIS")
print("=" * 60)

for section_id in sections['section_id']:
    print(f"\nSection {section_id}:")
    section_machines = machines[machines['section_id'] == section_id]
    available_machines = section_machines[section_machines['available'] == 1]
    
    if len(available_machines) == 0:
        print(f"  Skipped (no available machines)")
        continue
    
    # Calculate minimum time
    min_time = 0
    for task_id in range(1, num_tasks + 1):
        # Find fastest available machine for this task
        task_times = []
        for _, machine in available_machines.iterrows():
            task_times.append(machine['time_per_task'])
        
        if task_times:
            min_task_time = min(task_times)
            min_time += min_task_time
    
    print(f"  Minimum time: {min_time:.2f} hours")
    
    if min_time <= time_limit:
        print(f"  ✅ Within time limit ({time_limit} hours)")
    else:
        print(f"  ❌ EXCEEDS time limit by {min_time - time_limit:.2f} hours")

print("\n" + "=" * 60)
print("DIAGNOSIS")
print("=" * 60)

# Check each constraint
issues = []

for section_id in sections['section_id']:
    section_machines = machines[machines['section_id'] == section_id]
    available_machines = section_machines[section_machines['available'] == 1]
    
    if len(available_machines) == 0:
        issues.append(f"Section {section_id}: No available machines")
        continue
    
    section_fixed = sections[sections['section_id'] == section_id]['fixed_setup_cost'].values[0]
    
    # Calculate minimum cost
    min_var_cost = 0
    for task_id in range(1, num_tasks + 1):
        task_costs = []
        for _, machine in available_machines.iterrows():
            machine_id = machine['machine_id']
            cost_row = costs[(costs['section_id'] == section_id) & 
                           (costs['machine_id'] == machine_id) & 
                           (costs['task_id'] == task_id)]
            if not cost_row.empty:
                task_costs.append(cost_row['variable_cost'].values[0])
        if task_costs:
            min_var_cost += min(task_costs)
    
    total_cost = section_fixed + min_var_cost
    
    if total_cost > cost_limit:
        issues.append(f"Section {section_id}: Min cost ${total_cost:.2f} > limit ${cost_limit}")

if issues:
    print("\n❌ INFEASIBILITY CAUSES:")
    for issue in issues:
        print(f"  • {issue}")
    print(f"\n💡 SOLUTIONS:")
    print(f"  1. Increase cost limit (currently ${cost_limit})")
    print(f"  2. Reduce number of tasks (currently {num_tasks})")
    print(f"  3. Increase offered price (currently ${order_price})")
else:
    print("\n✅ All constraints appear satisfiable")
    print("   Problem may be with capacity or time constraints")
