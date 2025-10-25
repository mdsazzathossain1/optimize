# Combined script generated from notebook
# Installs are commented out; expected that environment has pulp, pandas, numpy, tabulate

import os
import json
import math
import pandas as pd
import numpy as np
import pulp
from tabulate import tabulate

# Setup data directory
base = os.path.join(os.getcwd(), "data")
os.makedirs(base, exist_ok=True)

# RNG and parameters
rng = np.random.default_rng(7)
p = 6  # number of CAD files / parts (customer)
sections = [1,2,3] #(manufacurer)
I = {1:[1,2,3], 2:[1,2,3,4], 3:[1,2]}  # machines per section (manufacurer)

# sections.csv
sections_df = pd.DataFrame({
    "section_id": sections,
    "fixed_setup_cost": [500.0, 900.0, 600.0], #(manufacurer)
    "capacity": [9, 12, 8],                      #manufacturer
    "output_score_optional": [100.0, 130.0, 110.0] #manufacturrer
})
sections_df.to_csv(f"{base}/sections.csv", index=False)

# machines.csv (machine-specific time_per_task and availability)
rows = []
for j in sections:
    for i in I[j]:
        t = round(1.5 + 0.2*j + 0.15*i + 0.05*rng.normal(), 3)
        rows.append(dict(section_id=j, machine_id=i, available=1, time_per_task=t))
# one unavailable machine (example)
for r in rows:
    if r["section_id"]==2 and r["machine_id"]==2:
        r["available"] = 0
machines_df = pd.DataFrame(rows)
machines_df.to_csv(f"{base}/machines.csv", index=False)

# costs.csv (C_ijk)
rows = []
for j in sections:
    for i in I[j]:
        base_cost = 35 + 5*j + 3*i
        for k in range(1, p+1):
            c = round(base_cost*(1 + 0.015*(k-1) + 0.02*rng.normal()), 2)
            rows.append(dict(section_id=j, machine_id=i, task_id=k, variable_cost=c))
costs_df = pd.DataFrame(rows)
costs_df.to_csv(f"{base}/costs.csv", index=False)

# params.csv — NOTE: Cc is the ORDER price (single price for the whole product)
params_df = pd.DataFrame([
    {"param":"num_tasks_p", "value": p},   #customer
    {"param":"order_price_Cc", "value": 6000.0},       # Customer
    {"param":"time_limit_Tdesired", "value": 24.0},     #customer
    {"param":"cost_limit_Cdesired", "value": 4200.0},   #customer
])
params_df.to_csv(f"{base}/params.csv", index=False)

# Optional: times.csv (leave empty to use machine times t_ij)
pd.DataFrame(columns=["section_id","machine_id","task_id","time_per_task"]).to_csv(f"{base}/times.csv", index=False)

print("Wrote CSVs to", base)
print(sections_df)
print(machines_df)
print(costs_df.head(24))
print(params_df)

# ---------- Load function ----------

def load_data_from_csv(base_path="./data"):
    sections_df = pd.read_csv(f"{base_path}/sections.csv")
    machines_df = pd.read_csv(f"{base_path}/machines.csv")
    costs_df    = pd.read_csv(f"{base_path}/costs.csv")
    params_df   = pd.read_csv(f"{base_path}/params.csv")

    # Params — robustly find order price key
    param_map = {str(r["param"]).strip(): float(r["value"]) for _, r in params_df.iterrows()}
    p = int(param_map["num_tasks_p"])
    # accept either of these names; interpret as TOTAL order price
    Cc = float(param_map.get("order_price_Cc", param_map.get("customer_price_per_unit_Cc", None)))
    if Cc is None:
        raise ValueError("params.csv must contain 'order_price_Cc' (total order price).")
    T_desired = float(param_map["time_limit_Tdesired"])
    C_desired = float(param_map["cost_limit_Cdesired"])

    sections = [int(x) for x in sections_df["section_id"].tolist()]
    I = {int(j): [int(i) for i in machines_df[machines_df.section_id==j]["machine_id"].tolist()] for j in sections}

    f = {int(r.section_id): float(r.fixed_setup_cost) for _, r in sections_df.iterrows()}
    Cap = {int(r.section_id): int(r.capacity) for _, r in sections_df.iterrows()}
    O = {}
    if "output_score_optional" in sections_df.columns:
        for _, r in sections_df.iterrows():
            if pd.notna(r["output_score_optional"]):
                O[int(r.section_id)] = float(r["output_score_optional"])

    A = {(int(r.section_id), int(r.machine_id)): int(r.available) for _, r in machines_df.iterrows()}

    # Times: prefer task-specific if present
    t_ijk, t_ij = None, None
    times_path = f"{base_path}/times.csv"
    if os.path.exists(times_path):
        tmp = pd.read_csv(times_path)
        if not tmp.empty:
            t_ijk = {(int(r.section_id), int(r.machine_id), int(r.task_id)): float(r.time_per_task)
                     for _, r in tmp.iterrows()}
    if t_ijk is None:
        t_ij = {(int(r.section_id), int(r.machine_id)): float(r.time_per_task) for _, r in machines_df.iterrows()}

    C_var = {(int(r.section_id), int(r.machine_id), int(r.task_id)): float(r.variable_cost)
             for _, r in costs_df.iterrows()}

    return dict(p=p, Cc=Cc, T_desired=T_desired, C_desired=C_desired,
                sections=sections, I=I, f=f, Cap=Cap, O=O, A=A, t_ij=t_ij, t_ijk=t_ijk, C_var=C_var)

