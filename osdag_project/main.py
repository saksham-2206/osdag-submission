import pandas as pd
import numpy as np
from pylatex import Document, Section, Subsection, Command, Figure, TikZ, Axis, Plot, Itemize, Description
from pylatex.utils import NoEscape, bold
import os

# CONFIG: Add MiKTeX to PATH manually
miktex_path = r"C:\Users\saksh_623c2rt\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
if miktex_path not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + miktex_path

# Constants
OUTPUT_FILENAME = "report"
BEAM_LENGTH = 10.0  # Default, can be adjusted based on load
NUM_POINTS = 500   # Resolution for diagrams

def read_data(filepath):
    """
    Reads the Excel file and normalizes columns.
    Expected columns in Excel: 'Load Type', 'Magnitude (kN)', 'Position (m)', 'Start Position (m)', 'End Position (m)'
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    df = pd.read_excel(filepath)
    
    # Normalize data for internal use
    loads = []
    
    for _, row in df.iterrows():
        l_type = str(row.get('Load Type', '')).lower()
        mag = row.get('Magnitude (kN)', 0)
        
        if 'point' in l_type:
            pos = row.get('Position (m)')
            if pd.isna(pos): pos = row.get('Start Position (m)') # Fallback
            loads.append({'type': 'point', 'mag': mag, 'pos': pos})
            
        elif 'udl' in l_type:
            start = row.get('Start Position (m)')
            end = row.get('End Position (m)')
            if pd.isna(start): start = row.get('Position (m)') # Fallback
            loads.append({'type': 'udl', 'mag': mag, 'start': start, 'end': end})
            
    return df, loads

def calculate_reactions(loads, length):
    """
    Calculates reactions Ra (left) and Rb (right) for a simply supported beam.
    Sum(Ma) = 0  =>  Rb * L = Sum(Moment_loads_about_A)
    """
    moment_sum_a = 0
    total_load = 0
    
    for load in loads:
        if load['type'] == 'point':
            P = load['mag']
            x = load['pos']
            moment_sum_a += P * x
            total_load += P
        elif load['type'] == 'udl':
            w = load['mag'] # kN/m
            x1 = load['start']
            x2 = load['end']
            span = x2 - x1
            total_w = w * span
            centroid = x1 + (span / 2)
            moment_sum_a += total_w * centroid
            total_load += total_w
            
    rb = moment_sum_a / length
    ra = total_load - rb
    
    return ra, rb

def calculate_arrays(loads, ra, length, num_points=NUM_POINTS):
    """
    Generates x, Shear(V), and Moment(M) arrays.
    """
    x_vals = np.linspace(0, length, num_points)
    shear_vals = []
    moment_vals = []
    
    for x in x_vals:
        # Calculate V and M at section x (from left)
        # V = Ra - Sum(Down_Loads)
        # M = Ra*x - Sum(Moments_of_Down_Loads)
        
        v = ra
        m = ra * x
        
        for load in loads:
            if load['type'] == 'point':
                P = load['mag']
                xp = load['pos']
                if x > xp: # Cut is to the right of load
                    v -= P
                    m -= P * (x - xp)
                    
            elif load['type'] == 'udl':
                w = load['mag']
                x1 = load['start']
                x2 = load['end']
                
                # UDL covers overlap of [x1, x2] and [0, x]
                # Actually, simpler: calculate portion of UDL to the left of x
                
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

def generate_tikz_coords(x_vals, y_vals):
    """Generates coordinate string (x,y) for TikZ"""
    coords = ""
    # Downsample slightly for TikZ string length safety if needed, or use full
    step = max(1, len(x_vals) // 200) 
    for i in range(0, len(x_vals), step):
        coords += f"({x_vals[i]:.2f},{y_vals[i]:.2f}) "
    # Ensure last point is included
    coords += f"({x_vals[-1]:.2f},{y_vals[-1]:.2f})"
    return coords

def get_max_values(x_vals, V_vals, M_vals):
    """Finds absolute maximums and their positions."""
    idx_v = np.argmax(np.abs(V_vals))
    idx_m = np.argmax(np.abs(M_vals))
    return {
        'v_max': V_vals[idx_v],
        'v_pos': x_vals[idx_v],
        'm_max': M_vals[idx_m],
        'm_pos': x_vals[idx_m]
    }

def create_report():
    input_file = os.path.join(os.path.dirname(__file__), 'input_data.xlsx')
    image_file = os.path.join(os.path.dirname(__file__), 'beam_setup.png')
    
    print("Reading data...")
    raw_df, loads = read_data(input_file)
    
    # Determine beam length exactly from loads
    positions = []
    for l in loads:
        if 'pos' in l: positions.append(l['pos'])
        if 'end' in l: positions.append(l['end'])
    
    if positions:
        L = float(max(positions))
        # Ensure it doesn't shrink below default if no loads are far out
        L = max(L, BEAM_LENGTH) 
    else:
        L = BEAM_LENGTH
    
    print(f"Beam Length: {L}m")
    ra, rb = calculate_reactions(loads, L)
    x, V, M = calculate_arrays(loads, ra, L)
    stats = get_max_values(x, V, M)
    
    # Create Document
    geometry_options = {"top": "1in", "bottom": "1in", "left": "1in", "right": "1in"}
    doc = Document(geometry_options=geometry_options)
    
    # Preamble
    doc.preamble.append(NoEscape(r'\usepackage{booktabs}'))
    doc.preamble.append(NoEscape(r'\usepackage{pgfplots}'))
    doc.preamble.append(NoEscape(r'\usepgfplotslibrary{fillbetween}'))
    doc.preamble.append(NoEscape(r'\pgfplotsset{compat=1.18}'))
    doc.preamble.append(NoEscape(r'\usepackage{fancyhdr}'))
    doc.preamble.append(NoEscape(r'\usepackage{placeins}'))
    doc.preamble.append(NoEscape(r'\usepackage{mathpazo}'))
    doc.preamble.append(NoEscape(r'\usepackage{float}'))
    
    doc.preamble.append(NoEscape(r'\pagestyle{fancy}'))
    doc.preamble.append(NoEscape(r'\fancyhf{}'))
    doc.preamble.append(NoEscape(r'\rhead{\today}'))
    doc.preamble.append(NoEscape(r'\lhead{Osdag Structural Analysis - Comprehensive Report}'))
    doc.preamble.append(NoEscape(r'\cfoot{\thepage}'))
    
    # Title
    doc.preamble.append(Command('title', 'Detailed Engineering Report: Simply Supported Beam Analysis'))
    doc.preamble.append(Command('author', 'Osdag Internship Project - Advanced Module'))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))
    doc.append(NoEscape(r'\thispagestyle{empty}'))
    doc.append(NoEscape(r'\tableofcontents'))
    doc.append(NoEscape(r'\newpage'))
    
    # 1. Executive Summary
    with doc.create(Section('Executive Summary')):
        doc.append("This comprehensive report details the structural response of a simply supported beam. ")
        doc.append("The analysis evaluates reactions at supports and internal force distributions (Shear and Moment) based on the specified loading conditions. ")
        doc.append(f"The beam has a total span of {L:.2f} meters and is subjected to {len(loads)} distinct loading elements.")
        doc.append(NoEscape(r'\par\medskip'))
        doc.append("Key findings include:")
        with doc.create(Itemize()) as itemize:
            itemize.add_item(NoEscape(f"Total applied downward force: {sum(l['mag'] if l['type']=='point' else l['mag']*(l['end']-l['start']) for l in loads):.2f} kN"))
            itemize.add_item(NoEscape(f"Maximum Shear Force: {abs(stats['v_max']):.2f} kN at x = {stats['v_pos']:.2f} m"))
            itemize.add_item(NoEscape(f"Maximum Bending Moment: {abs(stats['m_max']):.2f} kNm at x = {stats['m_pos']:.2f} m"))

    # 2. Methodology
    with doc.create(Section('Methodology')):
        doc.append("The analysis is performed using the principles of static equilibrium. ")
        doc.append("The beam is discretized into 500 segments to ensure high resolution in the resulting diagrams.")
        
        with doc.create(Subsection('Global Equilibrium')):
            doc.append("The support reactions $R_A$ and $R_B$ are calculated by taking moments about support A:")
            doc.append(NoEscape(r'\[ \sum M_A = 0 \implies R_B \cdot L = \sum (P_i \cdot x_i) + \sum (w_j \cdot L_j \cdot x_{centroid,j}) \]'))
            doc.append("Once $R_B$ is determined, $R_A$ is found using vertical force balance:")
            doc.append(NoEscape(r'\[ \sum F_y = 0 \implies R_A = \sum Load_{Total} - R_B \]'))

        with doc.create(Subsection('Internal Forces')):
            doc.append("At any section $x$, the shear force $V(x)$ and bending moment $M(x)$ are derived as:")
            doc.append(NoEscape(r'\[ V(x) = R_A - \int_{0}^{x} w(x) \, dx - \sum P_i |_{x_i < x} \]'))
            doc.append(NoEscape(r'\[ M(x) = R_A \cdot x - \int_{0}^{x} w(x)(x - \xi) \, d\xi - \sum P_i(x - x_i) |_{x_i < x} \]'))
    

    # Input Data
    with doc.create(Section('Input Data')):
        doc.append("The loading data extracted from the Excel file is shown below.")
        with doc.create(Subsection('Load Table')):
             doc.append(NoEscape(r'\begin{table}[H]'))
             doc.append(NoEscape(r'\centering'))
             try:
                 tex_table = raw_df.to_latex(index=False, float_format="%.2f")
                 doc.append(NoEscape(tex_table))
             except AttributeError:
                 doc.append(NoEscape(raw_df.to_string()))
             doc.append(NoEscape(r'\caption{Load Configuration}'))
             doc.append(NoEscape(r'\end{table}'))

    doc.append(NoEscape(r'\FloatBarrier'))

    # 4. Analysis Results
    with doc.create(Section('Analysis & Visualizations')):
        doc.append(f"The structural analysis yielded the following support reactions:\n")
        with doc.create(Description()) as description:
            description.add_item(NoEscape(r'$R_A$ (Left Support):'), f' {ra:.2f} kN')
            description.add_item(NoEscape(r'$R_B$ (Right Support):'), f' {rb:.2f} kN')

        # SFD
        with doc.create(Subsection('Shear Force Diagram (SFD)')):
            doc.append(f"The maximum absolute shear force is {abs(stats['v_max']):.2f} kN, occurring at {stats['v_pos']:.2f} m.")
            
            with doc.create(Figure(position='H')) as plot_fig:
                plot_fig.append(NoEscape(r'\centering'))
                with plot_fig.create(TikZ()) as tikz:
                    sfd_coords = generate_tikz_coords(x, V)
                    axis_options = r"width=0.9\textwidth, height=6.5cm, axis x line=middle, axis y line=left, xlabel={Position (m)}, ylabel={V (kN)}, grid=major, enlarge x limits=false"
                    tikz.append(NoEscape(r'\begin{axis}[' + axis_options + r']'))
                    tikz.append(NoEscape(r'\addplot[name path=f, blue, thick] coordinates {' + sfd_coords + r'};'))
                    tikz.append(NoEscape(r'\path[name path=axis] (axis cs:0,0) -- (axis cs:' + str(L) + r',0);'))
                    tikz.append(NoEscape(r'\addplot[blue!10] fill between[of=f and axis];'))
                    tikz.append(NoEscape(r'\end{axis}'))
                plot_fig.add_caption('Shear Force Diagram (SFD)')

        # BMD
        with doc.create(Subsection('Bending Moment Diagram (BMD)')):
            doc.append(f"The maximum absolute bending moment (critical section) is {abs(stats['m_max']):.2f} kNm, occurring at {stats['m_pos']:.2f} m.")
            
            with doc.create(Figure(position='H')) as plot_fig:
                plot_fig.append(NoEscape(r'\centering'))
                with plot_fig.create(TikZ()) as tikz:
                    bmd_coords = generate_tikz_coords(x, M)
                    axis_options = r"width=0.9\textwidth, height=6.5cm, axis x line=middle, axis y line=left, xlabel={Position (m)}, ylabel={M (kNm)}, grid=major, enlarge x limits=false"
                    tikz.append(NoEscape(r'\begin{axis}[' + axis_options + r']'))
                    tikz.append(NoEscape(r'\addplot[name path=f, red, thick] coordinates {' + bmd_coords + r'};'))
                    tikz.append(NoEscape(r'\path[name path=axis] (axis cs:0,0) -- (axis cs:' + str(L) + r',0);'))
                    tikz.append(NoEscape(r'\addplot[red!10] fill between[of=f and axis];'))
                    tikz.append(NoEscape(r'\end{axis}'))
                plot_fig.add_caption('Bending Moment Diagram (BMD)')

    # 5. Conclusion
    with doc.create(Section('Conclusion')):
        doc.append("The analysis of the simply supported beam has been successfully completed. ")
        doc.append("The resulting SFD and BMD provide the necessary internal force distributions for further structural design, such as reinforcement calculation or section selection. ")
        doc.append(f"Special attention should be given to the section at x = {stats['m_pos']:.2f} m, where the bending moment is maximized.")
        doc.append(NoEscape(r'\par\vfill'))
        doc.append(NoEscape(r'\begin{center} \textit{End of Engineering Report} \end{center}'))

    # Generate PDF
    try:
        doc.generate_pdf(OUTPUT_FILENAME, clean_tex=False, compiler='pdflatex')
        print(f"PDF generated: {OUTPUT_FILENAME}.pdf")
    except Exception as e:
        print("PDF Generation Failed (likely due to missing LaTeX compiler).")
        print("However, the .tex file has been generated.")
        print(f"Error: {e}")

if __name__ == "__main__":
    create_report()
