#!/usr/bin/env python3
"""
Create GitHub issues for bot function tasks
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
        labels = ["bot-functions", "enhancement"]
    
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
            "title": "Add Monitoring Option to Bot",
            "body": """## Overview
Add monitoring capabilities to track bot performance and user activity.

## Requirements
- Real-time bot performance monitoring
- User activity tracking
- Error rate monitoring
- Response time metrics
- Usage statistics

## Features
- Dashboard for monitoring
- Alert system for issues
- Performance metrics
- User behavior analytics
- Error tracking and reporting

## Implementation
- [ ] Set up monitoring infrastructure
- [ ] Add performance tracking
- [ ] Create monitoring dashboard
- [ ] Implement alert system
- [ ] Add usage analytics

## Acceptance Criteria
- [ ] Real-time monitoring works
- [ ] Performance metrics are accurate
- [ ] Alerts trigger appropriately
- [ ] Dashboard is accessible""",
            "labels": ["bot-functions", "monitoring", "enhancement"]
        },
        {
            "title": "Add Back Buttons in Menu Navigation",
            "body": """## Overview
Implement back button functionality throughout the bot menu system.

## Requirements
- Back button in all submenus
- Consistent navigation experience
- Return to previous menu level
- Clear navigation hierarchy

## Implementation
- [ ] Add back button handlers
- [ ] Implement menu state management
- [ ] Create navigation stack
- [ ] Update all menu flows
- [ ] Test navigation consistency

## Acceptance Criteria
- [ ] Back buttons work in all menus
- [ ] Navigation is intuitive
- [ ] No broken navigation flows
- [ ] Consistent user experience""",
            "labels": ["bot-functions", "ui/ux", "enhancement"]
        },
        {
            "title": "Enhance Ticketing System with User Questions",
            "body": """## Overview
Improve ticketing system by asking structured questions from users.

## Requirements
- Pre-defined question sets
- Dynamic question flow
- Better ticket categorization
- Faster issue resolution

## Features
- Question templates for common issues
- Conditional question flow
- Automatic ticket categorization
- Escalation based on answers

## Implementation
- [ ] Design question templates
- [ ] Implement dynamic flow
- [ ] Add categorization logic
- [ ] Create escalation rules
- [ ] Test question flows

## Acceptance Criteria
- [ ] Questions help categorize issues
- [ ] Flow is user-friendly
- [ ] Tickets are properly categorized
- [ ] Resolution time improves""",
            "labels": ["bot-functions", "support", "enhancement"]
        },
        {
            "title": "Review and Test Organization Functionalities",
            "body": """## Overview
Comprehensive review and testing of organization features for compatibility 
and security.

## Current Concerns
- New features may be incompatible with org structure
- Security/privacy concerns with user access
- Potential data access issues
- Organization boundary violations

## Requirements
- Security audit of org features
- Compatibility testing
- Privacy protection measures
- Access control review

## Implementation
- [ ] Audit organization features
- [ ] Test compatibility
- [ ] Implement access controls
- [ ] Add privacy protections
- [ ] Document security measures

## Acceptance Criteria
- [ ] All org features are secure
- [ ] No privacy violations
- [ ] Proper access controls
- [ ] Compatibility confirmed""",
            "labels": ["bot-functions", "security", "testing"]
        },
        {
            "title": "Implement Tutorials Flow",
            "body": """## Overview
Create comprehensive tutorial system to help users understand bot features.

## Requirements
- Step-by-step tutorials
- Interactive learning
- Feature explanations
- User onboarding

## Features
- Welcome tutorial for new users
- Feature-specific tutorials
- Interactive guides
- Progress tracking

## Implementation
- [ ] Design tutorial content
- [ ] Create interactive flows
- [ ] Add progress tracking
- [ ] Implement tutorial triggers
- [ ] Test tutorial effectiveness

## Acceptance Criteria
- [ ] Tutorials are helpful
- [ ] Users complete tutorials
- [ ] Feature adoption increases
- [ ] Support requests decrease""",
            "labels": ["bot-functions", "onboarding", "enhancement"]
        },
        {
            "title": "Remove First Button from Main Menu",
            "body": """## Overview
Remove the first button from the main menu as requested.

## Requirements
- Remove specific button
- Maintain menu functionality
- Update navigation flow
- Test menu layout

## Implementation
- [ ] Identify first button
- [ ] Remove button code
- [ ] Update menu layout
- [ ] Test navigation
- [ ] Verify no broken links

## Acceptance Criteria
- [ ] First button is removed
- [ ] Menu still works properly
- [ ] No broken navigation
- [ ] Layout looks good""",
            "labels": ["bot-functions", "ui/ux", "cleanup"]
        }
    ]
    
    print("🚀 Creating bot function issues...")
    
    created_count = 0
    for issue in issues:
        if create_issue(issue["title"], issue["body"], issue["labels"]):
            created_count += 1
    
    print(f"✅ Created {created_count} new bot function issues")


if __name__ == "__main__":
    main() 