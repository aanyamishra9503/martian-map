# MARSCOPE — Interplanetary Survival Guide: Martian Map

MARSCOPE is a prototype project focused on exploring potential Martian exploration sites through data analysis and interactive visualization. The goal is to support the exploration of Mars by presenting relevant location data and scientific indicators in an accessible interface.

## Project Overview

Mars exploration requires careful consideration of terrain, location, and scientific value. MARSCOPE aims to provide an interactive platform for exploring potential sites and comparing their characteristics using planetary datasets.

This project is being developed as part of NASA Space Apps Challenge 2026.

## Current Features

- Interactive web interface built with Streamlit.
- Tabular display of exploration targets.
- Filtering targets using a minimum science-value threshold.
- Python-based data handling and visualization setup.

**Note:** The current prototype uses fictional sample targets for demonstration. These are not real Martian locations or validated scientific measurements.

## Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Git and GitHub

## Project Structure

```text
martian-map/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── __init__.py
│   └── mars_targets.py
└── notebooks/
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/martian-map.git
cd martian-map
```

Replace `YOUR-USERNAME` with the GitHub account that owns the repository.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

**Windows Command Prompt:**

```bat
.venv\Scripts\activate.bat
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Run the application

```bash
python -m streamlit run app.py
```

The application will be available locally at `http://localhost:8501`.

## Development Roadmap

- Integrate relevant real Martian planetary datasets.
- Develop interactive map-based exploration visualizations.
- Analyze location characteristics and scientific indicators.
- Improve the interface and data-processing pipeline.
- Evaluate the prototype using appropriate source data.

## Team

Developed by a two-member
