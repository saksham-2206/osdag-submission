import pandas as pd
import os

# REVERSE ENGINEERED DATA
# User provided: V=45 at x=0, V=-45 at x=15. Linear change.
# This implies a UDL of w = delta_V / L = 90 / 15 = 6 kN/m.
# Max Moment at x=7.5 is 168.75, which matches wL^2/8 = 6*225/8 = 168.75.
# PERFECT MATCH.

data = {
    "Load Type": ["UDL"],
    "Magnitude (kN)": [6], # 6 kN/m
    "Position (m)": [None],        
    "Start Position (m)": [0], 
    "End Position (m)": [15]    
}

# Create DataFrame
df = pd.DataFrame(data)

# Ensure directory exists
output_dir = r"C:\Users\saksh_623c2rt\.gemini\antigravity\scratch\osdag_project"
os.makedirs(output_dir, exist_ok=True)

# Save to Excel
output_path = os.path.join(output_dir, "input_data.xlsx")
df.to_excel(output_path, index=False)

print(f"Data updated with Reverse Engineered Loads: 15m Beam, 6kN/m UDL")
print(df)
