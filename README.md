# LottoLogic System - Handoff Guide

## 🚀 Getting Started

Your **Pattern Resonance Engine** is ready. The system is designed to analyze the last 200 rounds of Korean Lotto 6/45 data and generate numbers based on the 10 "Suspicious Rules" you identified.

### 1. Prerequisites
- **Python 3.10+** (Already installed on your system).
- **Internet Connection** (For initial data fetching).

### 2. How to Run (Local)
**Option A: One-Click (Recommended)**
Double-click `run_lotto.bat` inside the `my-lotto-app` folder.
This will start the server and automatically open the dashboard in your browser.

**Option B: Manual**
Open a terminal in `my-lotto-app` and run:
```bash
python lotto_server.py
```

### 3. How to Deploy (Vercel)
This folder is fully configured for Vercel.
1. Upload `my-lotto-app` to GitHub.
2. Import the project in Vercel.
3. Deploy!
2.  **Background Sync**: It will quietly fetch the latest 200 rounds of data from `dhlottery.co.kr`. This takes about 30-40 seconds on first run.

### 3. Using the Dashboard
1.  Open your browser to `http://localhost:8888`.
2.  Click **"ANALYZE & GENERATE"**.
3.  The engine will produce 5 sets of numbers sorted by their **"Resonance Score"** (how well they match the system's pattern).
4.  **Green Tags** indicate which rules the set successfully passed (e.g., "Sum OK", "Zero Zone", "Odd/Even").

### 4. Technical Details
- **Core Logic (`lotto_core.py`)**: Handles data scraping, statistical analysis, and weighted pattern matching.
- **Server (`lotto_server.py`)**: A lightweight Python server that hosts the API and UI.
- **Frontend (`web/index.html`)**: A modern, dark-themed dashboard using vanilla JS/CSS (no installation needed).

### 5. Customization
To adjust the strictness of the rules, you can edit the `PatternAnalyzer` class in `lotto_core.py`. Change `self.weights` values (0.0 to 1.0) to prioritize different rules.

---
**Status**: Ready for Deployment.
**Version**: 1.0.0 (MVP)
