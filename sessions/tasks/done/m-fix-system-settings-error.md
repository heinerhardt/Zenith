---
task: m-fix-system-settings-error
branch: fix/system-settings-error
status: in-progress
created: 2025-01-26
modules: [ui, core, settings]
---

# Fix System Settings Method Call Error

## Problem/Goal
The admin panel functionality is broken due to a method name mismatch in the simple chat app UI. The code calls `get_system_settings()` method which doesn't exist - the actual method is `get_settings()`. This is causing the error message "Unable to load system settings. Please check system configuration." and blocking admin panel functionality.

## Success Criteria
- [ ] Fix method call from `get_system_settings()` to `get_settings()` in src/ui/simple_chat_app.py line 1126
- [ ] Verify admin panel loads system settings without error
- [ ] Test admin panel functionality to ensure it works correctly
- [ ] Confirm error message no longer appears in UI
- [ ] Run basic smoke test of admin features

## Context Files
- @src/ui/simple_chat_app.py:1126        # Line with incorrect method call
- @src/core/enhanced_settings_manager.py # Settings manager with correct get_settings() method
- @src/ui/simple_chat_app.py             # Full file context for admin panel implementation

## User Notes
- This is a straightforward method name correction
- The error is blocking admin panel functionality completely
- Need to verify the method signature and usage pattern matches
- Should test admin panel after fix to ensure no other related issues

## Work Log
- [2025-01-26] Task created, identified method name mismatch in simple_chat_app.py
