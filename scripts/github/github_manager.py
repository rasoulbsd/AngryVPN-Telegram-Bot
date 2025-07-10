#!/usr/bin/env python3
"""
GitHub Management Tool
Main script to access all GitHub-related tools.
"""

import sys
import subprocess
from pathlib import Path

def run_script(script_name: str) -> None:
    """Run a script in the current directory."""
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_name}")
        return
    
    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
    except KeyboardInterrupt:
        print(f"\n⏹️  {script_name} interrupted by user")

def show_menu() -> None:
    """Show the main menu."""
    print("\n" + "=" * 60)
    print("🚀 GitHub Management Tools")
    print("Repository: rasoulbsd/AngryVPN-Telegram-Bot")
    print("=" * 60)
    print("1. 🏷️  Manage Labels")
    print("2. 📝 Create Issue (Interactive)")
    print("3. 📋 Create Issues (Batch)")
    print("4. 📊 View Issues")
    print("5. 🔧 Quick Label Setup")
    print("6. 📚 View Issue Templates")
    print("0. ❌ Exit")
    print("-" * 60)

def quick_label_setup() -> None:
    """Quick setup for common labels."""
    print("\n🔧 Quick Label Setup")
    print("=" * 30)
    
    # Common labels for this project
    common_labels = [
        ("enhancement", "0366d6", "New feature or request"),
        ("bug", "d73a49", "Something isn't working"),
        ("documentation", "0075ca", "Documentation updates"),
        ("code-quality", "28a745", "Code quality improvements"),
        ("linter", "d73a49", "Linting and code style issues"),
        ("payment", "6f42c1", "Payment-related features"),
        ("stripe", "0366d6", "Stripe payment integration"),
        ("crypto", "f6a434", "Cryptocurrency payment features"),
        ("testing", "0075ca", "Testing and quality assurance"),
        ("quality", "28a745", "Code quality and reliability"),
        ("maintenance", "d73a49", "Maintenance and upkeep tasks"),
        ("performance", "f6a434", "Performance improvements"),
        ("monitoring", "0366d6", "Monitoring and observability"),
        ("security", "d73a49", "Security-related issues"),
        ("api", "0366d6", "API-related changes"),
        ("database", "0075ca", "Database-related changes"),
        ("deployment", "f6a434", "Deployment and infrastructure"),
        ("priority: high", "d73a49", "High priority"),
        ("priority: medium", "f6a434", "Medium priority"),
        ("priority: low", "28a745", "Low priority"),
        ("status: in progress", "0366d6", "Work in progress"),
        ("status: review needed", "f6a434", "Review required"),
        ("status: blocked", "d73a49", "Blocked status"),
        ("status: ready", "28a745", "Ready for work")
    ]
    
    print("This will create common labels for the project.")
    confirm = input("Continue? (y/N): ").strip().lower()
    
    if confirm not in ['y', 'yes']:
        print("❌ Setup cancelled.")
        return
    
    success_count = 0
    for name, color, description in common_labels:
        try:
            cmd = [
                "gh", "label", "create", name,
                "--color", color,
                "--description", description
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ Created: {name}")
            success_count += 1
        except subprocess.CalledProcessError as e:
            if "already exists" in e.stderr:
                print(f"ℹ️  Already exists: {name}")
                success_count += 1
            else:
                print(f"❌ Failed: {name} - {e.stderr}")
    
    print(f"\n✅ Setup complete! {success_count}/{len(common_labels)} labels ready.")

def view_issues() -> None:
    """View current issues."""
    print("\n📊 Current Issues")
    print("=" * 30)
    
    try:
        # Get issues
        result = subprocess.run(
            ["gh", "issue", "list", "--limit", "10"],
            capture_output=True, text=True, check=True
        )
        
        if result.stdout.strip():
            print(result.stdout)
        else:
            print("No issues found.")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching issues: {e.stderr}")

def view_templates() -> None:
    """View available issue templates."""
    print("\n📚 Available Issue Templates")
    print("=" * 40)
    
    templates = {
        "bug": "🐛 Bug Report - Report a bug or issue",
        "feature": "✨ Feature Request - Request a new feature",
        "improvement": "🔧 Improvement Request - Suggest improvements",
        "documentation": "📚 Documentation Update - Update documentation",
        "task": "📋 Task - General task or work item",
        "custom": "📝 Custom Issue - Create a custom issue"
    }
    
    for template_id, description in templates.items():
        print(f"• {description}")
    
    print("\n💡 Use the interactive issue creator to use these templates!")

def main() -> None:
    """Main function."""
    print("🚀 Welcome to GitHub Management Tools!")
    print("Managing: rasoulbsd/AngryVPN-Telegram-Bot")
    
    while True:
        show_menu()
        choice = input("\nSelect option (0-6): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            run_script("manage_labels.py")
        elif choice == "2":
            run_script("create_issue_interactive.py")
        elif choice == "3":
            run_script("create_github_issues.py")
        elif choice == "4":
            view_issues()
        elif choice == "5":
            quick_label_setup()
        elif choice == "6":
            view_templates()
        else:
            print("❌ Invalid option. Please try again.")
        
        if choice != "0":
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 