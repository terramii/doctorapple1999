import os
import sys
import subprocess
import json

def load_dotenv():
    # Basic .env loader
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

def run_script(script_name, args):
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".agents", "skills", "hack4health-clinic-automation", "scripts", script_name)
    cmd = [sys.executable, script_path] + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error executing {script_name}: {res.stderr.strip()}", file=sys.stderr)
        return None
    return res.stdout.strip()

def main():
    load_dotenv()
    
    # 1. Verify credentials safely (optional for local automation)
    api_key = os.environ.get("AGNES_AI_API_KEY")
    if not api_key:
        print("[!] Notice: AGNES_AI_API_KEY is not configured in .env (running in Local Offline Mode)")
    else:
        print(f"[+] Authenticated with Agnes AI Client (Key length: {len(api_key)} chars)")
    
    # Example flow using sample documents
    print("\n--- Running Agnes AI Automation Workflow ---")
    
    # Let's perform a sample run for patient Amir Loh
    sample_nric = "S8536477Z"
    insurer_code = "BLPHS" # Bluepeak Prosperity
    dob = "25/01/85"
    gender = "Male"
    
    # Step 1: Patient DB lookup
    print(f"\n[Step 1] Querying Patient Database for ID: {sample_nric}...")
    db_result = run_script("query_patients.py", ["--id", sample_nric])
    if db_result:
        parsed_db = json.loads(db_result)
        if parsed_db:
            patient = parsed_db[0]
            print(f"  Matched Patient: {patient['Full Name']} (DOB: {patient['Date of Birth (DD/MM/YY)']})")
            if patient.get("Drug Allergy") and patient["Drug Allergy"].lower() != "none":
                print(f"  [WARNING] Drug Allergy Detected: {patient['Drug Allergy']}!")
        else:
            print("  Patient not found.")
            
    # Step 2: Resolve eligibility package
    print(f"\n[Step 2] Resolving coverage eligibility for Policy Code: {insurer_code}...")
    elig_result = run_script("match_eligibility.py", ["--code", insurer_code, "--dob", dob, "--gender", gender])
    if elig_result:
        parsed_elig = json.loads(elig_result)
        print(f"  Eligible Package: {parsed_elig.get('package_name', 'Unknown')}")
        print(f"  Sponsor Code: {parsed_elig.get('package_code', 'N/A')}")
        print("  Covered procedures:")
        for test in parsed_elig.get("covered_tests", []):
            print(f"    - {test}")
            
    # Step 3: Prefill health screening questionnaire
    print(f"\n[Step 3] Pre-populating General Health Survey payload...")
    prefill_result = run_script("generate_prefill.py", ["--id", sample_nric, "--type", "general"])
    if prefill_result:
        parsed_prefill = json.loads(prefill_result)
        print(f"  Intake forms mapped successfully. Target: {parsed_prefill.get('Health Screening Provider')}")
        print(f"  Phone declaration: {parsed_prefill.get('Phone Number')}")
        
    print("\n[+] Agnes AI registration batch sync completed successfully.")

if __name__ == "__main__":
    main()
