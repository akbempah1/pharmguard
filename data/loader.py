"""
Flexible data loader that handles various file formats and column configurations
"""

import pandas as pd
from pathlib import Path
from data.validator import DataValidator
from config import DATA_SCHEMA


class DataLoader:
    """Loads and standardizes transaction data"""
    
    def __init__(self):
        self.validator = DataValidator()
        self.raw_df = None
        self.standardized_df = None
        self.validation_result = None
    
    def load(self, filepath):
        """
        Load data from file (CSV or Excel)
        
        Args:
            filepath: Path to data file
            
        Returns:
            tuple: (standardized_df, validation_result)
        """
        
        filepath = Path(filepath)
        
        # Load based on file extension
        if filepath.suffix.lower() == '.csv':
            self.raw_df = pd.read_csv(filepath)
        elif filepath.suffix.lower() in ['.xlsx', '.xls']:
            self.raw_df = pd.read_excel(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
        
        print(f"📂 Loaded {len(self.raw_df)} rows from {filepath.name}")
        
        # Validate and map columns
        self.validation_result = self.validator.validate_and_map(self.raw_df)
        self.validator.print_summary(self.validation_result)
        
        if not self.validation_result['valid']:
            raise ValueError("Data validation failed - missing required columns")
        
        # Standardize column names
        self.standardized_df = self._standardize_dataframe()
        
        # Calculate derived fields if needed
        self.standardized_df = self._calculate_derived_fields()
        
        # Clean data
        self.standardized_df = self._clean_data()
        
        return self.standardized_df, self.validation_result
    
    def _standardize_dataframe(self):
        """Rename columns to standard schema names"""
        
        mapping = self.validation_result['column_mapping']
        
        # Create new dataframe with standardized names
        standardized = pd.DataFrame()
        
        for schema_name, actual_name in mapping.items():
            standardized[schema_name] = self.raw_df[actual_name]
        
        return standardized
    
    def _calculate_derived_fields(self):
        """Calculate missing fields that can be derived"""
        
        df = self.standardized_df.copy()
        
         # Calculate unit_price if missing but amount and quantity exist
        if 'unit_price' not in df.columns and 'amount' in df.columns and 'quantity' in df.columns:
            df['unit_price'] = df['amount'] / df['quantity']
            df['unit_price'] = df['unit_price'].fillna(0)
            print("💡 Calculated 'unit_price' from amount/quantity")
    
    # Calculate amount if missing but unit_price and quantity exist
        if 'amount' not in df.columns and 'unit_price' in df.columns and 'quantity' in df.columns:
            df['amount'] = df['unit_price'] * df['quantity']
            df['amount'] = df['amount'].fillna(0)
            print("💡 Calculated 'amount' from unit_price * quantity")
        
        return df
    
    def _clean_data(self):
        """Clean and prepare data for analysis"""
        
        df = self.standardized_df.copy()
        
        # Convert date column to datetime
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
        
        # Handle time column if it exists
        if 'transaction_time' in df.columns:
            try:
                df['transaction_time'] = pd.to_datetime(df['transaction_time'], format='%H:%M:%S', errors='coerce').dt.time
            except:
                # Try other common formats
                df['transaction_time'] = pd.to_datetime(df['transaction_time'], errors='coerce').dt.time
        
        # Convert numeric columns
        for col in ['quantity', 'amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        if 'unit_price' in df.columns:
            df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
        
        # Remove rows with missing critical data
        initial_len = len(df)
        df = df.dropna(subset=['transaction_date', 'amount'])
        removed = initial_len - len(df)
        
        if removed > 0:
            print(f"🧹 Removed {removed} rows with missing critical data")
        
        # Remove rows with invalid values
        df = df[df['amount'] > 0]
        df = df[df['quantity'] > 0]
        
        # Sort by date (and time if available)
        if 'transaction_time' in df.columns:
            df = df.sort_values(['transaction_date', 'transaction_time']).reset_index(drop=True)
        else:
            df = df.sort_values('transaction_date').reset_index(drop=True)
        
        print(f"✅ Data cleaned: {len(df)} valid transactions ready for analysis\n")
        
        return df


# Convenience function
def load_transaction_data(filepath):
    """
    Quick function to load and validate data
    
    Returns:
        tuple: (dataframe, validation_result)
    """
    loader = DataLoader()
    return loader.load(filepath)