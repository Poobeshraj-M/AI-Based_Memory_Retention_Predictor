# 🧠 AI-Based Memory Retention Predictor

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![MySQL](https://img.shields.io/badge/MySQL-Supported-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

An advanced web application that leverages Artificial Intelligence to predict student memory retention scores based on study habits, previous academic performance, and sleep patterns.

---

## 🚀 Key Features

- **🤖 AI Predictions**: Get real-time retention scores using a trained machine learning model.
- **📊 Analytics Dashboard**: Beautifully visualized data using Chart.js to track student performance trends.
- **📁 Bulk Data Management**: Upload CSV/Excel datasets for batch predictions and historical analysis.
- **🛡️ Secure Admin Panel**: Manage users, monitor system logs, and control data access.
- **📄 PDF Reports**: Generate professional student profile and analytics reports.

---

## 📸 Screenshots

### 🖥️ Analytics Dashboard
Visualize student metrics and predicted retention scores at a glance.
![Dashboard](screenshots/dashboard.png)

### 🔮 Prediction Interface
Input student details to get instant AI-driven retention insights.
![Predict Page](screenshots/predict_page.png)

### 🔐 Secure Login
Role-based access control for Admins and Staff.
![Login Page](screenshots/login_page.png)

### 🛠️ Admin Management
System logs and user control panel.
![Admin Panel](screenshots/admin_panel.png)

---

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, Vanilla CSS, JavaScript
- **Database**: MySQL (with SQLite fallback)
- **Visualization**: Chart.js
- **AI/ML**: Pandas, Scikit-learn
- **Reporting**: FPDF

---

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Poobeshraj-M/AI-Based_Memory_Retention_Predictor.git
   cd AI-Based_Memory_Retention_Predictor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**:
   - Rename `.env.example` to `.env`.
   - Update your MySQL credentials in the `.env` file.

4. **Initialize Database**:
   ```bash
   python create_db.py
   ```

5. **Run the Application**:
   ```bash
   python app.py
   ```
   Access the app at `http://127.0.0.1:5000`.

---

## 👤 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
Developed by [Poobeshraj M](https://github.com/Poobeshraj-M)
