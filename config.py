"""
PharmGuard Configuration
Defines data requirements and flexible column mapping
"""

# Data Column Requirements
DATA_SCHEMA = {
    # CRITICAL COLUMNS (Code breaks without these)
    'transaction_date': {
        'required': True,
        'alternatives': ['date', 'sale_date', 'trans_date', 'Date', 'DATE', 'invoice_date', 'Invoice_Date'],
        'type': 'date',
        'description': 'Transaction date'
    },
    'product_name': {
        'required': True,
        'alternatives': ['product', 'item_name', 'description', 'Product', 'Item', 'product_name', 'item_description*', 'item_description'],
        'type': 'string',
        'description': 'Product name or description'
    },
    'quantity': {
        'required': True,
        'alternatives': ['qty', 'quantity_sold', 'Quantity', 'Qty', 'QTY'],
        'type': 'numeric',
        'description': 'Quantity sold'
    },
    'amount': {
        'required': False,  # Changed to optional since we can calculate it
        'alternatives': ['total', 'total_amount', 'sale_amount', 'Amount', 'Total', 'AMOUNT'],
        'type': 'numeric',
        'description': 'Total sale amount (will be calculated if missing)',
        'calculate_from': ['unit_price', 'quantity']
    },
    
    # OPTIONAL COLUMNS (Code adapts if missing)
    'transaction_time': {
        'required': False,
        'alternatives': ['time', 'sale_time', 'trans_time', 'Time'],
        'type': 'time',
        'description': 'Transaction time (enables timing analysis)',
        'enables': ['timing_pattern_analysis']
    },
    'unit_price': {
        'required': False,
        'alternatives': ['price', 'unit_price', 'selling_price', 'Price', 'Unit_Price'],
        'type': 'numeric',
        'description': 'Unit price (can be calculated from amount/quantity)',
        'calculate_from': ['amount', 'quantity']
    },
    'payment_method': {
        'required': False,
        'alternatives': ['payment', 'payment_type', 'method', 'Payment'],
        'type': 'categorical',
        'description': 'Payment method (Cash/Momo/Card)',
        'enables': ['payment_anomaly_detection']
    },
    'staff_name': {
        'required': False,
        'alternatives': ['staff', 'employee', 'cashier', 'Staff', 'sold_by'],
        'type': 'string',
        'description': 'Staff member name/ID',
        'enables': ['individual_staff_tracking']
    },
    'transaction_status': {
        'required': False,
        'alternatives': ['status', 'trans_status', 'Status'],
        'type': 'categorical',
        'description': 'Transaction status (Completed/Voided/Returned)',
        'enables': ['void_return_tracking']
    },
    'discount_amount': {
        'required': False,
        'alternatives': ['discount', 'Discount'],
        'type': 'numeric',
        'description': 'Discount amount given',
        'enables': ['discount_anomaly_detection']
    },
    'branch_id': {
        'required': False,
        'alternatives': ['branch', 'location', 'Branch'],
        'type': 'string',
        'description': 'Branch identifier',
        'enables': ['multi_branch_analysis']
    },
    'invoice_id': {
        'required': False,
        'alternatives': ['invoice_id', 'invoice_id*', 'transaction_id', 'receipt_id'],
        'type': 'string',
        'description': 'Invoice/transaction identifier',
        'enables': ['invoice_grouping']
    }
}

# High-value product threshold (in GHS)
HIGH_VALUE_THRESHOLD = 50

# Business hours (for timing analysis if time data available)
BUSINESS_HOURS = {
    'open': 7,   # 7am
    'close': 21  # 9pm
}

# Shift definitions
SHIFT_TIMES = {
    'morning': (7, 13),
    'afternoon': (13, 18),
    'evening': (18, 21)
}

# Risk score thresholds
RISK_LEVELS = {
    'low': (0, 39),
    'medium': (40, 59),
    'high': (60, 79),
    'critical': (80, 100)
}

# Alert settings
ALERT_THRESHOLD = 40