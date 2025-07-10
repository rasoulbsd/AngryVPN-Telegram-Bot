#!/usr/bin/env python3
"""
Create GitHub issues for additional improvements
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
        labels = ["improvement", "enhancement"]
    
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
            "title": "Add E-Transfer Payment Method (Non-Rial)",
            "body": """## Overview
Implement email transfer (e-transfer) payment method for users who cannot use Rial payments.

## Requirements
- E-transfer payment processing
- Email-based payment confirmation
- International payment support
- Payment verification system

## Features
- Email transfer integration
- Payment confirmation emails
- Transaction tracking
- Multi-currency support
- Payment status notifications

## Implementation
- [ ] Research e-transfer APIs
- [ ] Implement payment processing
- [ ] Add email confirmation system
- [ ] Create transaction tracking
- [ ] Add payment verification
- [ ] Test payment flow

## Technical Considerations
- E-transfer API integration
- Email parsing for confirmations
- Payment status monitoring
- Currency conversion handling
- Security measures for payment data

## Acceptance Criteria
- [ ] E-transfer payments work
- [ ] Payment confirmations are sent
- [ ] Transactions are tracked
- [ ] Multi-currency support works
- [ ] Payment verification is secure""",
            "labels": ["payment", "e-transfer", "enhancement"]
        },
        {
            "title": "Implement Alternative Infrastructure for Restricted Users",
            "body": """## Overview
Create alternative infrastructure for users who cannot access Telegram due to restrictions.

## Problem
- Telegram is restricted in many regions
- Users need alternative ways to access VPN services
- Current bot only works through Telegram

## Requirements
- Web-based interface
- Alternative communication channels
- API endpoints for direct access
- Mobile app integration

## Possible Solutions
1. **Web Dashboard**
   - User authentication
   - VPN configuration management
   - Payment processing
   - Usage statistics

2. **Alternative Messaging Platforms**
   - WhatsApp Business API
   - Signal integration
   - Discord bot
   - Email-based system

3. **Mobile App**
   - Native iOS/Android app
   - Direct VPN connection
   - Payment integration
   - User management

4. **API-First Approach**
   - RESTful API endpoints
   - Third-party integrations
   - Webhook support
   - Developer documentation

## Implementation Priority
- [ ] Research alternative platforms
- [ ] Design web dashboard
- [ ] Implement API endpoints
- [ ] Create mobile app
- [ ] Add alternative messaging

## Technical Requirements
- User authentication system
- VPN configuration API
- Payment processing
- Usage tracking
- Security measures

## Acceptance Criteria
- [ ] Users can access service without Telegram
- [ ] Alternative platforms work
- [ ] Security is maintained
- [ ] User experience is good
- [ ] Payment processing works""",
            "labels": ["infrastructure", "accessibility", "enhancement"]
        },
        {
            "title": "Implement Stripe Payment Integration",
            "body": """## Overview
Add Stripe payment gateway integration for international payments.

## Requirements
- Stripe API integration
- International payment support
- Payment webhook handling
- Transaction management

## Features
- Multiple currency support
- Automatic payment processing
- Payment confirmation
- Refund handling

## Implementation
- [ ] Integrate Stripe API
- [ ] Add payment processing
- [ ] Implement webhooks
- [ ] Add transaction tracking
- [ ] Test payment flow

## Acceptance Criteria
- [ ] Stripe payments work
- [ ] Webhooks are handled
- [ ] Transactions are tracked
- [ ] Refunds work properly""",
            "labels": ["payment", "stripe", "enhancement"]
        },
        {
            "title": "Add Comprehensive Error Handling and Logging",
            "body": """## Overview
Implement comprehensive error handling and logging throughout the bot.

## Requirements
- Structured error logging
- Error categorization
- Error reporting system
- Debug information

## Features
- Error tracking
- Performance monitoring
- Debug logging
- Error notifications

## Implementation
- [ ] Implement structured logging
- [ ] Add error categorization
- [ ] Create error reporting
- [ ] Add debug logging
- [ ] Test error handling

## Acceptance Criteria
- [ ] All errors are logged
- [ ] Errors are categorized
- [ ] Debug info is available
- [ ] Error reporting works""",
            "labels": ["logging", "error-handling", "enhancement"]
        },
        {
            "title": "Add Automated Testing Suite",
            "body": """## Overview
Create comprehensive automated testing for all bot functions.

## Requirements
- Unit tests for all functions
- Integration tests
- End-to-end tests
- Performance tests

