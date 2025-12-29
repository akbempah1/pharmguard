# 🛡️ PharmGuard

**AI-Powered Theft Detection System for Retail Pharmacies**

PharmGuard uses machine learning algorithms to detect potential theft, inventory anomalies, and suspicious transaction patterns in retail pharmacy operations.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Dashboard-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 Problem Statement

Retail pharmacies lose an estimated **2-5% of revenue annually** to:
- Employee theft
- Inventory shrinkage
- Undetected transaction anomalies
- Pricing manipulation

Most pharmacy owners discover these issues too late — after significant losses have accumulated.

## 💡 Solution

PharmGuard analyzes POS transaction data in real-time to detect anomalies before they become major losses. It acts as a 24/7 digital auditor, flagging suspicious patterns for immediate investigation.

---

## ✨ Features

### 🔍 Anomaly Detection Algorithms
- **Daily Sales Analysis** — Detects unusual revenue patterns
- **Transaction Velocity** — Identifies abnormal transaction frequencies
- **Discount Pattern Analysis** — Flags excessive or suspicious discounts
- **Void/Refund Monitoring** — Tracks unusual cancellation patterns
- **Time-Based Analysis** — Detects after-hours suspicious activity

### 📊 Risk Scoring System
- **0-100 Risk Score** — Quantified risk assessment
- **Severity Levels** — 🟢 LOW | 🟡 MEDIUM | 🔴 HIGH | ⚫ CRITICAL
- **Evidence-Based Alerts** — Every flag includes supporting data

### 🌐 Web Dashboard
- Visual anomaly timeline
- Branch-by-branch comparison
- Drill-down investigation tools
- Historical trend analysis
- Export reports

### 📱 Real-Time Alerts
- **WhatsApp Integration** — Instant alerts via Twilio
- **Configurable Thresholds** — Set your own risk tolerance
- **Daily Summaries** — Morning briefings on overnight activity

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Core Engine | Python, Pandas, NumPy |
| ML/Statistics | Scikit-learn, SciPy |
| Web Dashboard | Flask, HTML, CSS, JavaScript |
| Alerts | Twilio API (WhatsApp) |
| Data Processing | CSV/Excel ingestion |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- POS transaction data (CSV format)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pharmguard.git
   cd pharmguard-mvp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install twilio  # For WhatsApp alerts
   ```

3. **Set environment variables (optional - for alerts)**
   ```bash
   # Create .env file
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ALERT_PHONE_NUMBER=whatsapp:+233xxxxxxxxx
   ```

### Running the CLI

**Basic analysis:**
```bash
python main.py --data your_sales_data.csv --no-alerts
```

**Analyze specific date:**
```bash
python main.py --data your_sales_data.csv --date 2024-11-15 --no-alerts
```

**With WhatsApp alerts enabled:**
```bash
python main.py --data your_sales_data.csv --phone +233xxxxxxxxx
```

### Running the Web Dashboard

```bash
cd dashboard
python app.py
```

Access at http://127.0.0.1:5000

---

## 📁 Project Structure

```
pharmguard-mvp/
├── main.py                  # CLI entry point
├── config.py                # Configuration settings
├── algorithms/
│   ├── daily_sales.py       # Daily revenue analysis
│   ├── transaction_velocity.py
│   ├── discount_analysis.py
│   └── void_detection.py
├── alerts/
│   └── whatsapp.py          # Twilio WhatsApp integration
├── dashboard/
│   ├── app.py               # Flask web application
│   ├── templates/           # HTML templates
│   ├── static/              # CSS, JS, images
│   └── uploads/             # Uploaded data files
├── data/                    # Sample datasets
├── models/                  # ML models (if applicable)
├── utils/
│   └── data_loader.py       # Data ingestion utilities
├── requirements.txt
└── README.md
```

---

## 📊 Sample Output

```
============================================================
🛡️  PHARMGUARD - ML THEFT DETECTION SYSTEM
============================================================

📊 RISK ASSESSMENT SUMMARY
============================================================
Date: Sunday, December 28, 2025
Risk Score: 73/100
Risk Level: 🔴 HIGH

Algorithms Run: 4
  • daily_sales: 25 points [⚠️ ALERT]
  • discount_patterns: 30 points [⚠️ ALERT]
  • void_analysis: 18 points [⚠️ ALERT]
  • transaction_velocity: 0 points [✓ OK]

⚠️ Issues Detected:
  1. Revenue 23% below expected for this day of week
  2. Discount rate 340% above normal (15.2% vs 3.4% avg)
  3. 7 voided transactions in 2-hour window (unusual)

💡 Recommended Actions:
  • Review CCTV footage for 2:00 PM - 4:00 PM
  • Audit discount approvals for today
  • Interview staff on duty during void cluster

============================================================
```

---

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Risk thresholds
RISK_THRESHOLDS = {
    'low': 25,
    'medium': 50,
    'high': 75,
    'critical': 90
}

# Algorithm weights
ALGORITHM_WEIGHTS = {
    'daily_sales': 1.0,
    'discount_patterns': 1.2,  # Higher weight
    'void_analysis': 1.1,
    'transaction_velocity': 0.8
}

# Alert settings
ALERT_ON_RISK_LEVEL = 'medium'  # Send alerts for medium and above
```

---

## 📈 Data Format

PharmGuard expects CSV data with these columns:

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Transaction date |
| time | TIME | Transaction time |
| transaction_id | STRING | Unique transaction ID |
| product_name | STRING | Product sold |
| quantity | INT | Quantity sold |
| unit_price | FLOAT | Price per unit |
| total_amount | FLOAT | Transaction total |
| discount | FLOAT | Discount applied |
| payment_method | STRING | Cash/Card/Mobile |
| staff_id | STRING | Employee identifier |

---

## 🔮 Roadmap

- [ ] Machine learning model training on historical theft data
- [ ] Integration with popular POS systems (Loyverse, Square)
- [ ] Multi-branch consolidated dashboard
- [ ] Predictive risk forecasting
- [ ] Integration with PharmaLedger (financial intelligence)
- [ ] Mobile app for on-the-go monitoring

---

## 🤝 Integration with PharmaLedger

PharmGuard is designed to work alongside **PharmaLedger** (AI-powered P&L generator):

- **PharmGuard** → Detects anomalies and potential theft
- **PharmaLedger** → Generates financial reports and insights

Together, they provide a complete financial intelligence and loss prevention solution for retail pharmacies.

---

## 👨‍💻 Author

**Afriyie karikari bempah**
- PharmD | MSc Finance | MSc Computer Science
- Building AI-powered tools for pharmacy operations in West Africa
- [LinkedIn](https://linkedin.com/in/afriyiekarikaribempah)
- [GitHub](https://github.com/akbempah1)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

PharmGuard is a decision-support tool. All alerts should be investigated by qualified personnel before taking action. False positives can occur, and the system should not be used as the sole basis for employee discipline or termination.

---

## 🙏 Acknowledgments

- KAM AID Pharmacy for real-world testing
- Madina branch team for providing sample data
