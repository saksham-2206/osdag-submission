# Osdag Internship Submission - Engineering Report Generator & Web App

This repository contains my submission for the **Osdag Screening Task**. It includes a Python script for generating professional PDF engineering reports and a bonus Web Application for interactive analysis.

## 📂 Repository Structure

- **`osdag_project/`**  
  Contains the core Python script (`main.py`) that reads Excel data, calculates Shear Force/Bending Moment, and generates a PDF report using PyLaTeX and TikZ.
  
- **`osdag_web_app/`**  
  A complete Flask-based Web Application. It provides a premium "Dark Mode" dashboard for validatng beam loads interactively.

- **`Report_Documentation.md`**  
  Detailed explanation of the code structure, logic, and design choices.

## 🚀 How to Run

### 1. PDF Report Generator
Navigate to the project folder and run the script:
```bash
cd osdag_project
pip install pandas openpyxl pylatex
python main.py
```
*Output: `report.pdf` will be generated.*

### 2. Web Application
Navigate to the web app folder and start the server:
```bash
cd osdag_web_app
pip install flask matplotlib
python app.py
```
*Open your browser to: `http://127.0.0.1:5000`*

## 🛠️ Features
- **Automated Calculations**: SFD & BMD calculated programmatically.
- **High-Quality Vector Graphics**: Diagrams drawn using LaTeX/TikZ (not images).
- **Professional Formatting**: Palatino fonts, headers, and center-aligned figures.
- **Web Interface**: Real-time analysis with a glassmorphism UI.

## 👤 Author
[Your Name/ID]
