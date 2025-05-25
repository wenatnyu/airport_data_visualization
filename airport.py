import pandas as pd
from typing import List, Any

class Airport:
    def __init__(self, csv_file_path: str):
        """
        Initialize an Airport object with data from a CSV file.
        
        Args:
            csv_file_path (str): Path to the CSV file containing airport data
        """
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Get the name from the first non-null value in the first column
        self.name = df.iloc[1, 0]
        
        # Get field names by combining values from rows 4 and 5 (0-based index)
        self.field_names = []
        for col in df.columns:
            field_name = f"{df.iloc[2, df.columns.get_loc(col)]} {df.iloc[3, df.columns.get_loc(col)]}"
            self.field_names.append(field_name)
        
        # Get values, excluding null rows
        # Start from row 6 (0-based index) to skip header rows
        self.values = df.iloc[6:].dropna(how='all').values.tolist()
        
        # Initialize empty derived values list
        self.derived_values: List[Any] = []
    
    def __str__(self) -> str:
        """String representation of the Airport object."""
        return f"Airport: {self.name}\nFields: {self.field_names}\nNumber of rows: {len(self.values)}" 

if __name__ == "__main__":
    airport = Airport("./uploads/raw_data.csv")
    print(airport)