DATA = load_data_from_csv("./data")
print("Loaded keys:", list(DATA.keys()))

# ---------- Solver function ----------

def solve_two_stage_order_price(DATA, tiny_tie_break=1e-3, msg=False):
    p = int(DATA["p"]); Cc = float(DATA["Cc"]); T_desired = float(DATA["T_desired"]); C_desired = float(DATA["C_desired"])
    sections = list(map(int, DATA["sections"]))
    I = {int(j): [int(i) for i in DATA["I"][j]] for j in sections}
    f = {int(j): float(DATA["f"][j]) for j in sections}
    Cap = {int(j): int(DATA["Cap"][j]) for j in sections}
    O = {int(j): float(DATA["O"].get(j, 0.0)) for j in sections}
    A = {(int(j), int(i)): int(v) for (j,i), v in DATA["A"].items()}
    t_ij = DATA["t_ij"]; t_ijk = DATA["t_ijk"]
    C_var = {(int(j), int(i), int(k)): float(v) for (j,i,k), v in DATA["C_var"].items()}

    tasks = list(range(1, p+1))
    BIG_M = 1e6

    # ---------- Stage 1: Max Profit ----------
    m1 = pulp.LpProblem("Stage1_MaxProfit", pulp.LpMaximize)
    X = pulp.LpVariable.dicts("X", sections, lowBound=0, upBound=1, cat=pulp.LpBinary)
    Y = {(j,i,k): pulp.LpVariable(f"Y_{j}_{i}_{k}", lowBound=0, upBound=1, cat=pulp.LpBinary)
         for j in sections for i in I[j] for k in tasks}
    T = {j: pulp.LpVariable(f"T_{j}", lowBound=0) for j in sections}

    # Order-level revenue (single price for the whole order)
    revenue = pulp.lpSum([X[j]*Cc for j in sections])
    var_cost = pulp.lpSum([C_var[(j,i,k)]*Y[(j,i,k)] for j in sections for i in I[j] for k in tasks])
    setup_cost = pulp.lpSum([f[j]*X[j] for j in sections])
    m1 += revenue - (var_cost + setup_cost)

    # Choose exactly one section
    m1 += pulp.lpSum([X[j] for j in sections]) == 1

    # Time definition + cap
    for j in sections:
        if t_ijk:
            m1 += T[j] >= pulp.lpSum([t_ijk[(j,i,k)]*Y[(j,i,k)] for i in I[j] for k in tasks])
        else:
            m1 += T[j] >= pulp.lpSum([t_ij[(j,i)]*Y[(j,i,k)] for i in I[j] for k in tasks])
        m1 += T[j] <= T_desired * X[j]

    # Cost & capacity caps (gated)
    for j in sections:
        m1 += (pulp.lpSum([C_var[(j,i,k)]*Y[(j,i,k)] for i in I[j] for k in tasks]) + f[j]
               <= C_desired + BIG_M*(1 - X[j]))
        m1 += pulp.lpSum([Y[(j,i,k)] for i in I[j] for k in tasks]) \
               <= Cap[j] + BIG_M*(1 - X[j])

        for i in I[j]:
            for k in tasks:
                m1 += Y[(j,i,k)] <= X[j]
                m1 += Y[(j,i,k)] <= A[(j,i)]

    # Every part must be assigned exactly once in the chosen section
    for j in sections:
        for k in tasks:
            m1 += pulp.lpSum([Y[(j,i,k)] for i in I[j]]) == X[j]

    _ = m1.solve(pulp.PULP_CBC_CMD(msg=msg))
    status1 = pulp.LpStatus[m1.status]
    if status1 != "Optimal":
        return {"status1": status1, "note": "Stage 1 not optimal or infeasible."}

    profit1 = pulp.value(m1.objective)

    # ---------- Stage 2: Min Time (lock profit) ----------
    m2 = pulp.LpProblem("Stage2_MinTime", pulp.LpMinimize)
    X2 = pulp.LpVariable.dicts("X", sections, lowBound=0, upBound=1, cat=pulp.LpBinary)
    Y2 = {(j,i,k): pulp.LpVariable(f"Y_{j}_{i}_{k}", lowBound=0, upBound=1, cat=pulp.LpBinary)
          for j in sections for i in I[j] for k in tasks}
    T2 = {j: pulp.LpVariable(f"T_{j}", lowBound=0) for j in sections}

    m2 += (pulp.lpSum([T2[j] for j in sections])
           + tiny_tie_break * pulp.lpSum([Y2[(j,i,k)] for j in sections for i in I[j] for k in tasks]))
    m2 += pulp.lpSum([X2[j] for j in sections]) == 1

    for j in sections:
        if t_ijk:
            m2 += T2[j] >= pulp.lpSum([t_ijk[(j,i,k)]*Y2[(j,i,k)] for i in I[j] for k in tasks])
        else:
            m2 += T2[j] >= pulp.lpSum([t_ij[(j,i)]*Y2[(j,i,k)] for i in I[j] for k in tasks])
        m2 += T2[j] <= T_desired * X2[j]

        m2 += (pulp.lpSum([C_var[(j,i,k)]*Y2[(j,i,k)] for i in I[j] for k in tasks]) + f[j]
               <= C_desired + BIG_M*(1 - X2[j]))
        m2 += pulp.lpSum([Y2[(j,i,k)] for i in I[j] for k in tasks]) \
               <= Cap[j] + BIG_M*(1 - X2[j])

        for i in I[j]:
            for k in tasks:
                m2 += Y2[(j,i,k)] <= X2[j]
                m2 += Y2[(j,i,k)] <= A[(j,i)]

    # Profit lock to Stage-1 optimum
    eps = 1e-6
    profit2 = (pulp.lpSum([X2[j]*Cc for j in sections])
               - (pulp.lpSum([C_var[(j,i,k)]*Y2[(j,i,k)] for j in sections for i in I[j] for k in tasks])
                  + pulp.lpSum([f[j]*X2[j] for j in sections])))
    m2 += profit2 >= profit1 - eps
    m2 += profit2 <= profit1 + eps

    # Same "every part once in the chosen section"
    for j in sections:
        for k in tasks:
            m2 += pulp.lpSum([Y2[(j,i,k)] for i in I[j]]) == X2[j]

    _ = m2.solve(pulp.PULP_CBC_CMD(msg=msg))
    status2 = pulp.LpStatus[m2.status]

    # Extract solution
    chosen = [j for j in sections if pulp.value(X2[j]) > 0.5][0]
    used = [(i,k) for i in I[chosen] for k in tasks if pulp.value(Y2[(chosen,i,k)]) > 0.5]
    n_assgn = len(used)
    n_machs = len({i for i,_ in used})
    T_val = float(pulp.value(T2[chosen]))

    revenue_val = float(Cc)  # order-level price
    var_cost_val = float(sum(DATA["C_var"][(chosen,i,k)]*pulp.value(Y2[(chosen,i,k)]) for i in I[chosen] for k in tasks))
    cost_val = var_cost_val + f[chosen]
    profit_val = revenue_val - cost_val

    Oj = O.get(chosen, 0.0)
    eff_proxy = (Oj/(T_val*n_assgn)) if (Oj>0 and T_val>0 and n_assgn>0) else None

    assign_rows = []
    for (i,k) in sorted(used, key=lambda x:(x[0], x[1])):
        assign_rows.append(dict(
            section_id=chosen,
            machine_id=i,
            task_id=k,
            var_cost=DATA["C_var"][(chosen,i,k)],
            time=(DATA["t_ijk"][(chosen,i,k)] if t_ijk else DATA["t_ij"][(chosen,i)])
        ))
    assign_df = pd.DataFrame(assign_rows)

    summary = dict(
        status1=status1, status2=status2,
        chosen_section=int(chosen),
        total_revenue=float(revenue_val),
        total_cost=float(cost_val),
        total_profit=float(profit_val),
        time=float(T_val),
        time_limit=float(T_desired),
        cost_limit=float(C_desired),
        assignments=int(n_assgn),
        active_machines=int(n_machs),
        tasks_enforced=p,
        tasks_scheduled=p,  # all parts enforced
        capacity_of_chosen=int(Cap[chosen]),
        efficiency_proxy=(float(eff_proxy) if eff_proxy is not None else None)
    )
    return {"summary": summary, "assignments": assign_df}

# ---------- Run solver and save outputs ----------
RES = solve_two_stage_order_price(DATA, tiny_tie_break=1e-3, msg=False)

print(tabulate(RES["summary"].items(), headers=["Metric","Value"], tablefmt="github"))
print(RES["assignments"].head(50))

# Save outputs to files for download
with open(os.path.join(os.getcwd(), "solution_summary.json"), "w") as f:
    json.dump(RES["summary"], f, indent=2)
RES["assignments"].to_csv(os.path.join(os.getcwd(), "solution_assignments.csv"), index=False)

print("Saved:")
print("- ", os.path.join(os.getcwd(), "solution_summary.json"))
print("- ", os.path.join(os.getcwd(), "solution_assignments.csv"))