## Features
- Automated test execution
- Test coverage reporting
- Continuous integration
- Performance benchmarking

## Implementation
- [ ] Create unit tests
- [ ] Add integration tests
- [ ] Implement e2e tests
- [ ] Add performance tests
- [ ] Set up CI/CD

## Acceptance Criteria
- [ ] All functions are tested
- [ ] Tests run automatically
- [ ] Coverage is high
- [ ] Performance is monitored""",
            "labels": ["testing", "ci/cd", "enhancement"]
        },
        {
            "title": "Implement Rate Limiting and Security Measures",
            "body": """## Overview
Add rate limiting and security measures to protect the bot.

## Requirements
- Rate limiting per user
- DDoS protection
- Input validation
- Security headers

## Features
- User rate limiting
- IP-based limiting
- Input sanitization
- Security monitoring

## Implementation
- [ ] Add rate limiting
- [ ] Implement DDoS protection
- [ ] Add input validation
- [ ] Create security monitoring
- [ ] Test security measures

## Acceptance Criteria
- [ ] Rate limiting works
- [ ] DDoS protection is active
- [ ] Input is validated
- [ ] Security is monitored""",
            "labels": ["security", "rate-limiting", "enhancement"]
        },
        {
            "title": "Add Analytics and User Behavior Tracking",
            "body": """## Overview
Implement analytics to track user behavior and bot performance.

## Requirements
- User behavior tracking
- Performance analytics
- Usage statistics
- Conversion tracking

## Features
- User journey tracking
- Performance metrics
- Usage analytics
- Conversion funnels

## Implementation
- [ ] Add analytics tracking
- [ ] Implement user journeys
- [ ] Create performance metrics
- [ ] Add conversion tracking
- [ ] Create analytics dashboard

## Acceptance Criteria
- [ ] User behavior is tracked
- [ ] Performance is measured
- [ ] Analytics are accurate
- [ ] Dashboard is useful""",
            "labels": ["analytics", "tracking", "enhancement"]
        },
        {
            "title": "Add Backup and Recovery System",
            "body": """## Overview
Implement backup and recovery system for bot data and configurations.

## Requirements
- Automated backups
- Data recovery
- Configuration backup
- Disaster recovery

## Features
- Automated backup scheduling
- Data encryption
- Recovery procedures
- Backup verification

## Implementation
- [ ] Set up backup system
- [ ] Add data encryption
- [ ] Create recovery procedures
- [ ] Add backup verification
- [ ] Test recovery process

## Acceptance Criteria
- [ ] Backups are automated
- [ ] Data is encrypted
- [ ] Recovery works
- [ ] Backups are verified""",
            "labels": ["backup", "recovery", "enhancement"]
        },
        {
            "title": "Add Multi-Language Support for All Content",
            "body": """## Overview
Expand multi-language support to cover all bot content and messages.

## Requirements
- Complete content translation
- Dynamic language switching
- Cultural adaptation
- RTL language support

## Features
- Full content translation
- Cultural customization
- RTL text support
- Language detection

## Implementation
- [ ] Translate all content
- [ ] Add cultural adaptation
- [ ] Implement RTL support
- [ ] Add language detection
- [ ] Test all languages

## Acceptance Criteria
- [ ] All content is translated
- [ ] Cultural adaptation works
- [ ] RTL languages work
- [ ] Language detection works""",
            "labels": ["localization", "translation", "enhancement"]
        },
        {
            "title": "Add Advanced Notification System",
            "body": """## Overview
Implement advanced notification system for users and admins.

## Requirements
- Push notifications
- Email notifications
- SMS notifications
- Custom notification rules

## Features
- Multi-channel notifications
- Custom notification rules
- Notification preferences
- Notification history

## Implementation
- [ ] Add push notifications
- [ ] Implement email notifications
- [ ] Add SMS notifications
- [ ] Create notification rules
- [ ] Add notification preferences

## Acceptance Criteria
- [ ] Notifications are sent
- [ ] Rules work properly
- [ ] Preferences are respected
- [ ] History is maintained""",
            "labels": ["notifications", "communication", "enhancement"]
        }
    ]
    
    print("🚀 Creating additional improvement issues...")
    
    created_count = 0
    for issue in issues:
        if create_issue(issue["title"], issue["body"], issue["labels"]):
            created_count += 1
    
    print(f"✅ Created {created_count} new additional improvement issues")


if __name__ == "__main__":
    main() 