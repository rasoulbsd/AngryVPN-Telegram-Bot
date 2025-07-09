#!/usr/bin/env python3
"""
Interactive GitHub Issue Creator
Guides users through creating GitHub issues with all options.
"""

import subprocess
import json
import sys
from typing import List, Dict, Optional

# Issue templates for common types
ISSUE_TEMPLATES = {
    "bug": {
        "title": "🐛 Bug Report",
        "body": """## 🐛 Bug Description
Brief description of the bug.

## 🔍 Steps to Reproduce
1. 
2. 
3. 

## ✅ Expected Behavior
What should happen?

## ❌ Actual Behavior
What actually happens?

## 📱 Environment
- OS: 
- Browser: 
- Version: 

## 📸 Screenshots
If applicable, add screenshots to help explain the problem.

## 🔧 Additional Context
Add any other context about the problem here.""",
        "labels": ["bug"]
    },
    "feature": {
        "title": "✨ Feature Request",
        "body": """## ✨ Feature Description
Brief description of the feature you'd like to see.

## 🎯 Problem Statement
What problem does this feature solve?

## 💡 Proposed Solution
Describe the solution you'd like to see.

## 🔄 Alternative Solutions
Describe any alternative solutions you've considered.

## 📋 Additional Context
Add any other context, screenshots, or examples.""",
        "labels": ["enhancement"]
    },
    "improvement": {
        "title": "🔧 Improvement Request",
        "body": """## 🔧 Improvement Description
Brief description of the improvement.

## 🎯 Current State
Describe the current implementation.

## 💡 Proposed Changes
Describe the improvements you'd like to see.

## 📊 Impact
What impact will this have?

## 🔄 Implementation Notes
Any specific implementation details or considerations.""",
        "labels": ["enhancement"]
    },
    "documentation": {
        "title": "📚 Documentation Update",
        "body": """## 📚 Documentation Update
Brief description of the documentation changes needed.

## 📖 Current Documentation
What documentation currently exists?

## ✏️ Proposed Changes
What changes are needed?

## 🎯 Target Audience
Who will be reading this documentation?

## 📋 Additional Context
Any other relevant information.""",
        "labels": ["documentation"]
    },
    "task": {
        "title": "📋 Task",
        "body": """## 📋 Task Description
Brief description of the task.

## 🎯 Objective
What needs to be accomplished?

## ✅ Acceptance Criteria
- [ ] 
- [ ] 
- [ ] 

## 📅 Timeline
When does this need to be completed?

## 🔗 Related Issues
Link to any related issues or PRs.""",
        "labels": ["enhancement"]
    },
    "custom": {
        "title": "📝 Custom Issue",
        "body": """## 📝 Issue Description
Describe the issue here.

## 🔍 Additional Details
Add any additional details, context, or requirements.

## 📋 Tasks
- [ ] 
- [ ] 
- [ ] 

## 🎯 Goals
What are the main goals of this issue?

## 📅 Timeline
When does this need to be completed?""",
        "labels": []
    }
}

