import os
import pandas as pd
import json

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(base_dir), "Data", "Data")
    
    # 1. Load patient registration CSV
    pat_csv = os.path.join(data_dir, "patient_registration_synthetic.csv")
    df_pat = pd.read_csv(pat_csv).fillna("")
    patients = df_pat.to_dict(orient="records")
    
    # 2. Load general surveys
    gen_csv = os.path.join(data_dir, "general_health_questionnaire_mock_patients.csv")
    df_gen = pd.read_csv(gen_csv).fillna("")
    surveys_gen = df_gen.to_dict(orient="records")
    
    # 3. Load occupational surveys
    occ_csv = os.path.join(data_dir, "occupational_health_questionnaire_mock_patients.csv")
    df_occ = pd.read_csv(occ_csv).fillna("")
    surveys_occ = df_occ.to_dict(orient="records")
    
    # 4. Generate db.js contents
    js_content = f"""// Doctor Apple Synthetic Database Bundle
// Generated automatically from CSV files

const PATIENT_DB = {json.dumps(patients, indent=2)};

const MOCK_SURVEYS_GENERAL = {json.dumps(surveys_gen, indent=2)};

const MOCK_SURVEYS_OCCUPATIONAL = {json.dumps(surveys_occ, indent=2)};
"""
    
    output_js = os.path.join(base_dir, "db.js")
    with open(output_js, "w", encoding="utf-8") as f:
        f.write(js_content)
        
    print(f"[+] Successfully bundled databases into '{output_js}'")
    print(f"  - Patients: {len(patients)}")
    print(f"  - General Surveys: {len(surveys_gen)}")
    print(f"  - Occupational Surveys: {len(surveys_occ)}")

if __name__ == "__main__":
    main()
