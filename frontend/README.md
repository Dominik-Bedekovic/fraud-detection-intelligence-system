# Frontend

---

## Overview

This folder contains the user interface of the **Fraud Detection Intelligence System (FDIS)**.

It allows users to input transaction data and view fraud predictions returned by the backend API.

---

## Purpose

The frontend provides a simple interface for:

- Submitting manual transaction data
- Uploading batch data (.csv files)
- Displaying fraud prediction results

---

## Tech Stack

- HTML
- CSS
- JavaScript
- API communication with FastAPI backend

---

## How to Run

### 1. Install Requirements

Make sure you have the latest versions of `Python3` and `pip` installed first.

Then install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Start Docker services

```bash
docker compose up -d
```

### 3. Start the backend server (if running locally)

```bash
python -m uvicorn backend.app.main:app --reload
```

### 4. Open the application

Open your browser and go to:

```bash
http://127.0.0.1:8000
```

---

## How to Use

1. Open the website in your browser:
2. Use the navigation bar at the top or scroll until you see:

- **Single Transaction** → enter one transaction manually
- **Batch Transaction** → upload a `.csv` file

3. Submit your input
4. The website will display a **fraud probability score (%)**
