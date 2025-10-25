"""
Flask web application for Manufacturing Order Management System
- Customer portal: submit orders with CAD files
- Admin portal: manage manufacturer data and view optimization results
"""
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import pandas as pd

from solver import load_data_from_csv, solve_two_stage_order_price

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For flash messages
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORDERS_DIR = os.path.join(BASE_DIR, "orders")
MANUFACTURER_DATA_DIR = os.path.join(BASE_DIR, "data")
ALLOWED_EXTENSIONS = {'pdf', 'dwg', 'dxf', 'step', 'stp', 'igs', 'iges', 'stl', 'jpg', 'png', 'zip', 'rar'}

os.makedirs(ORDERS_DIR, exist_ok=True)
os.makedirs(MANUFACTURER_DATA_DIR, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== CUSTOMER PORTAL ====================

@app.route('/')
def index():
    """Landing page - customer order submission"""
    # Load manufacturer config to show compatible constraints
    config_info = {}
    try:
        if os.path.exists(os.path.join(MANUFACTURER_DATA_DIR, 'config.json')):
            with open(os.path.join(MANUFACTURER_DATA_DIR, 'config.json'), 'r') as f:
                mfg_config = json.load(f)
                config_info = {
                    'max_tasks': mfg_config.get('max_tasks', 10),
                    'num_sections': mfg_config.get('num_sections', 3),
                    'cost_limit': mfg_config.get('default_cost_limit', 999999)
                }
    except:
        # Use defaults if config doesn't exist
        config_info = {
            'max_tasks': 10,
            'num_sections': 3,
            'cost_limit': 999999
        }
    
    return render_template('customer_form.html', config=config_info)


@app.route('/submit_order', methods=['POST'])
def submit_order():
    """Handle customer order submission and automatically run optimization"""
    try:
        # Validate against manufacturer configuration
        num_tasks_requested = int(request.form.get('num_cad_files', 0))
        
        # Load manufacturer config for validation
        mfg_config = {}
        if os.path.exists(os.path.join(MANUFACTURER_DATA_DIR, 'config.json')):
            with open(os.path.join(MANUFACTURER_DATA_DIR, 'config.json'), 'r') as f:
                mfg_config = json.load(f)
        
        max_tasks = mfg_config.get('max_tasks', 10)
        
        # Validate task count
        if num_tasks_requested > max_tasks:
            flash(f'Error: Number of tasks ({num_tasks_requested}) exceeds manufacturer capacity ({max_tasks}). Please reduce the number of parts.', 'error')
            return redirect(url_for('index'))
        
        # Check if manufacturer configuration exists
        if not all([os.path.exists(os.path.join(MANUFACTURER_DATA_DIR, f)) 
                   for f in ['sections.csv', 'machines.csv', 'costs.csv']]):
            flash('Error: Manufacturer has not configured the system yet. Please contact the manufacturer.', 'error')
            return redirect(url_for('index'))
        
        # Generate unique order ID
        order_id = request.form.get('order_id') or f"ORD-{uuid.uuid4().hex[:8].upper()}"
        order_dir = os.path.join(ORDERS_DIR, order_id)
        os.makedirs(order_dir, exist_ok=True)
        
        # Save uploaded CAD files
        cad_files = request.files.getlist('cad_files')
        cad_filenames = []
        for file in cad_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(order_dir, filename))
                cad_filenames.append(filename)
        
        # Save additional documents
        docs = request.files.getlist('additional_docs')
        doc_filenames = []
        for doc in docs:
            if doc and allowed_file(doc.filename):
                filename = secure_filename(doc.filename)
                doc.save(os.path.join(order_dir, filename))
                doc_filenames.append(filename)
        
        # Collect customer data
        customer_data = {
            'order_id': order_id,
            'customer_name': request.form.get('customer_name'),
            'num_cad_files': num_tasks_requested,
            'product_description': request.form.get('product_description'),
            'quantity': request.form.get('quantity'),
            'desired_delivery_time': float(request.form.get('desired_delivery_time')),
            'offered_price': float(request.form.get('offered_price')),
            'material_specs': request.form.get('material_specs'),
            'surface_finish': request.form.get('surface_finish'),
            'testing_requirements': request.form.get('testing_requirements'),
            'certifications': request.form.get('certifications'),
            'nda_confirmed': request.form.get('nda_confirmed') == 'on',
            'special_instructions': request.form.get('special_instructions'),
            'cad_files': cad_filenames,
            'additional_docs': doc_filenames,
            'submission_timestamp': datetime.now().isoformat(),
            'status': 'processing'
        }
        
        # Save customer data as JSON
        with open(os.path.join(order_dir, 'customer_data.json'), 'w') as f:
            json.dump(customer_data, f, indent=2)
        
        # Load default cost limit from manufacturer config
        default_cost_limit = mfg_config.get('default_cost_limit', 999999)
        
        # Create params.csv for this order
        params_df = pd.DataFrame([
            {"param": "num_tasks_p", "value": num_tasks_requested},
            {"param": "order_price_Cc", "value": customer_data['offered_price']},
            {"param": "time_limit_Tdesired", "value": customer_data['desired_delivery_time']},
            {"param": "cost_limit_Cdesired", "value": default_cost_limit}
        ])
        params_df.to_csv(os.path.join(order_dir, 'params.csv'), index=False)
        
        # AUTOMATICALLY RUN OPTIMIZATION
        try:
            # Copy manufacturer data to order folder
            for filename in ['sections.csv', 'machines.csv', 'costs.csv', 'times.csv']:
                src = os.path.join(MANUFACTURER_DATA_DIR, filename)
                dst = os.path.join(order_dir, filename)
                if os.path.exists(src):
                    pd.read_csv(src).to_csv(dst, index=False)
            
            # Run optimization
            print(f"Loading data for order {order_id}...")
            DATA = load_data_from_csv(order_dir)
            print(f"Running solver for {DATA['p']} tasks...")
            result = solve_two_stage_order_price(DATA, tiny_tie_break=1e-3, msg=False)
            
            # Debug output
            print(f"Solver result type: {type(result)}")
            print(f"Solver result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            # Check if result is valid
            if result is None:
                raise ValueError("Solver returned None. Check optimization constraints.")
            if not isinstance(result, dict):
                raise ValueError(f"Solver returned {type(result)} instead of dict.")
            
            # Check if optimization was infeasible
            if 'summary' not in result:
                # Solver returned early due to infeasibility
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
            
            if 'assignments' not in result:
                raise ValueError(f"Solver result missing 'assignments' key. Keys present: {list(result.keys())}")
            
            # Save results
            with open(os.path.join(order_dir, 'solution_summary.json'), 'w') as f:
                json.dump(result['summary'], f, indent=2)
            
            result['assignments'].to_csv(os.path.join(order_dir, 'solution_assignments.csv'), index=False)
            
            # Update status to processed
            customer_data['status'] = 'processed'
            customer_data['processing_timestamp'] = datetime.now().isoformat()
            with open(os.path.join(order_dir, 'customer_data.json'), 'w') as f:
                json.dump(customer_data, f, indent=2)
            
            print(f"✅ Order {order_id} processed successfully!")
                
        except Exception as opt_error:
            # If optimization fails, mark as failed but still save the order
            import traceback
            error_details = f"{str(opt_error)}\n\nTraceback:\n{traceback.format_exc()}"
            print(f"❌ Optimization failed for order {order_id}:")
            print(error_details)
            
            customer_data['status'] = 'failed'
            customer_data['error_message'] = str(opt_error)
            customer_data['error_details'] = error_details
            with open(os.path.join(order_dir, 'customer_data.json'), 'w') as f:
                json.dump(customer_data, f, indent=2)
        
        flash(f'Order {order_id} submitted successfully!', 'success')
        return render_template('customer_success.html', order_id=order_id)
        
    except Exception as e:
        flash(f'Error submitting order: {str(e)}', 'error')
        return redirect(url_for('index'))


# ==================== ADMIN PORTAL ====================

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard - view orders and manage manufacturer data"""
    # List all orders
    orders = []
    if os.path.exists(ORDERS_DIR):
        for order_id in os.listdir(ORDERS_DIR):
            order_path = os.path.join(ORDERS_DIR, order_id, 'customer_data.json')
            if os.path.exists(order_path):
                with open(order_path, 'r') as f:
                    order_data = json.load(f)
                    orders.append(order_data)
    
    # Load current manufacturer config if exists
    config_exists = all([
        os.path.exists(os.path.join(MANUFACTURER_DATA_DIR, f))
        for f in ['sections.csv', 'machines.csv', 'costs.csv']
    ])
    
    return render_template('admin_dashboard.html', orders=orders, config_exists=config_exists)


@app.route('/admin/config', methods=['GET', 'POST'])
def admin_config():
    """Manage manufacturer configuration with dynamic form inputs"""
    if request.method == 'POST':
        try:
            # Get dynamic structure configuration
            num_sections = int(request.form.get('num_sections', 3))
            machines_per_section = [int(x.strip()) for x in request.form.get('machines_per_section', '3,4,2').split(',')]
            max_tasks = int(request.form.get('max_tasks', 10))
            
            if len(machines_per_section) != num_sections:
                flash('Number of machine counts must match number of sections', 'error')
                return redirect(url_for('admin_config'))
            
            # Build sections data from dynamic form
            sections_data = []
            for section_id in range(1, num_sections + 1):
                output_score = request.form.get(f'section_{section_id}_output_score')
                sections_data.append({
                    "section_id": section_id,
                    "fixed_setup_cost": float(request.form.get(f'section_{section_id}_fixed_cost')),
                    "capacity": int(request.form.get(f'section_{section_id}_capacity')),
                    "output_score_optional": float(output_score) if output_score else None
                })
            sections_df = pd.DataFrame(sections_data)
            sections_df.to_csv(os.path.join(MANUFACTURER_DATA_DIR, 'sections.csv'), index=False)
            
            # Build machines data from dynamic form
            machines_data = []
            base_costs = {}
            
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
                    # Collect base costs
                    base_costs[(section_id, machine_id)] = float(request.form.get(f'machine_{machine_key}_cost'))
            
            machines_df = pd.DataFrame(machines_data)
            machines_df.to_csv(os.path.join(MANUFACTURER_DATA_DIR, 'machines.csv'), index=False)
            
            # Build costs data - auto-generate for all tasks with small variations
            costs_data = []
            for (section_id, machine_id), base_cost in base_costs.items():
                for task_id in range(1, max_tasks + 1):
                    # Add small variation: increase 1.5% per task
                    cost = round(base_cost * (1 + 0.015 * (task_id - 1)), 2)
                    costs_data.append({
                        "section_id": section_id,
                        "machine_id": machine_id,
                        "task_id": task_id,
                        "variable_cost": cost
                    })
            
            costs_df = pd.DataFrame(costs_data)
            costs_df.to_csv(os.path.join(MANUFACTURER_DATA_DIR, 'costs.csv'), index=False)
            
            # Create empty times.csv
            pd.DataFrame(columns=["section_id", "machine_id", "task_id", "time_per_task"]).to_csv(
                os.path.join(MANUFACTURER_DATA_DIR, 'times.csv'), index=False
            )
            
            # Save configuration metadata
            config_data = {
                'default_cost_limit': float(request.form.get('default_cost_limit')),
                'max_tasks': max_tasks,
                'num_sections': num_sections,
                'machines_per_section': machines_per_section,
                'last_updated': datetime.now().isoformat()
            }
            with open(os.path.join(MANUFACTURER_DATA_DIR, 'config.json'), 'w') as f:
                json.dump(config_data, f, indent=2)
            
            flash('Manufacturer configuration saved successfully! This will be used for all new orders.', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            flash(f'Error saving configuration: {str(e)}', 'error')
            import traceback
            traceback.print_exc()
    
    # Load existing config if available
    config = {}
    try:
        if os.path.exists(os.path.join(MANUFACTURER_DATA_DIR, 'sections.csv')):
            config['sections'] = pd.read_csv(os.path.join(MANUFACTURER_DATA_DIR, 'sections.csv')).to_dict('records')
        if os.path.exists(os.path.join(MANUFACTURER_DATA_DIR, 'machines.csv')):
            machines_df = pd.read_csv(os.path.join(MANUFACTURER_DATA_DIR, 'machines.csv'))
            config['machines'] = machines_df.to_dict('records')
            # Create indexed machine dict for easy lookup in template
            config['machines_dict'] = {}
            for _, row in machines_df.iterrows():
                key = f"{int(row['section_id'])},{int(row['machine_id'])}"
                config['machines_dict'][key] = row.to_dict()
        if os.path.exists(os.path.join(MANUFACTURER_DATA_DIR, 'costs.csv')):
            costs_df = pd.read_csv(os.path.join(MANUFACTURER_DATA_DIR, 'costs.csv'))
            config['costs'] = costs_df.to_dict('records')
            # Get base costs (from task 1 for each machine)
            config['base_costs'] = {}
            for _, row in costs_df[costs_df['task_id'] == 1].iterrows():
                key = f"{int(row['section_id'])},{int(row['machine_id'])}"
                config['base_costs'][key] = row['variable_cost']
        if os.path.exists(os.path.join(MANUFACTURER_DATA_DIR, 'config.json')):
            with open(os.path.join(MANUFACTURER_DATA_DIR, 'config.json'), 'r') as f:
                settings = json.load(f)
                config['settings'] = settings
                # Extract structure info for form generation
                config['structure'] = {
                    'num_sections': settings.get('num_sections', 3),
                    'machines_per_section': ','.join(map(str, settings.get('machines_per_section', [3, 4, 2])))
                }
    except Exception as e:
        print(f"Error loading config: {e}")
        import traceback
        traceback.print_exc()
    
    return render_template('admin_config_dynamic.html', config=config)


@app.route('/admin/process_order/<order_id>', methods=['POST'])
def process_order(order_id):
    """Run optimization for a specific order"""
    try:
        order_dir = os.path.join(ORDERS_DIR, order_id)
        
        # Update cost_limit if provided
        cost_limit = request.form.get('cost_limit')
        if cost_limit:
            params_path = os.path.join(order_dir, 'params.csv')
            params_df = pd.read_csv(params_path)
            params_df.loc[params_df['param'] == 'cost_limit_Cdesired', 'value'] = float(cost_limit)
            params_df.to_csv(params_path, index=False)
        
        # Copy manufacturer data to order folder
        for filename in ['sections.csv', 'machines.csv', 'costs.csv', 'times.csv']:
            src = os.path.join(MANUFACTURER_DATA_DIR, filename)
            dst = os.path.join(order_dir, filename)
            if os.path.exists(src):
                pd.read_csv(src).to_csv(dst, index=False)
        
        # Load data and run solver
        DATA = load_data_from_csv(order_dir)
        result = solve_two_stage_order_price(DATA, tiny_tie_break=1e-3, msg=False)
        
        # Save results
        with open(os.path.join(order_dir, 'solution_summary.json'), 'w') as f:
            json.dump(result['summary'], f, indent=2)
        
        result['assignments'].to_csv(os.path.join(order_dir, 'solution_assignments.csv'), index=False)
        
        # Update order status
        with open(os.path.join(order_dir, 'customer_data.json'), 'r') as f:
            customer_data = json.load(f)
        customer_data['status'] = 'processed'
        customer_data['processing_timestamp'] = datetime.now().isoformat()
        with open(os.path.join(order_dir, 'customer_data.json'), 'w') as f:
            json.dump(customer_data, f, indent=2)
        
        flash(f'Order {order_id} processed successfully!', 'success')
        return redirect(url_for('view_results', order_id=order_id))
        
    except Exception as e:
        flash(f'Error processing order: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/results/<order_id>')
def view_results(order_id):
    """View optimization results for an order"""
    order_dir = os.path.join(ORDERS_DIR, order_id)
    
    # Load customer data
    with open(os.path.join(order_dir, 'customer_data.json'), 'r') as f:
        customer_data = json.load(f)
    
    # Load solution if exists
    solution = None
    assignments = None
    summary_path = os.path.join(order_dir, 'solution_summary.json')
    assignments_path = os.path.join(order_dir, 'solution_assignments.csv')
    
    if os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            solution = json.load(f)
    
    if os.path.exists(assignments_path):
        assignments = pd.read_csv(assignments_path).to_dict('records')
    
    return render_template('admin_results.html', 
                         order_id=order_id,
                         customer_data=customer_data,
                         solution=solution,
                         assignments=assignments)


@app.route('/admin/download/<order_id>/<filename>')
def download_file(order_id, filename):
    """Download files from order folder"""
    order_dir = os.path.join(ORDERS_DIR, order_id)
    return send_from_directory(order_dir, filename, as_attachment=True)


if __name__ == '__main__':
    print("=" * 60)
    print("Manufacturing Order Management System")
    print("=" * 60)
    print("Customer Portal: http://localhost:5000/")
    print("Admin Portal:    http://localhost:5000/admin")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
