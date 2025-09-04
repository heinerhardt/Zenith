---
task: m-fix-ai-provider-exclusivity
branch: fix/ai-provider-exclusivity
status: completed
created: 2025-01-09
started: 2025-01-09
completed: 2025-01-09
modules: [ui]
---

# Fix AI Provider Configuration Mutual Exclusivity

## Problem/Goal
In the System Settings page (@src/ui/simple_chat_app.py), the AI Provider Configuration section currently allows both OpenAI Settings and Ollama Settings to be checked simultaneously. This creates confusion and potential configuration conflicts.

The current implementation has no mutual exclusivity logic. Both checkboxes can be checked simultaneously, leading to:
- Configuration conflicts where both providers appear active
- User confusion about which provider is actually being used
- Potential runtime issues if both providers are configured but system expects only one primary provider
- Inconsistency between the "AI Provider Configuration" section and "Active Providers" section

Need to implement mutual exclusivity:
- When OpenAI Settings checkbox is selected, Ollama Settings should automatically uncheck
- When Ollama Settings checkbox is selected, OpenAI Settings should automatically uncheck
- Only one AI provider should be allowed to remain checked at any time
- The Active Providers section (Chat Provider and Embedding Provider dropdowns) should automatically update based on which AI Provider Configuration is chosen

## Success Criteria
- [ ] OpenAI Settings and Ollama Settings checkboxes are mutually exclusive
- [ ] When one provider is selected, the other is automatically deselected
- [ ] Active Providers (Chat Provider and Embedding Provider) automatically update to match the selected AI provider
- [ ] Dropdown options filtered to show only the enabled provider
- [ ] Active Providers default to .env file configuration (CHAT_PROVIDER and EMBEDDING_PROVIDER)
- [ ] UI behavior is smooth and intuitive for users
- [ ] Settings save correctly with only one provider enabled
- [ ] No configuration conflicts between providers
- [ ] Data persistence maintains consistency (when one provider enabled, other's settings cleared)

## Context Files
- @src/ui/simple_chat_app.py:1117-1320  # System Settings page and AI Provider Configuration section
- @src/auth/models.py:261-391  # SystemSettings class data model
- @src/core/enhanced_settings_manager.py  # Settings persistence layer
- @src/core/config.py  # Configuration management

## Context Manifest

### How This Currently Works: System Settings AI Provider Configuration

The system settings page in `src/ui/simple_chat_app.py` (lines 1117-1320) currently implements a configuration interface where users can independently enable both OpenAI and Ollama providers simultaneously. When a user accesses the System Settings page through the `render_system_settings_page()` function, the system loads current settings from the `EnhancedSettingsManager` and displays them in a two-column layout.

**Current Flow:**
1. **Settings Loading**: The function calls `get_enhanced_settings_manager().get_settings()` which retrieves a `SystemSettings` object from the Qdrant database
2. **OpenAI Configuration (Column 1)**: An independent checkbox `openai_enabled` is determined by `bool(current_settings.openai_api_key)` - if there's an API key, it shows as enabled
3. **Ollama Configuration (Column 2)**: A separate independent checkbox `ollama_enabled` uses `current_settings.ollama_enabled` boolean flag
4. **Active Providers Section**: Two dropdowns allow selection of chat and embedding providers with hardcoded options `["openai", "ollama"]`
5. **Save Logic**: When settings are saved (lines 1276-1307), both provider configurations are preserved independently in the `updates` dictionary

**Data Model Context**: The `SystemSettings` class stores:
- `openai_api_key: Optional[str]` - OpenAI API key (None means disabled)
- `ollama_enabled: bool` - Explicit boolean for Ollama enablement
- `preferred_chat_provider: str` - Currently independent of the checkbox states
- `preferred_embedding_provider: str` - Currently independent of the checkbox states

The asymmetry in how OpenAI (key-based) vs Ollama (boolean-based) enablement is determined creates additional complexity.

### For New Feature Implementation: Mutual Exclusivity Logic

**UI State Management**: The current Streamlit implementation uses independent checkbox states. We'll need to implement callback logic where checking one provider automatically unchecks the other. Streamlit's reactive behavior means we'll need to use session state or implement a callback pattern to manage this interdependency.

**Settings Synchronization**: The "Active Providers" dropdowns (lines 1191-1204) currently operate independently from the checkbox states. When a user selects a provider in the configuration section, these dropdowns should automatically update to match. Additionally, the dropdown options should be filtered to only show the enabled provider.

**Data Persistence Logic**: The save operation (lines 1276-1307) needs enhancement to ensure consistency. When one provider is enabled, the system should:
- Clear/disable the other provider's settings
- Update both `preferred_chat_provider` and `preferred_embedding_provider` to match the enabled provider
- Maintain data integrity by ensuring only one provider is truly active

### Implementation Strategy

**Streamlit Session State Approach:**
- Use `st.session_state` to track previous checkbox states
- Implement logic to detect state changes and enforce mutual exclusivity
- Update dropdown options dynamically based on enabled provider

**Settings Update Logic:**
- Modify the save operation to enforce consistency
- When OpenAI is enabled: set `ollama_enabled=False`, clear Ollama settings
- When Ollama is enabled: set `openai_api_key=None`, update provider preferences

## User Notes
- Focus on the render_system_settings_page() function
- The mutual exclusivity logic should be implemented in the Streamlit UI components
- Both the checkbox states and the dropdown selections need to be synchronized
- Ensure the settings are properly saved with the correct provider selection
- Maintain backward compatibility while ensuring clear user experience
- Pay attention to Streamlit's reactive behavior and existing settings persistence architecture
- Active Providers should default to .env file values: CHAT_PROVIDER=openai, EMBEDDING_PROVIDER=openai

## Work Log
- [2025-01-09] Created task for implementing AI provider mutual exclusivity with comprehensive context manifest
- [2025-01-09] Started task implementation - created branch, set up todos, examining current code
- [2025-01-09] Implemented full mutual exclusivity logic with session state management, .env defaults, and provider synchronization
- [2025-01-09] Implementation completed successfully - all success criteria met, syntax verified, ready for testing
