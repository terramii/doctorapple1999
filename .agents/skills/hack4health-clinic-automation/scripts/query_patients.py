import os
import sys
import argparse
import pandas as pd
import json

def search_patients(csv_path, name=None, id_number=None):
    if not os.path.exists(csv_path):
        print(f"Error: Patient database not found at '{csv_path}'", file=sys.stderr)
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    
    # Fill NaN values for easier processing
    df = df.fillna("")
    
    results = df
    
    if id_number:
        # Clean ID number for search
        id_number_clean = id_number.strip().upper()
        results = results[results['NRIC/FIN/Passport Number'].str.upper().str.contains(id_number_clean, na=False)]
        
    if name:
        name_clean = name.strip().lower()
        results = results[results['Full Name'].str.lower().str.contains(name_clean, na=False)]
        
    return results.to_dict(orient="records")

def main():
    parser = argparse.ArgumentParser(description="Query the synthetic patient registration database")
    parser.add_argument("--db", default="Data/Data/patient_registration_synthetic.csv", help="Path to patient database CSV")
    parser.add_argument("--name", help="Patient name to search for (partial match)")
    parser.add_argument("--id", help="NRIC/FIN/Passport number to search for (partial match)")
    
    args = parser.parse_args()
    
    if not args.name and not args.id:
        print("Error: You must provide either --name or --id", file=sys.stderr)
        sys.exit(1)
        
    # Make path relative to workspace root if it's relative
    csv_path = args.db
    if not os.path.isabs(csv_path):
        # assume running from workspace root
        csv_path = os.path.abspath(csv_path)
        
    matches = search_patients(csv_path, name=args.name, id_number=args.id)
    print(json.dumps(matches, indent=2))

if __name__ == "__main__":
    main()
