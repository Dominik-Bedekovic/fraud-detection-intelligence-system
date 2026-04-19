# Fraud-detection-intelligence-system

Website for analyzing and validating bank payments through the use of Machine Learning

This project demonstrates how machine learning can be used to improve financial security by detecting potentially fraudulent activities.

---

## Features

- Input of transaction data through the user interface
- Trained machine learning model which predicts probability of fraud
- Immediate display of the fraud probability results to the user
- Backend API for handling requests between the frontend and the machine learning model

---

## How to Run

1. Clone the repository:

``` bash
git clone https://github.com/Dominik-Bedekovic/fraud-detection-intelligence-system.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt

```

3. Run the backend:

```bash
python -m uvicorn backend.app.main:app --reload
```

4. Paste the URL into a browser's search bar:

```
http://127.0.0.1:8000
```

---

## Project structure

- `backend/` – API and server logic  
- `frontend/` – user interface   
- `ml/` – machine learning model  
- `docs/` – documentation  

---

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python (FastAPI)
- Machine Learning: Scikit-learn (pipeline-based ML system)
- Data processing: Pandas, NumPy
- Model storage: Joblib
- Version Control: Git + GitHub

---

## Project Planning

### Work Breakdown Structure
![WBS](docs/wbs-diagram.drawio.svg)

### PERT Diagram
![PERT](docs/pert-diagram.png)

---

## Authors
- Dominik Bedeković
- Matija Dežjot
- Ella Vučemilović-Grgić
- Perun Vinski
