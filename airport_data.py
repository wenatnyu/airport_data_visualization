import pandas as pd
from datetime import datetime
import numpy as np
import os
import glob

class AirportData:
    def __init__(self, csv_path):
        # Read the CSV file
        df = pd.read_csv(csv_path, header=None)
        
        # Get the name from first row, first column
        self.name = df.iloc[0, 0]
        
        # Get the field names by combining second and third rows
        self.fields = []
        for i in range(10):
            field1 = str(df.iloc[1, i]) if pd.notna(df.iloc[1, i]) else ""
            field2 = str(df.iloc[2, i]) if pd.notna(df.iloc[2, i]) else ""
            self.fields.append(field1 + field2)
        
        # Process the data rows (starting from row 4)
        data_rows = df.iloc[3:].values
        
        # Initialize the 2D array
        self.data = []
        
        for row in data_rows:
            if pd.isna(row[0]):  # Skip empty rows
                continue
                
            # Convert date string to datetime
            date_str = row[0]
            try:
                # Try parsing full date format (YYYY-MM-DD)
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                try:
                    # Fallback to month-day format (MM-DD)
                    date = datetime.strptime(date_str, "%m-%d")
                except ValueError:
                    print(f"Warning: Could not parse date {date_str}, skipping row")
                    continue
            
            # Create a new row with date and numeric values
            new_row = [date]
            
            # Add integer values (columns 1-6)
            for i in range(1, 7):
                try:
                    value = int(float(row[i])) if pd.notna(row[i]) else 0
                    new_row.append(value)
                except (ValueError, TypeError):
                    new_row.append(0)
            
            # Add float values (columns 7-9)
            for i in range(7, 10):
                try:
                    value = float(row[i]) if pd.notna(row[i]) else 0.0
                    new_row.append(value)
                except (ValueError, TypeError):
                    new_row.append(0.0)
            
            self.data.append(new_row)
        
        # Convert to numpy array
        self.data = np.array(self.data, dtype=object)
    
    def __str__(self):
        return f"AirportData(name='{self.name}', fields={self.fields}, data_shape={self.data.shape})"

def load_all_airports(uploads_dir="uploads"):
    """
    Load all airport CSV files from the uploads directory and return a list of AirportData objects.
    
    Args:
        uploads_dir (str): Path to the directory containing airport CSV files
        
    Returns:
        list: List of AirportData objects
    """
    # Get all CSV files in the uploads directory
    csv_files = glob.glob(os.path.join(uploads_dir, "*.csv"))
    
    # Create a list to store AirportData objects
    airports = []
    
    # Process each CSV file
    for csv_file in csv_files:
        try:
            airport = AirportData(csv_file)
            airports.append(airport)
            print(f"Successfully loaded {airport.name}")
        except Exception as e:
            print(f"Error loading {csv_file}: {str(e)}")
    
    return airports

if __name__ == "__main__":
    # Load all airports
    airports = load_all_airports()
    
    # Print summary of loaded airports
    print("\nLoaded airports summary:")
    for airport in airports:
        print(f"- {airport.name}: {airport.data.shape[0]} days of data")
