from flask import Flask, render_template, request, jsonify, send_file
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

app = Flask(__name__)

# --- ENGINEERING LOGIC (Copied from main.py) ---
def calculate_reactions(loads, length):
    moment_sum_a = 0
    total_load = 0
    for load in loads:
        if load['type'] == 'point':
            P = float(load['mag'])
            x = float(load['pos'])
            moment_sum_a += P * x
            total_load += P
        elif load['type'] == 'udl':
            w = float(load['mag'])
            x1 = float(load['start'])
            x2 = float(load['end'])
            span = x2 - x1
            total_w = w * span
            centroid = x1 + (span / 2)
            moment_sum_a += total_w * centroid
            total_load += total_w
    rb = moment_sum_a / length
    ra = total_load - rb
    return ra, rb

def calculate_arrays(loads, ra, length, num_points=500):
    x_vals = np.linspace(0, length, num_points)
    shear_vals = []
    moment_vals = []
    for x in x_vals:
        v = ra
        m = ra * x
        for load in loads:
            if load['type'] == 'point':
                P = float(load['mag'])
                xp = float(load['pos'])
                if x > xp:
                    v -= P
                    m -= P * (x - xp)
            elif load['type'] == 'udl':
                w = float(load['mag'])
                x1 = float(load['start'])
                x2 = float(load['end'])
                if x > x1:
                    udl_end = min(x, x2)
                    udl_span = udl_end - x1
                    load_force = w * udl_span
                    load_centroid = x1 + (udl_span / 2)
                    v -= load_force
                    m -= load_force * (x - load_centroid)
        shear_vals.append(v)
        moment_vals.append(m)
    return x_vals, np.array(shear_vals), np.array(moment_vals)

def create_plot(x, y, title, color, ylabel):
    plt.figure(figsize=(10, 5))
    plt.plot(x, y, color=color, linewidth=2)
    plt.fill_between(x, y, color=color, alpha=0.1)
    plt.title(title)
    plt.xlabel('Position (m)')
    plt.ylabel(ylabel)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save to base64
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    loads = data['loads']
    
    # Determine length
    positions = []
    for l in loads:
        if l['type'] == 'point': positions.append(float(l['pos']))
        if l['type'] == 'udl': positions.append(float(l['end']))
    
    length = max(float(max(positions, default=10)), 10.0) # Min 10m
    
    ra, rb = calculate_reactions(loads, length)
    x, V, M = calculate_arrays(loads, ra, length)
    
    sfd_img = create_plot(x, V, 'Shear Force Diagram', '#3b82f6', 'Shear (kN)')
    bmd_img = create_plot(x, M, 'Bending Moment Diagram', '#ef4444', 'Moment (kNm)')
    
    return jsonify({
        'ra': round(ra, 2),
        'rb': round(rb, 2),
        'sfd': sfd_img,
        'bmd': bmd_img
    })

if __name__ == '__main__':
    app.run(debug=True)
