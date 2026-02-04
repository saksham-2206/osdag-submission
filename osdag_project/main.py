import pandas as pd
import numpy as np
from pylatex import Document, Section, Subsection, Command, Figure, TikZ, Axis, Plot
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
    print(f"Reactions: Ra={ra:.2f} kN, Rb={rb:.2f} kN")
    
    x, V, M = calculate_arrays(loads, ra, L)
    
    # Create Document with Professional Settings
    geometry_options = {"top": "1in", "bottom": "1in", "left": "1in", "right": "1in"}
    doc = Document(geometry_options=geometry_options)
    
    # Packages for Professional Look
    doc.preamble.append(NoEscape(r'\usepackage{booktabs}')) # Nice tables
    doc.preamble.append(NoEscape(r'\usepackage{pgfplots}'))
    doc.preamble.append(NoEscape(r'\usepgfplotslibrary{fillbetween}'))
    doc.preamble.append(NoEscape(r'\pgfplotsset{compat=1.18}'))
    doc.preamble.append(NoEscape(r'\usepackage{fancyhdr}')) # Headers
    doc.preamble.append(NoEscape(r'\usepackage{placeins}')) # Stop floating
    doc.preamble.append(NoEscape(r'\usepackage{mathpazo}')) # Palatino Font (Professional)
    doc.preamble.append(NoEscape(r'\usepackage{float}'))    # Force H placement
    
    # Header/Footer Setup
    doc.preamble.append(NoEscape(r'\pagestyle{fancy}'))
    doc.preamble.append(NoEscape(r'\fancyhf{}'))
    doc.preamble.append(NoEscape(r'\rhead{\today}'))
    doc.preamble.append(NoEscape(r'\lhead{Osdag Structural Analysis}'))
    doc.preamble.append(NoEscape(r'\cfoot{\thepage}'))
    
    # Title Page
    doc.preamble.append(Command('title', 'Engineering Report: Simply Supported Beam Analysis'))
    doc.preamble.append(Command('author', 'Osdag Internship Project'))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))
    doc.append(NoEscape(r'\thispagestyle{empty}')) # No header on title page
    doc.append(NoEscape(r'\tableofcontents'))
    doc.append(NoEscape(r'\newpage'))
    
    # Introduction
    with doc.create(Section('Introduction')):
        doc.append("This report presents the analysis of a simply supported beam under various loads.")
        doc.append(" The detailed Shear Force and Bending Moment diagrams are generated programmatically.")
        
        with doc.create(Subsection('Beam Setup')):
            with doc.create(Figure(position='H')) as beam_fig: # 'H' forces it HERE
                doc.append(NoEscape(r'\centering'))
                if os.path.exists(image_file):
                    beam_fig.add_image(image_file, width='350px')
                    beam_fig.add_caption('Simply Supported Beam Configuration')
                else:
                    beam_fig.append(bold("Image not found."))

    doc.append(NoEscape(r'\FloatBarrier')) # Finish section before moving on

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

    # Analysis
    with doc.create(Section('Analysis Results')):
        doc.append(f"Calculated Reactions:\n")
        doc.append(f"Ra (Left Support): {ra:.2f} kN\n")
        doc.append(f"Rb (Right Support): {rb:.2f} kN\n")

        # SFD
        with doc.create(Subsection('Shear Force Diagram (SFD)')):
            doc.append("The Shear Force Diagram shows the variation of shear force along the beam.")
            
            with doc.create(Figure(position='H')) as plot_fig:
                plot_fig.append(NoEscape(r'\centering'))
                with plot_fig.create(TikZ()) as tikz:
                    sfd_coords = generate_tikz_coords(x, V)
                    
                    # TikZ Axis
                    axis_options = r"""
                    width=0.9\textwidth, height=7cm,
                    axis x line=bottom, axis y line=left,
                    xlabel={Position (m)}, ylabel={Shear Force (kN)},
                    grid=major,
                    enlarge x limits=false,
                    enlargelimits=0.1
                    """
                    
                    tikz.append(NoEscape(r'\begin{axis}[' + axis_options + r']'))
                    
                    # Plot Fill
                    tikz.append(NoEscape(r'\addplot[name path=f, color=blue, thick] coordinates {' + sfd_coords + r'};'))
                    tikz.append(NoEscape(r'\path[name path=axis] (axis cs:0,0) -- (axis cs:' + str(L) + r',0);'))
                    tikz.append(NoEscape(r'\addplot[blue!10] fill between[of=f and axis];'))
                    
                    tikz.append(NoEscape(r'\end{axis}'))
                plot_fig.add_caption('Shear Force Diagram')

        # BMD
        with doc.create(Subsection('Bending Moment Diagram (BMD)')):
            doc.append("The Bending Moment Diagram shows the variation of bending moment along the beam.")
            
            with doc.create(Figure(position='H')) as plot_fig:
                plot_fig.append(NoEscape(r'\centering'))
                with plot_fig.create(TikZ()) as tikz:
                    bmd_coords = generate_tikz_coords(x, M)
                    
                    axis_options = r"""
                    width=0.9\textwidth, height=7cm,
                    axis x line=bottom, axis y line=left,
                    xlabel={Position (m)}, ylabel={Moment (kNm)},
                    grid=major,
                    enlarge x limits=false,
                    enlargelimits=0.1
                    """
                    
                    tikz.append(NoEscape(r'\begin{axis}[' + axis_options + r']'))
                    
                    tikz.append(NoEscape(r'\addplot[name path=f, color=red, thick] coordinates {' + bmd_coords + r'};'))
                    tikz.append(NoEscape(r'\path[name path=axis] (axis cs:0,0) -- (axis cs:' + str(L) + r',0);'))
                    tikz.append(NoEscape(r'\addplot[red!10] fill between[of=f and axis];'))
                    
                    tikz.append(NoEscape(r'\end{axis}'))
                plot_fig.add_caption('Bending Moment Diagram')

    # Generate PDF
    # We use clean_tex=False so we can see the .tex file if PDF extraction fails
    try:
        doc.generate_pdf(OUTPUT_FILENAME, clean_tex=False, compiler='pdflatex')
        print(f"PDF generated: {OUTPUT_FILENAME}.pdf")
    except Exception as e:
        print("PDF Generation Failed (likely due to missing LaTeX compiler).")
        print("However, the .tex file has been generated.")
        print(f"Error: {e}")

if __name__ == "__main__":
    create_report()
