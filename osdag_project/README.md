# Osdag Internship Project: PyLaTeX Report Generator

## 📌 Overview
This project is a Python-based automation tool capable of generating professional structural engineering reports. It reads load data from an Excel file, analyzes a Simply Supported Beam (calculating Reactions, Shear Force, and Bending Moment), and produces a PDF report with high-quality vector graphics (TikZ/PGFPlots).

## 🛠️ Tech Stack
-   **Language**: Python 3
-   **Libraries**:
    -   `pandas`, `openpyxl`: For data ingestion.
    -   `pylatex`: For programmatic PDF generation.
    -   `numpy`: For numerical computation.
-   **Output Format**: LaTeX (.tex) / PDF

## 🚀 How to Run

### Prerequisites
1.  Python 3.x installed.
2.  Install dependencies:
    ```bash
    pip install pandas openpyxl pylatex numpy
    ```
3.  (Optional) A local LaTeX distribution (MiKTeX, TeX Live) to generate PDFs automatically. If not installed, the tool generates a `.tex` file you can compile on Overleaf.

### Steps
1.  **Prepare Data**: Edit `input_data.xlsx` with your beam loads.
2.  **Run Script**:
    ```bash
    python main.py
    ```
3.  **View Report**:
    -   If LaTeX is installed: Open `report.pdf`.
    -   If not: Upload `report.tex` and `beam_setup.png` to [Overleaf.com](https://www.overleaf.com).

## 📄 File Structure
-   `main.py`: Core logic for analysis and report generation.
-   `input_data.xlsx`: Input file for load configuration.
-   `beam_setup.png`: Asset image for the beam diagram.

## 📊 Features
-   **Automated Analysis**: Solves reactions ($R_a, R_b$) using equilibrium equations.
-   **Vector Graphics**: Generates native TikZ code for SFD and BMD plots (no pixelation).
-   **Dynamic Tables**: Automatically converts Pandas DataFrames to LaTeX tables.
