import os
import sys
import argparse
import pandas as pd
import json

def get_id_type(id_val):
    id_val = id_val.strip().upper()
    if len(id_val) == 9 and (id_val.startswith(('S', 'T', 'F', 'G', 'M'))):
        return "NRIC/FIN"
    return "Passport"

def format_dob(dob_str):
    try:
        parts = dob_str.split('/')
        if len(parts) != 3:
            return dob_str
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        if year < 100:
            if year > 26:
                year += 1900
            else:
                year += 2000
        return f"{day:02d}/{month:02d}/{year:04d}"
    except Exception:
        return dob_str

def generate_prefill(csv_path, id_number, form_type="general", provider=None, location=None, screening_type=None):
    if not os.path.exists(csv_path):
        print(f"Error: Patient database not found at '{csv_path}'", file=sys.stderr)
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    df = df.fillna("")
    
    # Search for patient
    id_clean = id_number.strip().upper()
    match = df[df['NRIC/FIN/Passport Number'].str.upper() == id_clean]
    
    if match.empty:
        return {"error": f"Patient with ID '{id_number}' not found in database."}
        
    patient = match.iloc[0].to_dict()
    
    # Base demographic payload common to both questionnaires
    id_type = get_id_type(patient['NRIC/FIN/Passport Number'])
    
    payload = {
        "Name": patient['Full Name'],
        "Select One": id_type,
        "NRIC/FIN no.": patient['NRIC/FIN/Passport Number'] if id_type == "NRIC/FIN" else "",
        "Passport": patient['NRIC/FIN/Passport Number'] if id_type == "Passport" else "",
        "Date of Birth": format_dob(patient['Date of Birth (DD/MM/YY)']),
        "Email Address": patient['Email'],
        "Country code": "+65", # Default Singapore
        "Phone Number": str(patient['Contact - Mobile']) or str(patient['Contact - Home']) or str(patient['Contact - Office']),
        "Address": patient['Address'],
        "Postal Code": str(patient['Postal Code']).zfill(6) if patient['Postal Code'] else "",
        "Gender": "Male" if patient['Sex'].strip().lower() in ['m', 'male'] else "Female",
        "Ethnicity (Race)": "Asian" # default fallback
    }
    
    # Clean phone number
    if payload["Phone Number"].endswith(".0"):
        payload["Phone Number"] = payload["Phone Number"][:-2]
        
    # Mapping drug allergies
    allergy = patient.get("Drug Allergy", "").strip()
    if allergy and allergy.lower() != "none" and allergy.lower() != "nil":
        payload["Do you have any drug allergies?"] = "Yes"
        payload["Please provide name(s) of the drug(s)"] = allergy
    else:
        payload["Do you have any drug allergies?"] = "No"
        
    if form_type.lower() == "general":
        payload["Health Screening Provider"] = provider or "Parkway Shenton Medical Clinic"
        payload["Health Screening Location"] = location or "Republic Plaza"
        
    elif form_type.lower() == "occupational":
        payload["Occupational Health Screening Type"] = screening_type or ["Pre/Re Employment"]
        payload["Health Screening Location"] = location or "Parkway Shenton Medical Clinic (Republic Plaza)"
        # Convert drug allergy mapping to Occupational Health schema:
        payload["Personal - Current Medications"] = "Yes" if allergy else "No"
        
    return payload

def main():
    parser = argparse.ArgumentParser(description="Generate Parkway Shenton Questionnaire pre-fill JSON payload")
    parser.add_argument("--db", default="Data/Data/patient_registration_synthetic.csv", help="Path to patient database CSV")
    parser.add_argument("--id", required=True, help="Patient NRIC/FIN/Passport Number")
    parser.add_argument("--type", default="general", choices=["general", "occupational"], help="Screening questionnaire type")
    parser.add_argument("--provider", help="Health Screening Provider (for General form)")
    parser.add_argument("--location", help="Health Screening Location")
    parser.add_argument("--hazard", action="append", help="Occupational hazards (e.g. Asbestos Hazard) - repeat option for multiple")
    
    args = parser.parse_args()
    
    csv_path = args.db
    if not os.path.isabs(csv_path):
        csv_path = os.path.abspath(csv_path)
        
    payload = generate_prefill(
        csv_path=csv_path,
        id_number=args.id,
        form_type=args.type,
        provider=args.provider,
        location=args.location,
        screening_type=args.hazard
    )
    
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
