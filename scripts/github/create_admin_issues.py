#!/usr/bin/env python3
"""
Create GitHub issues for admin feature tasks
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
        labels = ["admin", "enhancement"]
    
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
            "title": "Add Admin Management Functions in Bot",
            "body": """## Overview
Implement bot functions to add and remove administrators.

## Requirements
- Add new admins through bot interface
- Remove existing admins
- Admin permission management
- Admin role assignment

## Features
- Admin invitation system
- Permission level management
- Admin removal with confirmation
- Admin list management

## Implementation
- [ ] Create admin invitation flow
- [ ] Implement admin removal
- [ ] Add permission management
- [ ] Create admin list view
- [ ] Add confirmation dialogs

## Acceptance Criteria
- [ ] Admins can be added via bot
- [ ] Admins can be removed via bot
- [ ] Permissions are properly managed
- [ ] Security is maintained""",
            "labels": ["admin", "security", "enhancement"]
        },
        {
            "title": "Edit Manual Charging Admin Bot Function",
            "body": """## Overview
Improve the manual charging function for administrators.

## Requirements
- Enhanced manual charging interface
- Better user selection
- Improved charge amount input
- Charge history tracking

## Features
- User search and selection
- Flexible charge amounts
- Charge reason tracking
- Admin audit trail

## Implementation
- [ ] Improve user selection interface
- [ ] Add charge amount validation
- [ ] Implement charge history
- [ ] Add admin audit logging
- [ ] Create charge confirmation

## Acceptance Criteria
- [ ] Manual charging is user-friendly
- [ ] Charge amounts are validated
- [ ] History is properly tracked
- [ ] Admin actions are logged""",
            "labels": ["admin", "billing", "enhancement"]
        },
        {
            "title": "Add Server Activation/Deactivation Bot Functions",
            "body": """## Overview
Add bot functions to activate and deactivate servers.

## Requirements
- Activate servers through bot
- Deactivate servers through bot
- Server status management
- Server health monitoring

## Features
- Server status toggle
- Server health checks
- Server list management
- Status change notifications

## Implementation
- [ ] Create server management interface
- [ ] Implement status toggle
- [ ] Add health monitoring
- [ ] Create server list view
- [ ] Add status notifications

## Acceptance Criteria
- [ ] Servers can be activated/deactivated
- [ ] Status changes are immediate
- [ ] Health monitoring works
- [ ] Notifications are sent""",
            "labels": ["admin", "servers", "enhancement"]
        }
    ]
    
    print("🚀 Creating admin feature issues...")
    
    created_count = 0
    for issue in issues:
        if create_issue(issue["title"], issue["body"], issue["labels"]):
            created_count += 1
    
    print(f"✅ Created {created_count} new admin feature issues")


if __name__ == "__main__":
    main() 