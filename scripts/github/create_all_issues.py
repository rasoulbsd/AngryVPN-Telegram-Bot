#!/usr/bin/env python3
"""
Master script to create all GitHub issues
"""

import subprocess
import os


def run_script(script_name):
    """Run a script and return success status"""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run([script_path], capture_output=True, text=True, 
                              check=True)
        print(f"✅ Successfully ran {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run {script_name}: {e.stderr}")
        return False


def main():
    scripts = [
        "create_infra_issues.py",
        "create_bot_functions_issues.py", 
        "create_admin_issues.py",
        "create_user_profile_issues.py",
        "create_additional_issues.py"
    ]
    
    print("🚀 Creating all GitHub issues...")
    print("=" * 50)
    
    success_count = 0
    total_scripts = len(scripts)
    
    for script in scripts:
        print(f"\n📝 Running {script}...")
        if run_script(script):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Completed! {success_count}/{total_scripts} scripts ran successfully")
    
    if success_count == total_scripts:
        print("🎉 All issues created successfully!")
    else:
        print("⚠️  Some scripts failed. Check the output above.")


if __name__ == "__main__":
    main() 