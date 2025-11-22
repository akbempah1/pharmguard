"""
Data validation and column detection
Automatically maps available columns to required schema
"""

import pandas as pd
from config import DATA_SCHEMA


class DataValidator:
    """Validates data and detects available columns"""
    
    def __init__(self):
        self.column_mapping = {}
        self.available_features = []
        self.missing_required = []
        self.warnings = []
    
    def validate_and_map(self, df):
        """
        Validate dataframe and create column mapping
        
        Returns:
            dict: {
                'valid': bool,
                'column_mapping': dict,
                'available_features': list,
                'missing_required': list,
                'warnings': list
            }
        """
        
        df_columns = [col.lower().strip() for col in df.columns]
        
        # Check each schema field
        for field_name, field_config in DATA_SCHEMA.items():
            found = False
            
            # Check if exact name exists
            if field_name in df_columns:
                self.column_mapping[field_name] = df.columns[df_columns.index(field_name)]
                found = True
            else:
                # Check alternatives
                for alt in field_config['alternatives']:
                    if alt.lower() in df_columns:
                        self.column_mapping[field_name] = df.columns[df_columns.index(alt.lower())]
                        found = True
                        break
            
            # Handle missing columns
            if not found:
                # Special handling for 'amount' - can be calculated from unit_price * quantity
                if field_name == 'amount':
                    has_unit_price = any(alt.lower() in df_columns for alt in DATA_SCHEMA['unit_price']['alternatives'])
                    has_quantity = any(alt.lower() in df_columns for alt in DATA_SCHEMA['quantity']['alternatives'])
                    
                    if has_unit_price and has_quantity:
                        self.warnings.append(f"'{field_name}' will be calculated from unit_price * quantity")
                        found = True  # Mark as found since we can calculate it
                
                # Special handling for 'unit_price' - can be calculated from amount / quantity
                elif field_name == 'unit_price':
                    has_amount = any(alt.lower() in df_columns for alt in DATA_SCHEMA['amount']['alternatives'])
                    has_quantity = any(alt.lower() in df_columns for alt in DATA_SCHEMA['quantity']['alternatives'])
                    
                    if has_amount and has_quantity:
                        self.warnings.append(f"'{field_name}' will be calculated from amount / quantity")
                        found = True
                
                if not found:
                    if field_config['required']:
                        self.missing_required.append(field_name)
                    else:
                        self.warnings.append(f"Optional column '{field_name}' not found - {field_config['description']}")
                        if 'enables' in field_config:
                            for feature in field_config['enables']:
                                self.warnings.append(f"  → Feature disabled: {feature}")
            else:
                # Track available optional features
                if not field_config['required'] and 'enables' in field_config:
                    self.available_features.extend(field_config['enables'])
        
        # Determine if data is valid
        valid = len(self.missing_required) == 0
        
        return {
            'valid': valid,
            'column_mapping': self.column_mapping,
            'available_features': self.available_features,
            'missing_required': self.missing_required,
            'warnings': self.warnings
        }
    
    def print_summary(self, validation_result):
        """Print human-readable validation summary"""
        
        print("\n" + "="*60)
        print("📋 DATA VALIDATION SUMMARY")
        print("="*60)
        
        if validation_result['valid']:
            print("✅ Data is VALID - all required columns found\n")
        else:
            print("❌ Data is INVALID - missing required columns:\n")
            for col in validation_result['missing_required']:
                print(f"   • {col} - {DATA_SCHEMA[col]['description']}")
                print(f"     Alternatives: {', '.join(DATA_SCHEMA[col]['alternatives'])}")
            print("\n⚠️  Please add these columns or rename existing columns to match.\n")
            return
        
        print("📊 Column Mapping:")
        for schema_name, actual_name in validation_result['column_mapping'].items():
            required = "✓ REQUIRED" if DATA_SCHEMA[schema_name]['required'] else "  optional"
            print(f"   {schema_name:20} → {actual_name:20} [{required}]")
        
        if validation_result['available_features']:
            print("\n✨ Available Features:")
            for feature in set(validation_result['available_features']):
                print(f"   • {feature}")
        
        if validation_result['warnings']:
            print("\n⚠️  Warnings:")
            for warning in validation_result['warnings']:
                print(f"   {warning}")
        
        print("="*60 + "\n")


def detect_data_capabilities(df, validation_result):
    """
    Determine which algorithms can run based on available data
    
    Returns:
        dict: Analysis capabilities
    """
    
    features = set(validation_result['available_features'])
    
    capabilities = {
        'can_run': {
            # These run with minimum data
            'daily_sales_anomaly': True,
            'high_value_tracking': True,
            'product_mix_analysis': True,
            'weekly_trends': True,
            
            # This needs time column
            'timing_patterns': 'timing_pattern_analysis' in features,
            
            # These need other optional columns
            'payment_anomaly': 'payment_anomaly_detection' in features,
            'individual_staff_tracking': 'individual_staff_tracking' in features,
            'void_return_tracking': 'void_return_tracking' in features,
            'discount_anomaly': 'discount_anomaly_detection' in features,
            'multi_branch': 'multi_branch_analysis' in features,
        },
        'requires_manual_input': {
            'high_value_products': 'List of products worth >GHS 50 (or we auto-detect from price data)',
            'shift_schedule': 'Weekly schedule of which staff work which shifts (if staff tracking enabled)',
            'branch_names': 'Branch names if using multi-branch (if branch_id column exists)'
        }
    }
    
    return capabilities