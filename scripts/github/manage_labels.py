#!/usr/bin/env python3
"""
GitHub Labels Management Script
Allows users to add, remove, and list GitHub labels interactively.
"""

import subprocess
import sys
import json
from typing import List, Dict, Optional

# Predefined label configurations
PREDEFINED_LABELS = {
    "enhancement": {"color": "0366d6", "description": "New feature or request"},
    "bug": {"color": "d73a49", "description": "Something isn't working"},
    "documentation": {"color": "0075ca", "description": "Documentation updates"},
    "good first issue": {"color": "7057ff", "description": "Good for newcomers"},
    "help wanted": {"color": "008672", "description": "Extra attention is needed"},
    "code-quality": {"color": "28a745", "description": "Code quality improvements"},
    "linter": {"color": "d73a49", "description": "Linting and code style issues"},
    "payment": {"color": "6f42c1", "description": "Payment-related features"},
    "stripe": {"color": "0366d6", "description": "Stripe payment integration"},
    "crypto": {"color": "f6a434", "description": "Cryptocurrency payment features"},
    "testing": {"color": "0075ca", "description": "Testing and quality assurance"},
    "quality": {"color": "28a745", "description": "Code quality and reliability"},
    "maintenance": {"color": "d73a49", "description": "Maintenance and upkeep tasks"},
    "performance": {"color": "f6a434", "description": "Performance improvements"},
    "monitoring": {"color": "0366d6", "description": "Monitoring and observability"},
    "security": {"color": "d73a49", "description": "Security-related issues"},
    "api": {"color": "0366d6", "description": "API-related changes"},
    "database": {"color": "0075ca", "description": "Database-related changes"},
    "deployment": {"color": "f6a434", "description": "Deployment and infrastructure"},
    "mobile": {"color": "7057ff", "description": "Mobile app related"},
    "web": {"color": "0075ca", "description": "Web interface related"},
    "backend": {"color": "0366d6", "description": "Backend changes"},
    "frontend": {"color": "0075ca", "description": "Frontend changes"},
    "ui/ux": {"color": "7057ff", "description": "User interface/experience"},
    "accessibility": {"color": "28a745", "description": "Accessibility improvements"},
    "internationalization": {"color": "0075ca", "description": "i18n and l10n"},
    "blocked": {"color": "d73a49", "description": "Blocked by other issues"},
    "duplicate": {"color": "cfd3d7", "description": "Duplicate issue"},
    "invalid": {"color": "e4e669", "description": "Invalid issue"},
    "wontfix": {"color": "ffffff", "description": "Won't be fixed"},
    "question": {"color": "d876e3", "description": "Further information is requested"},
    "discussion": {"color": "0075ca", "description": "Discussion needed"},
    "research": {"color": "f6a434", "description": "Research and investigation"},
    "design": {"color": "7057ff", "description": "Design work needed"},
    "content": {"color": "0075ca", "description": "Content updates"},
    "legal": {"color": "d73a49", "description": "Legal and compliance"},
    "sponsor": {"color": "dbed3a", "description": "Sponsored work"},
    "priority: high": {"color": "d73a49", "description": "High priority"},
    "priority: medium": {"color": "f6a434", "description": "Medium priority"},
    "priority: low": {"color": "28a745", "description": "Low priority"},
    "status: in progress": {"color": "0366d6", "description": "Work in progress"},
    "status: review needed": {"color": "f6a434", "description": "Review required"},
    "status: blocked": {"color": "d73a49", "description": "Blocked status"},
    "status: ready": {"color": "28a745", "description": "Ready for work"},
    "type: feature": {"color": "0366d6", "description": "New feature"},
    "type: bug": {"color": "d73a49", "description": "Bug report"},
    "type: improvement": {"color": "28a745", "description": "Improvement"},
    "type: task": {"color": "0075ca", "description": "Task"},
    "type: story": {"color": "7057ff", "description": "User story"},
    "type: epic": {"color": "6f42c1", "description": "Epic"},
    "sprint: current": {"color": "0366d6", "description": "Current sprint"},
    "sprint: next": {"color": "28a745", "description": "Next sprint"},
    "sprint: backlog": {"color": "f6a434", "description": "Backlog"},
    "team: frontend": {"color": "0075ca", "description": "Frontend team"},
    "team: backend": {"color": "0366d6", "description": "Backend team"},
    "team: devops": {"color": "f6a434", "description": "DevOps team"},
    "team: design": {"color": "7057ff", "description": "Design team"},
    "team: qa": {"color": "28a745", "description": "QA team"},
    "team: product": {"color": "6f42c1", "description": "Product team"}
}

