#!/usr/bin/env python3
"""
Create GitHub issues for user profile tasks
"""

import subprocess
import json


def check_issue_exists(title):
    """Check if an issue with the given title already exists"""
    try:
        # Get all issues (open and closed)
        result = subprocess.run(
            ["gh", "issue", "list", "--state", "all", "--json", "title"],
            capture_output=True, text=True, check=True
        )
        issues = json.loads(result.stdout)
        
        # Check if any issue has the same title
        for issue in issues:
            if issue["title"] == title:
                return True
        return False
    except subprocess.CalledProcessError:
        return False


def create_issue(title, body, labels=None):
    """Create a GitHub issue if it doesn't already exist"""
    if labels is None:
        labels = ["user-profile", "enhancement"]
    
    # Check if issue already exists
    if check_issue_exists(title):
        print(f"ℹ️  Issue already exists: {title}")
        return None
    
    cmd = [
        "gh", "issue", "create",
        "--title", title,
        "--body", body,
        "--label", ",".join(labels)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              check=True)
        print(f"✅ Created issue: {title}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create issue '{title}': {e.stderr}")
        return None


def main():
    issues = [
        {
            "title": "Add Personal Referral Code System",
            "body": """## Overview
Implement personal referral code system for users.

## Requirements
- Unique referral codes per user
- Referral tracking system
- Referral rewards
- Referral statistics

## Features
- Generate unique codes
- Track referrals
- Reward system
- Referral analytics

## Implementation
- [ ] Create referral code generation
- [ ] Implement referral tracking
- [ ] Add reward system
- [ ] Create referral dashboard
- [ ] Add referral statistics

## Acceptance Criteria
- [ ] Each user has unique code
- [ ] Referrals are tracked
- [ ] Rewards are given
- [ ] Statistics are accurate""",
            "labels": ["user-profile", "referral", "enhancement"]
        },
        {
            "title": "Add Referral Code Revocation Function",
            "body": """## Overview
Allow users to revoke their personal referral codes.

## Requirements
- Referral code revocation
- Security confirmation
- Revocation history
- New code generation

## Features
- Secure revocation process
- Confirmation dialogs
- Revocation logging
- New code generation

## Implementation
- [ ] Create revocation interface
- [ ] Add security confirmations
- [ ] Implement revocation logging
- [ ] Add new code generation
- [ ] Test revocation process

## Acceptance Criteria
- [ ] Codes can be revoked securely
- [ ] Confirmation is required
- [ ] New codes are generated
- [ ] Process is logged""",
            "labels": ["user-profile", "referral", "security"]
        },
        {
            "title": "Add Estimated GB Display on User Wallet",
            "body": """## Overview
Show estimated GB usage on user wallet interface.

## Requirements
- GB usage estimation
- Real-time calculation
- Usage history
- Usage predictions

## Features
- Usage estimation algorithm
- Historical usage tracking
- Usage predictions
- Usage alerts

## Implementation
- [ ] Create usage estimation
- [ ] Add historical tracking
- [ ] Implement predictions
- [ ] Add usage alerts
- [ ] Test accuracy

## Acceptance Criteria
- [ ] Estimates are accurate
- [ ] History is tracked
- [ ] Predictions work
- [ ] Alerts are timely""",
            "labels": ["user-profile", "wallet", "enhancement"]
        },
        {
            "title": "Add ISP/Phone/Client Data Collection in User Profile",
            "body": """## Overview
Allow users to set ISP, phone, and client information in their profile.

## Requirements
- ISP information field
- Phone number field
- Client data field
- Profile management

## Features
- Profile data collection
- Data validation
- Privacy controls
- Data management

## Implementation
- [ ] Add profile fields
- [ ] Implement data validation
- [ ] Add privacy controls
- [ ] Create data management
- [ ] Test data handling

## Acceptance Criteria
- [ ] Users can set their data
- [ ] Data is validated
- [ ] Privacy is protected
- [ ] Data is manageable""",
            "labels": ["user-profile", "data-collection", "enhancement"]
        },
        {
            "title": "Add Language Change Option for Users",
            "body": """## Overview
Allow users to change their language preference.

## Requirements
- Language selection interface
- Multiple language support
- Language persistence
- Dynamic language switching

## Features
- Language selection menu
- Language persistence
- Dynamic content switching
- Language preferences

## Implementation
- [ ] Create language selector
- [ ] Implement language persistence
- [ ] Add dynamic switching
- [ ] Test all languages
- [ ] Add language preferences

## Acceptance Criteria
- [ ] Users can change language
- [ ] Language persists
- [ ] All content is translated
- [ ] Switching works smoothly""",
            "labels": ["user-profile", "localization", "enhancement"]
        },
        {
            "title": "Add Configuration Revocation for Users",
            "body": """## Overview
Allow users to revoke their VPN configurations.

## Requirements
- Configuration revocation
- Security confirmation
- Revocation history
- New configuration generation

## Features
- Secure revocation process
- Confirmation dialogs
- Revocation logging
- New config generation

## Implementation
- [ ] Create revocation interface
- [ ] Add security confirmations
- [ ] Implement revocation logging
- [ ] Add new config generation
- [ ] Test revocation process

## Acceptance Criteria
- [ ] Configs can be revoked
- [ ] Confirmation is required
- [ ] New configs are generated
- [ ] Process is secure""",
            "labels": ["user-profile", "security", "enhancement"]
        }
    ]
    
    print("🚀 Creating user profile issues...")
    
    created_count = 0
    for issue in issues:
        if create_issue(issue["title"], issue["body"], issue["labels"]):
            created_count += 1
    
    print(f"✅ Created {created_count} new user profile issues")


if __name__ == "__main__":
    main() 