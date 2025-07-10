#!/usr/bin/env python3
"""
Create GitHub issues for infrastructure tasks
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
        labels = ["infrastructure", "enhancement"]
    
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
            "title": "Add Development Mode Toggle for Bot Status",
            "body": """## Overview
Add ability to quickly change bot status during development/testing phases.

## Requirements
- Fast toggle between development and production modes
- Different bot status/behavior in dev mode
- Easy configuration switch
- Logging for mode changes

## Implementation Ideas
- Environment variable or config file toggle
- Different bot responses in dev mode
- Development-specific features (debug info, test data)
- Status indicator in bot responses

## Acceptance Criteria
- [ ] Bot can switch between dev/prod modes quickly
- [ ] Dev mode has clear indicators
- [ ] No impact on production functionality
- [ ] Easy configuration management""",
            "labels": ["infrastructure", "enhancement", "development"]
        },
        {
            "title": "Add VLESS/SS Protocol Support with User Choice",
            "body": """## Overview
Implement support for VLESS and Shadowsocks protocols with user-selectable options.

## Requirements
- Support for VLESS protocol
- Support for Shadowsocks protocol
- User choice per server or profile
- Protocol selection in user interface

## Technical Details
- Xray-core compatibility
- Protocol configuration in user profiles
- Server-side protocol support
- Connection testing for each protocol

## Implementation
- [ ] Add VLESS protocol support
- [ ] Add Shadowsocks protocol support
- [ ] User interface for protocol selection
- [ ] Server configuration for multiple protocols
- [ ] Connection testing functionality
- [ ] Profile-based protocol preferences

## Acceptance Criteria
- [ ] Users can select protocol per server
- [ ] Users can set default protocol in profile
- [ ] All protocols work correctly
- [ ] Connection testing works for all protocols""",
            "labels": ["infrastructure", "enhancement", "protocols"]
        },
        {
            "title": "Implement Automated Support Messages",
            "body": """## Overview
Create automated message system for common support scenarios.

## Requirements
- Pre-defined responses for common issues
- Automated ticket categorization
- Quick response templates
- Support workflow automation

## Features
- Common FAQ responses
- Automated ticket routing
- Support message templates
- Escalation procedures

## Implementation
- [ ] Define common support scenarios
- [ ] Create response templates
- [ ] Implement automated routing
- [ ] Add escalation logic
- [ ] Support message management

## Acceptance Criteria
- [ ] Automated responses for common issues
- [ ] Proper ticket categorization
- [ ] Human escalation when needed
- [ ] Configurable message templates""",
            "labels": ["infrastructure", "support", "automation"]
        },
        {
            "title": "Improve Panel Error Handling and User Experience",
            "body": """## Overview
Fix current implementation that blocks on unreachable panels and improve error handling.

## Current Issues
- Bot blocks when panels are unreachable
- Users see technical errors instead of user-friendly messages
- No graceful degradation when panels are down
- Poor user experience during panel outages

## Requirements
- Graceful handling of panel unavailability
- User-friendly error messages
- Non-blocking operations
- Fallback mechanisms

## Implementation
- [ ] Implement panel health checks
- [ ] Add timeout mechanisms
- [ ] Create user-friendly error messages
- [ ] Implement fallback options
- [ ] Add retry logic with backoff

## Acceptance Criteria
- [ ] Bot doesn't block on panel issues
- [ ] Users see helpful error messages
- [ ] Operations continue when possible
- [ ] Clear communication about issues""",
            "labels": ["infrastructure", "bug", "user-experience"]
        },
        {
            "title": "Integrate Xray (v2fly) Core Panel",
            "body": """## Overview
Add support for Xray-core panel integration.

## Requirements
- Xray-core panel API integration
- User management through Xray
- Configuration generation
- Statistics and monitoring

## Technical Details
- Xray API integration
- User account management
- Traffic statistics
- Configuration file generation
- Panel communication

## Implementation
- [ ] Research Xray panel APIs
- [ ] Implement user management
- [ ] Add configuration generation
- [ ] Integrate statistics
- [ ] Test panel communication

## Acceptance Criteria
- [ ] Full Xray panel integration
- [ ] User management works
- [ ] Statistics are accurate
- [ ] Configurations are valid""",
            "labels": ["infrastructure", "enhancement", "xray"]
        },
        {
            "title": "Create Test Connection System",
            "body": """## Overview
Implement system for testing VPN connections and configurations.

## Requirements
- Test connection functionality
- Configuration validation
- Speed and latency testing
- Connection health monitoring

## Features
- Connection testing before activation
- Speed test integration
- Latency measurement
- Configuration validation
- Health check endpoints

## Implementation
- [ ] Design test connection API
- [ ] Implement speed testing
- [ ] Add latency measurement
- [ ] Create health check system
- [ ] Add configuration validation

## Acceptance Criteria
- [ ] Connections can be tested
- [ ] Speed tests work accurately
- [ ] Latency is measured
- [ ] Configurations are validated""",
            "labels": ["infrastructure", "testing", "monitoring"]
        }
    ]
    
    print("🚀 Creating infrastructure issues...")
    
    created_count = 0
    for issue in issues:
        if create_issue(issue["title"], issue["body"], issue["labels"]):
            created_count += 1
    
    print(f"✅ Created {created_count} new infrastructure issues")


if __name__ == "__main__":
    main() 