def run_command(cmd: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        return subprocess.run(cmd, capture_output=capture_output, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return e

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

def create_label(name: str, color: str, description: str) -> bool:
    """Create a GitHub label."""
    try:
        cmd = [
            "gh", "label", "create", name,
            "--color", color,
            "--description", description
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Created label: {name}")
        return True
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr:
            print(f"ℹ️  Label '{name}' already exists")
            return True
        else:
            print(f"❌ Failed to create label '{name}': {e.stderr}")
            return False

def delete_label(name: str) -> bool:
    """Delete a GitHub label."""
    try:
        cmd = ["gh", "label", "delete", name, "--yes"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Deleted label: {name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to delete label '{name}': {e.stderr}")
        return False

def list_labels() -> None:
    """List all existing labels."""
    labels = get_existing_labels()
    if not labels:
        print("No labels found.")
        return
    
    print("\n📋 Existing Labels:")
    print("-" * 50)
    for label in labels:
        color_emoji = "🟢" if label.get("color") == "28a745" else "🔵"
        print(f"{color_emoji} {label['name']} - {label.get('description', 'No description')}")

def add_predefined_labels() -> None:
    """Add predefined labels."""
    existing_labels = {label["name"] for label in get_existing_labels()}
    
    print("\n🔧 Adding predefined labels...")
    success_count = 0
    
    for name, config in PREDEFINED_LABELS.items():
        if name not in existing_labels:
            if create_label(name, config["color"], config["description"]):
                success_count += 1
    
    print(f"\n✅ Added {success_count} new labels")

def add_custom_label() -> None:
    """Add a custom label with user input."""
    print("\n🎨 Add Custom Label")
    print("-" * 30)
    
    name = input("Label name: ").strip()
    if not name:
        print("❌ Label name cannot be empty")
        return
    
    description = input("Description (optional): ").strip()
    
    # Color selection
    print("\n🎨 Available colors:")
    colors = {
        "1": ("0366d6", "Blue"),
        "2": ("28a745", "Green"),
        "3": ("d73a49", "Red"),
        "4": ("f6a434", "Orange"),
        "5": ("0075ca", "Light Blue"),
        "6": ("7057ff", "Purple"),
        "7": ("6f42c1", "Dark Purple"),
        "8": ("d876e3", "Pink"),
        "9": ("e4e669", "Yellow"),
        "10": ("ffffff", "White"),
        "11": ("cfd3d7", "Gray"),
        "12": ("dbed3a", "Light Green")
    }
    
    for key, (color, color_name) in colors.items():
        print(f"  {key}. {color_name} ({color})")
    
    choice = input("\nSelect color (1-12): ").strip()
    color = colors.get(choice, ("0366d6", "Blue"))[0]
    
    if create_label(name, color, description):
        print(f"✅ Custom label '{name}' created successfully!")

def delete_custom_label() -> None:
    """Delete a label with user selection."""
    labels = get_existing_labels()
    if not labels:
        print("No labels to delete.")
        return
    
    print("\n🗑️  Delete Label")
    print("-" * 20)
    
    for i, label in enumerate(labels, 1):
        print(f"{i}. {label['name']} - {label.get('description', 'No description')}")
    
    try:
        choice = int(input("\nSelect label to delete (number): "))
        if 1 <= choice <= len(labels):
            label_name = labels[choice - 1]["name"]
            confirm = input(f"Are you sure you want to delete '{label_name}'? (y/N): ")
            if confirm.lower() in ['y', 'yes']:
                delete_label(label_name)
            else:
                print("❌ Deletion cancelled")
        else:
            print("❌ Invalid selection")
    except ValueError:
        print("❌ Please enter a valid number")

def show_menu() -> None:
    """Show the main menu."""
    print("\n" + "=" * 50)
    print("🏷️  GitHub Labels Manager")
    print("=" * 50)
    print("1. 📋 List all labels")
    print("2. 🔧 Add predefined labels")
    print("3. 🎨 Add custom label")
    print("4. 🗑️  Delete label")
    print("5. 📊 Label statistics")
    print("6. 🔄 Refresh labels")
    print("0. ❌ Exit")
    print("-" * 50)

def show_statistics() -> None:
    """Show label statistics."""
    labels = get_existing_labels()
    if not labels:
        print("No labels found.")
        return
    
    print("\n📊 Label Statistics")
    print("-" * 30)
    print(f"Total labels: {len(labels)}")
    
    # Count by color
    color_counts = {}
    for label in labels:
        color = label.get("color", "unknown")
        color_counts[color] = color_counts.get(color, 0) + 1
    
    print("\nColors used:")
    for color, count in sorted(color_counts.items()):
        print(f"  {color}: {count} labels")
    
    # Show labels without descriptions
    no_desc = [label for label in labels if not label.get("description")]
    if no_desc:
        print(f"\nLabels without descriptions: {len(no_desc)}")
        for label in no_desc:
            print(f"  - {label['name']}")

def main() -> None:
    """Main function."""
    print("🚀 GitHub Labels Manager")
    print("Managing labels for: rasoulbsd/AngryVPN-Telegram-Bot")
    
    while True:
        show_menu()
        choice = input("\nSelect option (0-6): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            list_labels()
        elif choice == "2":
            add_predefined_labels()
        elif choice == "3":
            add_custom_label()
        elif choice == "4":
            delete_custom_label()
        elif choice == "5":
            show_statistics()
        elif choice == "6":
            print("🔄 Refreshing labels...")
            list_labels()
        else:
            print("❌ Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 