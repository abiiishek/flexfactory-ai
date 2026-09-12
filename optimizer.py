from ortools.sat.python import cp_model

def optimize_production(target_units, machines_status):
    model = cp_model.CpModel()
    
    # Decision Variables
    allocations = {}
    for m_id in machines_status:
        cap = machines_status[m_id]['capacity']
        allocations[m_id] = model.NewIntVar(0, cap, f'alloc_{m_id}')
        
    # Constraint: Total allocated units must equal target
    model.Add(sum(allocations.values()) == target_units)
    
    # Objective: Minimize total energy cost with anomaly penalties
    total_energy_cost = []
    for m_id, info in machines_status.items():
        weight = int(info['sec'] * 1000)
        if not info['is_healthy']:
            weight *= 2  # Penalty for abnormal machines
        total_energy_cost.append(allocations[m_id] * weight)
        
    model.Minimize(sum(total_energy_cost))
    
    # Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return {m_id: solver.Value(allocations[m_id]) for m_id in machines_status}
    else:
        return None

if __name__ == "__main__":
    sample_status = {
        'Machine_A': {'capacity': 500, 'sec': 0.20, 'is_healthy': True},
        'Machine_B': {'capacity': 500, 'sec': 0.38, 'is_healthy': False},
        'Machine_C': {'capacity': 400, 'sec': 0.24, 'is_healthy': True}
    }
    print("Optimization Test Result:")
    print(optimize_production(1000, sample_status))