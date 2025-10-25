"""
Fix manufacturer configuration by regenerating costs.csv with proper task coverage
"""
import pandas as pd
import os

# Read existing files
sections_df = pd.read_csv('data/sections.csv')
machines_df = pd.read_csv('data/machines.csv')

print("Current configuration:")
print(f"Sections: {len(sections_df)}")
print(f"Machines: {len(machines_df)}")

# Generate costs for 10 tasks per machine with proper structure
max_tasks = 10
costs_data = []

# Base costs per machine (reasonable defaults)
base_costs = {
    (1, 1): 43.0,
    (1, 2): 46.0,
    (1, 3): 49.0,
    (2, 1): 48.0,
    (2, 2): 51.0,
    (2, 3): 54.0,
    (2, 4): 57.0,
    (3, 1): 56.0,
    (3, 2): 59.0,
}

# Generate costs for each machine
for _, machine in machines_df.iterrows():
    section_id = int(machine['section_id'])
    machine_id = int(machine['machine_id'])
    
    # Get base cost or use default
    base_cost = base_costs.get((section_id, machine_id), 50.0)
    
    # Generate for all tasks
    for task_id in range(1, max_tasks + 1):
        # Increase cost by 1.5% per task
        cost = round(base_cost * (1 + 0.015 * (task_id - 1)), 2)
        costs_data.append({
            'section_id': section_id,
            'machine_id': machine_id,
            'task_id': task_id,
            'variable_cost': cost
        })

costs_df = pd.DataFrame(costs_data)
costs_df.to_csv('data/costs.csv', index=False)

print(f"\nGenerated costs.csv with {len(costs_df)} entries")
print(f"Tasks per machine: {max_tasks}")
print(f"Total machines: {len(machines_df)}")

# Create config.json
import json
from datetime import datetime

config = {
    'default_cost_limit': 4200.0,
    'max_tasks': max_tasks,
    'num_sections': len(sections_df),
    'machines_per_section': machines_df.groupby('section_id').size().tolist(),
    'last_updated': datetime.now().isoformat()
}

with open('data/config.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"\nCreated config.json")
print(f"Configuration: {config['num_sections']} sections, machines per section: {config['machines_per_section']}")
print("\n✅ Configuration fixed! You can now submit orders.")
