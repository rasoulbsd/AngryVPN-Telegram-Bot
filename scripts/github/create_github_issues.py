#!/usr/bin/env python3
"""
Script to create GitHub issues for remaining tasks in the AngryVPN-Telegram-Bot project.
"""

import subprocess
import sys

# Define the issues to create
ISSUES = [
    {
        "title": "🔧 Fix remaining linter errors",
        "body": """## Description
There are approximately 38 remaining linter errors that need to be addressed.

## Current Issues
- Unused variables in `helpers/bot_functions.py`
- Unused variables in `helpers/client/crypto.py` 
- Unused variables in `helpers/org_admin/charging.py`
- Bare except statements in `helpers/org_admin/announcements.py`
- Comparison to None issues in `helpers/org_admin/charging.py`

## Tasks
- [ ] Remove unused variable assignments
- [ ] Replace bare `except:` with specific exception handling
- [ ] Fix `== None` comparisons to use `is None`
- [ ] Run `python -m ruff check --fix .` to auto-fix what's possible
- [ ] Manually fix remaining issues

## Priority
Medium - Code quality improvement

## Labels
- `enhancement`
- `code-quality`
- `linter`""",
        "labels": ["enhancement", "code-quality", "linter"]
    },
    {
        "title": "💳 Implement Stripe payment integration",
        "body": """## Description
Add Stripe payment integration to the purchase module.

## Current Status
- Placeholder functions created in `helpers/client/purchase/stripe.py`
- Basic structure ready for implementation

## Tasks
- [ ] Install Stripe Python SDK: `pip install stripe`
- [ ] Add Stripe configuration to secrets/config
- [ ] Implement `newuser_purchase_stripe()` function
- [ ] Implement webhook handler for payment confirmation
- [ ] Add Stripe payment option to plan selection
- [ ] Test payment flow end-to-end
- [ ] Add error handling and logging
- [ ] Update documentation

## Files to Modify
- `helpers/client/purchase/stripe.py`
- `helpers/initial.py` (add Stripe config)
- `bot.py` (add Stripe handlers)
- `req.txt` (add stripe dependency)

## Priority
High - New payment method

## Labels
- `enhancement`
- `payment`
- `stripe`""",
        "labels": ["enhancement", "payment", "stripe"]
    },
    {
        "title": "₿ Add Bitcoin and Ethereum crypto payments",
        "body": """## Description
Implement Bitcoin and Ethereum payment methods in the crypto module.

## Current Status
- Stub functions exist in `helpers/client/purchase/crypto.py`
- Basic crypto payment structure already implemented

## Tasks
- [ ] Research best crypto payment APIs (Coinbase, BitPay, etc.)
- [ ] Implement `newuser_purchase_receipt_bitcoin()` function
- [ ] Implement `newuser_purchase_receipt_ethereum()` function
- [ ] Add crypto wallet configuration
- [ ] Implement transaction verification
- [ ] Add crypto payment options to plan selection
- [ ] Test with testnet first
- [ ] Add error handling for network issues

## Files to Modify
- `helpers/client/purchase/crypto.py`
- `helpers/initial.py` (add crypto config)
- `bot.py` (add crypto handlers)

## Priority
Medium - Additional payment method

## Labels
- `enhancement`
- `payment`
- `crypto`""",
        "labels": ["enhancement", "payment", "crypto"]
    },
    {
        "title": "🧪 Create comprehensive test suite",
        "body": """## Description
Create a comprehensive test suite for the modularized codebase.

## Current Status
- No automated tests exist
- Manual testing only

## Tasks
- [ ] Set up pytest framework
- [ ] Create unit tests for payment modules
- [ ] Create unit tests for org admin modules
- [ ] Create integration tests for bot flows
- [ ] Add test coverage reporting
- [ ] Create mock data for testing
- [ ] Add CI/CD pipeline for automated testing
- [ ] Document testing procedures

## Test Structure
```
tests/
├── unit/
│   ├── test_purchase_rial.py
│   ├── test_purchase_crypto.py
│   ├── test_purchase_stripe.py
│   └── test_org_admin.py
├── integration/
│   ├── test_purchase_flow.py
│   └── test_admin_flow.py
└── fixtures/
    └── test_data.py
```

## Priority
High - Code reliability

## Labels
- `enhancement`
- `testing`
- `quality`""",
        "labels": ["enhancement", "testing", "quality"]
    },
    {
        "title": "📚 Update documentation and scripts",
        "body": """## Description
Update all documentation, scripts, and configuration files to reflect the new modular structure.

## Tasks
- [ ] Update README.md with new module structure
- [ ] Update Docker configuration
- [ ] Update localization files if needed
- [ ] Update deployment scripts
- [ ] Create module documentation
- [ ] Update API documentation
- [ ] Create developer setup guide
- [ ] Update changelog

## Files to Update
- `README.md`
- `Dockerfile`
- `docker-compose.yml`
- `localization.sh`
- `scripts/` directory
- `docs/` directory

## Priority
Medium - Documentation

## Labels
- `documentation`
- `maintenance`""",
        "labels": ["documentation", "maintenance"]
    },
    {
        "title": "🚀 Performance optimization and monitoring",
        "body": """## Description
Optimize performance and add monitoring capabilities to the bot.

## Tasks
- [ ] Add request/response logging
- [ ] Implement performance metrics
- [ ] Add error tracking and alerting
- [ ] Optimize database queries
- [ ] Add caching for frequently accessed data
- [ ] Implement rate limiting
- [ ] Add health check endpoints
- [ ] Monitor memory usage and optimize

## Priority
Low - Performance improvement

## Labels
- `enhancement`
- `performance`
- `monitoring`""",
        "labels": ["enhancement", "performance", "monitoring"]
    }
]

def create_issue(title, body, labels):
    """Create a GitHub issue using gh CLI."""
    try:
        # Create the issue
        cmd = [
            "gh", "issue", "create",
            "--title", title,
            "--body", body,
            "--label", ",".join(labels)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Created issue: {title}")
            return True
        else:
            print(f"❌ Failed to create issue: {title}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating issue '{title}': {e}")
        return False

def main():
    """Main function to create all issues."""
    print("🚀 Creating GitHub issues for remaining tasks...")
    print("=" * 50)
    
    success_count = 0
    total_count = len(ISSUES)
    
    for issue in ISSUES:
        if create_issue(issue["title"], issue["body"], issue["labels"]):
            success_count += 1
        print()
    
    print("=" * 50)
    print(f"📊 Summary: {success_count}/{total_count} issues created successfully")
    
    if success_count < total_count:
        print("\n💡 Manual creation instructions:")
        print("1. Go to: https://github.com/rasoulbsd/AngryVPN-Telegram-Bot/issues")
        print("2. Click 'New issue'")
        print("3. Copy and paste the issue content from the script above")
    
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main()) 