def get_existing_labels() -> List[Dict]:
    """Get existing labels from GitHub."""
    try:
        result = subprocess.run(
            ["gh", "api", "repos/:owner/:repo/labels"],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        print("⚠️  Could not fetch existing labels")
        return []

def create_issue(title: str, body: str, labels: List[str], assignees: List[str] = None) -> bool:
    """Create a GitHub issue."""
    try:
        cmd = ["gh", "issue", "create", "--title", title, "--body", body]
        
        if labels:
            cmd.extend(["--label", ",".join(labels)])
        
        if assignees:
            cmd.extend(["--assignee", ",".join(assignees)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Issue created successfully!")
        
        # Extract issue URL from output
        for line in result.stdout.split('\n'):
            if 'rasoulbsd/AngryVPN-Telegram-Bot#' in line:
                print(f"🔗 Issue URL: {line.strip()}")
                break
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create issue: {e.stderr}")
        return False

def select_issue_type() -> str:
    """Let user select issue type."""
    print("\n📝 Select Issue Type:")
    print("-" * 30)
    
    types = list(ISSUE_TEMPLATES.keys())
    for i, issue_type in enumerate(types, 1):
        emoji = "🐛" if issue_type == "bug" else "✨" if issue_type == "feature" else "🔧" if issue_type == "improvement" else "📚" if issue_type == "documentation" else "📋" if issue_type == "task" else "📝"
        print(f"{i}. {emoji} {issue_type.title()}")
    
    while True:
        try:
            choice = int(input(f"\nSelect type (1-{len(types)}): "))
            if 1 <= choice <= len(types):
                return types[choice - 1]
            else:
                print("❌ Invalid choice. Please try again.")
        except ValueError:
            print("❌ Please enter a valid number.")

def select_labels() -> List[str]:
    """Let user select labels."""
    labels = get_existing_labels()
    if not labels:
        print("⚠️  No labels available. You can add labels later.")
        return []
    
    print("\n🏷️  Select Labels:")
    print("-" * 30)
    
    selected_labels = []
    
    # Show available labels
    for i, label in enumerate(labels, 1):
        color_emoji = "🟢" if label.get("color") == "28a745" else "🔵"
        print(f"{i}. {color_emoji} {label['name']} - {label.get('description', 'No description')}")
    
    print(f"{len(labels) + 1}. Skip labels")
    
    while True:
        try:
            choice = input(f"\nSelect labels (comma-separated numbers, or {len(labels) + 1} to skip): ")
            if choice.strip() == str(len(labels) + 1):
                return []
            
            choices = [int(x.strip()) for x in choice.split(",")]
            for choice_num in choices:
                if 1 <= choice_num <= len(labels):
                    selected_labels.append(labels[choice_num - 1]["name"])
                else:
                    print(f"❌ Invalid choice: {choice_num}")
                    return []
            
            return selected_labels
        except ValueError:
            print("❌ Please enter valid numbers separated by commas.")

def select_assignees() -> List[str]:
    """Let user select assignees."""
    try:
        # Get repository collaborators
        result = subprocess.run(
            ["gh", "api", "repos/:owner/:repo/collaborators"],
            capture_output=True, text=True, check=True
        )
        collaborators = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        print("⚠️  Could not fetch collaborators.")
        return []
    
    if not collaborators:
        print("⚠️  No collaborators found.")
        return []
    
    print("\n👥 Select Assignees:")
    print("-" * 30)
    
    for i, collaborator in enumerate(collaborators, 1):
        print(f"{i}. {collaborator['login']} - {collaborator.get('name', 'No name')}")
    
    print(f"{len(collaborators) + 1}. Skip assignees")
    
    try:
        choice = input(f"\nSelect assignees (comma-separated numbers, or {len(collaborators) + 1} to skip): ")
        if choice.strip() == str(len(collaborators) + 1):
            return []
        
        choices = [int(x.strip()) for x in choice.split(",")]
        selected_assignees = []
        
        for choice_num in choices:
            if 1 <= choice_num <= len(collaborators):
                selected_assignees.append(collaborators[choice_num - 1]["login"])
            else:
                print(f"❌ Invalid choice: {choice_num}")
                return []
        
        return selected_assignees
    except ValueError:
        print("❌ Please enter valid numbers separated by commas.")
        return []

def edit_template(template: Dict) -> Dict:
    """Let user edit the template."""
    print("\n✏️  Edit Issue Details:")
    print("-" * 30)
    
    # Edit title
    print(f"Current title: {template['title']}")
    new_title = input("New title (or press Enter to keep current): ").strip()
    if new_title:
        template['title'] = new_title
    
    # Edit body
    print(f"\nCurrent body preview:")
    print("-" * 40)
    print(template['body'][:200] + "..." if len(template['body']) > 200 else template['body'])
    print("-" * 40)
    
    edit_body = input("Edit body? (y/N): ").strip().lower()
    if edit_body in ['y', 'yes']:
        print("\nEnter the new body (press Ctrl+D when done):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        template['body'] = '\n'.join(lines)
    
    return template

def main() -> None:
    """Main function."""
    print("🚀 Interactive GitHub Issue Creator")
    print("Repository: rasoulbsd/AngryVPN-Telegram-Bot")
    print("=" * 50)
    
    # Select issue type
    issue_type = select_issue_type()
    template = ISSUE_TEMPLATES[issue_type].copy()
    
    # Edit template
    template = edit_template(template)
    
    # Select labels
    labels = select_labels()
    if labels:
        template['labels'].extend(labels)
    
    # Select assignees
    assignees = select_assignees()
    
    # Confirm creation
    print("\n📋 Issue Summary:")
    print("-" * 30)
    print(f"Title: {template['title']}")
    print(f"Labels: {', '.join(template['labels']) if template['labels'] else 'None'}")
    print(f"Assignees: {', '.join(assignees) if assignees else 'None'}")
    print(f"Body length: {len(template['body'])} characters")
    
    confirm = input("\nCreate this issue? (y/N): ").strip().lower()
    if confirm in ['y', 'yes']:
        success = create_issue(
            template['title'],
            template['body'],
            template['labels'],
            assignees
        )
        if success:
            print("🎉 Issue created successfully!")
        else:
            print("❌ Failed to create issue.")
    else:
        print("❌ Issue creation cancelled.")

if __name__ == "__main__":
    main() 