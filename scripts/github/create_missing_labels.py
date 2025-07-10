#!/usr/bin/env python3
"""
Create missing GitHub labels
"""

import subprocess


def create_label(name, color, description):
    """Create a GitHub label"""
    cmd = [
        "gh", "label", "create", name,
        "--color", color,
        "--description", description
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              check=True)
        print(f"✅ Created label: {name}")
        return True
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr:
            print(f"ℹ️  Label already exists: {name}")
            return True
        else:
            print(f"❌ Failed to create label '{name}': {e.stderr}")
            return False


def main():
    labels = [
        ("monitoring", "0366d6", "Monitoring and analytics features"),
        ("ui/ux", "28a745", "User interface and experience"),
        ("onboarding", "0075ca", "User onboarding features"),
        ("cleanup", "fbca04", "Code cleanup and maintenance"),
        ("billing", "d73a49", "Billing and payment features"),
        ("servers", "0e8a16", "Server management features"),
        ("referral", "0366d6", "Referral system features"),
        ("wallet", "28a745", "Wallet and balance features"),
        ("data-collection", "0075ca", "Data collection features"),
        ("localization", "fbca04", "Localization and translation"),
        ("stripe", "d73a49", "Stripe payment integration"),
        ("logging", "0e8a16", "Logging and debugging"),
        ("error-handling", "0366d6", "Error handling improvements"),
        ("ci/cd", "28a745", "Continuous integration/deployment"),
        ("rate-limiting", "0075ca", "Rate limiting features"),
        ("analytics", "fbca04", "Analytics and tracking"),
        ("tracking", "d73a49", "User tracking features"),
        ("backup", "0e8a16", "Backup and recovery"),
        ("recovery", "0366d6", "Recovery and restoration"),
        ("translation", "28a745", "Translation features"),
        ("notifications", "0075ca", "Notification system"),
        ("communication", "fbca04", "Communication features"),
        ("improvement", "d73a49", "General improvements"),
        ("enhancement", "0e8a16", "Feature enhancements"),
        ("bug", "0366d6", "Bug fixes"),
        ("automation", "28a745", "Automation features")
    ]
    
    print("🚀 Creating missing labels...")
    
    success_count = 0
    total_labels = len(labels)
    
    for name, color, description in labels:
        if create_label(name, color, description):
            success_count += 1
    
    print(f"\n✅ Created {success_count}/{total_labels} labels successfully")


if __name__ == "__main__":
    main() 