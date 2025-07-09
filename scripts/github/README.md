# GitHub Management Tools

This directory contains scripts to help manage GitHub issues, labels, and project organization for the AngryVPN-Telegram-Bot project.

## 🚀 Quick Start

Run the main GitHub manager:
```bash
python scripts/github/github_manager.py
```

## 📁 Scripts Overview

### 1. `github_manager.py` - Main Manager
The main entry point for all GitHub tools. Provides a menu to access all other scripts.

**Features:**
- 🏷️ Manage Labels
- 📝 Create Issues (Interactive)
- 📋 Create Issues (Batch)
- 📊 View Issues
- 🔧 Quick Label Setup
- 📚 View Templates

### 2. `manage_labels.py` - Label Management
Interactive tool to manage GitHub labels.

**Features:**
- 📋 List all existing labels
- 🔧 Add predefined labels (50+ common labels)
- 🎨 Add custom labels with color selection
- 🗑️ Delete labels
- 📊 Label statistics
- 🔄 Refresh labels

### 3. `create_issue_interactive.py` - Interactive Issue Creator
Guides users through creating GitHub issues with templates.

**Features:**
- 📝 Multiple issue templates (Bug, Feature, Improvement, etc.)
- 🏷️ Label selection from existing labels
- 👥 Assignee selection from collaborators
- ✏️ Template editing
- 📋 Issue preview before creation

### 4. `create_github_issues.py` - Batch Issue Creator
Creates multiple issues at once for project setup.

**Features:**
- 📋 Creates 6 predefined issues for remaining tasks
- 🏷️ Automatic label assignment
- 📊 Progress tracking
- 🔄 Error handling

### 5. `github_issues_content.md` - Issue Templates
Markdown file with issue content for manual creation.

## 🏷️ Label Categories

The scripts include predefined labels organized by categories:

### **Type Labels**
- `enhancement` - New features
- `bug` - Bug reports
- `documentation` - Documentation updates
- `task` - General tasks

### **Quality Labels**
- `code-quality` - Code improvements
- `linter` - Linting issues
- `testing` - Testing related
- `quality` - Quality assurance

### **Payment Labels**
- `payment` - Payment features
- `stripe` - Stripe integration
- `crypto` - Cryptocurrency payments

### **Priority Labels**
- `priority: high` - High priority
- `priority: medium` - Medium priority
- `priority: low` - Low priority

### **Status Labels**
- `status: in progress` - Work in progress
- `status: review needed` - Review required
- `status: blocked` - Blocked status
- `status: ready` - Ready for work

### **Team Labels**
- `team: frontend` - Frontend team
- `team: backend` - Backend team
- `team: devops` - DevOps team
- `team: design` - Design team
- `team: qa` - QA team
- `team: product` - Product team

## 📝 Issue Templates

### Bug Report Template
```markdown
## 🐛 Bug Description
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
Add any other context about the problem here.
```

### Feature Request Template
```markdown
## ✨ Feature Description
Brief description of the feature you'd like to see.

## 🎯 Problem Statement
What problem does this feature solve?

## 💡 Proposed Solution
Describe the solution you'd like to see.

## 🔄 Alternative Solutions
Describe any alternative solutions you've considered.

## 📋 Additional Context
Add any other context, screenshots, or examples.
```

## 🛠️ Usage Examples

### Quick Setup
```bash
# Run the main manager
python scripts/github/github_manager.py

# Quick label setup
python scripts/github/github_manager.py
# Select option 5

# Create an interactive issue
python scripts/github/github_manager.py
# Select option 2
```

### Direct Script Usage
```bash
# Manage labels
python scripts/github/manage_labels.py

# Create interactive issue
python scripts/github/create_issue_interactive.py

# Create batch issues
python scripts/github/create_github_issues.py
```

## 🔧 Prerequisites

1. **GitHub CLI**: Must be installed and authenticated
   ```bash
   brew install gh
   gh auth login
   ```

2. **Python**: Python 3.7+ required

3. **Repository Access**: Must have access to `rasoulbsd/AngryVPN-Telegram-Bot`

## 🎨 Color Codes

The scripts use GitHub's standard color codes:
- `0366d6` - Blue (enhancement, backend)
- `28a745` - Green (quality, ready)
- `d73a49` - Red (bug, blocked, high priority)
- `f6a434` - Orange (improvement, medium priority)
- `0075ca` - Light Blue (documentation, frontend)
- `7057ff` - Purple (design, story)
- `6f42c1` - Dark Purple (epic, product)
- `d876e3` - Pink (question)
- `e4e669` - Yellow (invalid)
- `ffffff` - White (wontfix)
- `cfd3d7` - Gray (duplicate)
- `dbed3a` - Light Green (sponsor)

## 🔄 Workflow

### For New Projects
1. Run `github_manager.py`
2. Select "Quick Label Setup" (option 5)
3. Create initial issues using batch creator (option 3)

### For Ongoing Development
1. Use interactive issue creator (option 2) for new issues
2. Use label manager (option 1) to add new labels as needed
3. View issues (option 4) to track progress

### For Team Management
1. Use team-specific labels for assignment
2. Use priority labels for triage
3. Use status labels for workflow tracking

## 🐛 Troubleshooting

### Common Issues

**"gh: command not found"**
- Install GitHub CLI: `brew install gh`
- Authenticate: `gh auth login`

**"Permission denied"**
- Check repository access
- Ensure GitHub CLI is authenticated

**"Label already exists"**
- This is normal, the script will skip existing labels

**"No collaborators found"**
- Repository might be private or you might not have collaborator access
- Issues can still be created without assignees

## 📊 Statistics

The label manager provides statistics including:
- Total label count
- Color distribution
- Labels without descriptions
- Usage patterns

## 🔗 Related Files

- `github_issues_content.md` - Manual issue templates
- `create_github_issues.py` - Batch issue creation
- `manage_labels.py` - Label management
- `create_issue_interactive.py` - Interactive issue creation

## 🤝 Contributing

To add new features to these tools:
1. Follow the existing code style
2. Add proper error handling
3. Update this README
4. Test with your repository

## 📝 License

These tools are part of the AngryVPN-Telegram-Bot project and follow the same license. 