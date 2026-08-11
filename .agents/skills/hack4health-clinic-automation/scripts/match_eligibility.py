import os
import sys
import argparse
from datetime import datetime
import json

def calculate_age(dob_str):
    # Formats could be DD/MM/YY or DD/MM/YYYY
    try:
        parts = dob_str.split('/')
        if len(parts) != 3:
            return None
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        if year < 100:
            # 2-digit year
            if year > 26: # assume 1900s
                year += 1900
            else: # assume 2000s
                year += 2000
        # Reference year for hackathon is 2026
        return 2026 - year
    except Exception:
        return None

def match_eligibility(insurer_code, dob_str, gender="Male"):
    insurer_code = insurer_code.strip().upper()
    age = calculate_age(dob_str) if dob_str else None
    
    result = {
        "insurer_code": insurer_code,
        "age": age,
        "gender": gender,
        "package_code": "UNKNOWN",
        "package_name": "Unknown Package / Custom Referral",
        "covered_tests": [],
        "notes": ""
    }
    
    if insurer_code == "BLPHS": # Bluepeak Wellness Package
        result["package_name"] = "BluePeak Wellness Package"
        if age is not None:
            if age < 40:
                result["package_code"] = "WELL1"
                result["package_name"] += " - Essential Screen (Under 40)"
                result["covered_tests"] = ["Complete History Taking", "Complete Physical Examination", "BMI and Fat Composition", "Blood pressure measurement", "Full Blood Count", "Cholesterol screening"]
            elif 40 <= age <= 59:
                result["package_code"] = "WELL2"
                result["package_name"] += " - Comprehensive Screen (40-59)"
                result["covered_tests"] = ["Complete History Taking", "Complete Physical Examination", "BMI and Fat Composition", "Blood pressure measurement", "Full Blood Count", "Cholesterol screening", "Liver function screening", "Kidney function screening", "Thyroid function screening", "Resting ECG", "Medical Report Consultation"]
            else:
                result["package_code"] = "WELL3"
                result["package_name"] += " - Executive Screen (60 and above)"
                result["covered_tests"] = ["Complete History Taking", "Complete Physical Examination", "BMI and Fat Composition", "Blood pressure measurement", "Full Blood Count", "Cholesterol screening", "Liver function screening", "Kidney function screening", "Thyroid function screening", "Resting ECG", "Liver Cancer Marker", "Medical Report Consultation"]
        else:
            result["notes"] = "Age could not be calculated. Please check date of birth."
            
    elif insurer_code == "BLPDE": # Bluepeak Underwriting
        result["package_code"] = "BLPDE_UW"
        result["package_name"] = "Bluepeak Underwriting Requirements"
        result["covered_tests"] = ["Full Medical Examination (No Paramedics)", "Anti-HIV Test (BP#HIV)"]
        result["notes"] = "Note to clinic: Send samples to Bluepeak Lab. Contact: 6278 0000. Check address proof."
        
    elif insurer_code == "MOL0199VME": # Ministry of Learning
        result["package_name"] = "Ministry of Learning Civil Service Medical Scheme"
        if age is not None:
            if age <= 24:
                result["package_code"] = "PEE225"
                result["package_name"] += " (24 and below)"
            elif 25 <= age <= 49:
                result["package_code"] = "PEE226"
                result["package_name"] += " (25 to 49)"
            else:
                result["package_code"] = "PEE224"
                result["package_name"] += " (50 and above)"
            result["covered_tests"] = ["Pre-employment medical examination"]
        else:
            result["notes"] = "Age could not be calculated. Defaulting to general MOL pre-employment exam."
            
    elif insurer_code == "MRDEB": # Meridian Life
        result["package_code"] = "MRDEB_UW"
        result["package_name"] = "Meridian Life Medical Referral Letter"
        result["covered_tests"] = ["Chest X-Ray", "Meridian Life# 10 - HIV Antibody Test", "Treadmill ECG"]
        result["notes"] = "Please forward medical underwriting requirements to eb.uw@mail.meridianlife.com.sg"
        
    elif insurer_code == "EVWME": # Everwell Health check-up
        result["package_code"] = "EVWME_VOUCHER"
        result["package_name"] = "Everwell Health Check-up Voucher"
        result["covered_tests"] = ["Medical Examination", "Lipid Profile", "UFEME (Urine)", "Resting ECG"]
        
    elif insurer_code == "EVWPA": # Everwell Policy invitation
        result["package_code"] = "EVWPA_UW"
        result["package_name"] = "Everwell Adult Medical Examination"
        result["covered_tests"] = ["Adult Medical Examination"]
        
    elif insurer_code == "NSTNBU": # Northstar Life
        result["package_code"] = "NSTNBU_UW"
        result["package_name"] = "Northstar Life Underwriting Follow Up"
        result["covered_tests"] = ["Two repeat Urine Examination and Microscopy on different days"]
        result["notes"] = "Client must present NRIC/Passport and this letter."
        
    else:
        result["notes"] = f"Unknown insurer/TPA code '{insurer_code}'. Manual verification required."
        
    return result

def main():
    parser = argparse.ArgumentParser(description="Match patient demographics and insurer code to package eligibility")
    parser.add_argument("--code", required=True, help="Insurer/TPA Code (e.g. BLPHS, MOL0199VME)")
    parser.add_argument("--dob", required=True, help="Patient DOB in DD/MM/YY or DD/MM/YYYY format")
    parser.add_argument("--gender", default="Male", choices=["Male", "Female"], help="Patient gender")
    
    args = parser.parse_args()
    
    eligibility = match_eligibility(args.code, args.dob, args.gender)
    print(json.dumps(eligibility, indent=2))

if __name__ == "__main__":
    main()
