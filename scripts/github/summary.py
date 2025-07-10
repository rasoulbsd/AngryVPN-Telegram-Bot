#!/usr/bin/env python3
"""
Show summary of created GitHub issues
"""

import subprocess
import json


def get_issues():
    """Get all issues from GitHub"""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--json", "title,number,labels,state"],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get issues: {e.stderr}")
        return []


def main():
    issues = get_issues()
    
    if not issues:
        print("❌ No issues found or failed to retrieve issues")
        return
    
    print(f"📊 Found {len(issues)} issues:")
    print("=" * 60)
    
    # Group by labels
    categories = {
        "Infrastructure": [],
        "Bot Functions": [],
        "Admin Features": [],
        "User Profile": [],
        "Additional Improvements": []
    }
    
    for issue in issues:
        labels = [label["name"] for label in issue["labels"]]
        
        if "infrastructure" in labels:
            categories["Infrastructure"].append(issue)
        elif "bot-functions" in labels:
            categories["Bot Functions"].append(issue)
        elif "admin" in labels:
            categories["Admin Features"].append(issue)
        elif "user-profile" in labels:
            categories["User Profile"].append(issue)
        else:
            categories["Additional Improvements"].append(issue)
    
    for category, category_issues in categories.items():
        if category_issues:
            print(f"\n🔹 {category} ({len(category_issues)} issues):")
            for issue in category_issues:
                labels_str = ", ".join([label["name"] for label in issue["labels"]])
                print(f"  • #{issue['number']}: {issue['title']}")
                print(f"    Labels: {labels_str}")
    
    print(f"\n🎉 Total: {len(issues)} issues created successfully!")


if __name__ == "__main__":
    main() 