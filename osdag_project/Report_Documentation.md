# Report Documentation: Osdag PyLaTeX Project

## 1. Introduction
This document explains the internal working of the Python automation script designed to generate structural analysis reports. The goal of the tool is to bridge the gap between numerical analysis and professional documentation by integrating Python's calculation power with LaTeX's typesetting capabilities.

## 2. Code Structure & Logic

### 2.1 Data Ingestion (`read_data`)
The script uses the `pandas` library to read `input_data.xlsx`. It normalizes the data into a list of dictionaries, handling both 'Point' loads and 'Uniformly Distributed Loads' (UDL).
-   **Input**: Excel file path.
-   **Output**: A clean list of load objects (dictionaries).

### 2.2 Engineering Analysis (`calculate_reactions`, `calculate_arrays`)
The core physics engine is implemented from first principles of statics for a Simply Supported Beam.

**Step 1: Reaction Calculation**
Using the equilibrium equation $\sum M_A = 0$:
$$ R_B = \frac{\sum (Load \times Distance)}{L} $$
Then, $R_A = \sum Load - R_B$.

**Step 2: Discretization**
The beam is divided into 500 discrete points. At each point $x$:
-   **Shear Force ($V$)**: Start with $R_A$ and subtract any loads to the left of $x$.
-   **Bending Moment ($M$)**: Sum of moments caused by $R_A$ and all loads to the left of $x$ about point $x$.

### 2.3 Visualization (TikZ Integration)
Instead of embedding static images (like PNGs from Matplotlib), the script generates **native LaTeX TikZ code**.
-   The Python script builds a string of coordinates: `(0,0) (0.1, 5) (0.2, 10)...`
-   This string is injected into a `\addplot` command inside a `pgfplots` axis environment.
-   **Benefit**: This results in infinite-resolution vector graphics suitable for professional engineering publications.

### 2.4 Report Assembly (PyLaTeX)
The `pylatex` library is used to construct the document object model (DOM).
-   **Sections/Subsections**: Created programmatically.
-   **Tables**: Pandas DataFrames are converted to LaTeX tabular environments.
-   **Figures**: The beam setup image is embedded using standard LaTeX `figure` environments.

## 3. Usage Guide
To execute the project, ensure dependencies (`pandas`, `pylatex`) are installed. Run `main.py` in the root directory. The output `report.tex` is a standalone LaTeX file containing all analysis results and diagram code.
