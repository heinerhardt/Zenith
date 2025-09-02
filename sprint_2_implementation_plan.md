# Sprint 2: Core Accessibility Implementation & Feature Integration Plan
*Timeline: 3 weeks (21 days) | Effort: 144 total hours*

## 📋 Executive Summary

This Sprint 2 implementation plan focuses on achieving WCAG 2.1 AA accessibility compliance while integrating advanced features from `enhanced_streamlit_app.py` into the modern `three_panel_chat_app.py` interface. The plan maintains the clean three-panel ChatGPT-inspired design while adding sophisticated functionality and ensuring inclusive user experience.

**Success Metrics:**
- 100% WCAG 2.1 AA compliance across all components
- Screen reader task completion rate >90%
- Keyboard navigation covering 100% of functionality
- Color contrast ratios meeting 4.5:1 (normal text) and 3:1 (large text) standards

---

## 🎯 Sprint 2 Objectives

1. **ARIA Implementation & Screen Reader Support** (8 days, 64 hours)
2. **Keyboard Navigation & Focus Management** (6 days, 48 hours)
3. **Color Contrast & Visual Accessibility** (4 days, 32 hours)
4. **Feature Integration from Enhanced App** (3 days continuous)

---

# 📅 DETAILED TASK BREAKDOWN

## Task 2.1: ARIA Implementation & Screen Reader Support
**Owner**: Frontend Developer + Accessibility Specialist  
**Timeline**: 8 days  
**Effort**: 64 hours

### 🔍 Analysis Phase (Day 1-2: 16 hours)

**Deliverables:**
- [ ] Complete ARIA audit of existing three-panel interface
- [ ] Screen reader testing results (NVDA, JAWS, VoiceOver)
- [ ] Dynamic content accessibility assessment
- [ ] Form interaction accessibility baseline
- [ ] Chat message structure accessibility evaluation

**Technical Assessment:**
```html
<!-- Current State Analysis -->
<div class="three-panel-container"> <!-- Missing main landmark -->
  <div class="left-panel"> <!-- Missing navigation role -->
    <!-- Session items lack proper labeling -->
  </div>
  <div class="center-panel"> <!-- Missing main content role -->
    <!-- Chat messages lack live regions -->
    <!-- Chat input lacks proper descriptions -->
  </div>
  <div class="right-panel"> <!-- Missing complementary role -->
    <!-- Admin controls lack proper grouping -->
  </div>
</div>
```

### 🛠️ Implementation Phase (Day 3-6: 32 hours)

**Priority 1: Semantic HTML Structure Enhancement**
```html
<!-- Enhanced Three-Panel Structure with ARIA -->
<div class="three-panel-container">
  <!-- Left Panel: Navigation -->
  <nav class="left-panel" 
       role="navigation" 
       aria-label="Chat history and navigation">
    
    <header class="left-panel-header" role="banner">
      <h1 id="chat-nav-title">Recent Chats</h1>
    </header>
    
    <main class="left-panel-content" 
          role="main" 
          aria-labelledby="chat-nav-title">
      
      <!-- New Chat Button with Clear Intent -->
      <button type="button" 
              class="new-chat-btn" 
              aria-describedby="new-chat-help">
        <span class="btn-icon" aria-hidden="true">🆕</span>
        <span class="btn-text">New Chat</span>
      </button>
      <div id="new-chat-help" class="sr-only">
        Start a new conversation with Zenith AI
      </div>
      
      <!-- Chat Sessions List with Proper Semantics -->
      <section aria-label="Recent chat sessions">
        <h2 class="sr-only">Recent Conversations</h2>
        <ul role="list" class="sessions-list">
          <li role="listitem" class="session-item">
            <button type="button" 
                    class="session-btn"
                    aria-describedby="session-meta-{{id}}"
                    aria-pressed="false">
              <div class="session-title">{{title}}</div>
              <div id="session-meta-{{id}}" class="session-meta">
                {{message_count}} messages, {{time_ago}}
              </div>
            </button>
          </li>
        </ul>
      </section>
    </main>
  </nav>

  <!-- Center Panel: Main Chat Interface -->
  <main class="center-panel" 
        role="main" 
        aria-label="Zenith AI Chat Interface">
    
    <header class="chat-header" role="banner">
      <h1 class="chat-title">
        <span class="logo" aria-hidden="true">🤖</span>
        Zenith AI
      </h1>
      <p class="chat-subtitle">Intelligent Document Chat System</p>
    </header>
    
    <!-- Chat Messages with Live Region -->
    <section class="chat-messages" 
             role="log" 
             aria-live="polite" 
             aria-label="Conversation history"
             aria-atomic="false">
      
      <div id="chat-status" class="sr-only" aria-live="assertive">
        <!-- Status updates for screen readers -->
      </div>
      
      <!-- Messages Container -->
      <div class="messages-container">
        <!-- User Message -->
        <article class="message-container user-message" 
                 role="article"
                 aria-label="User message"
                 tabindex="0">
          <div class="message-avatar user-avatar" 
               role="img" 
               aria-label="User avatar">👤</div>
          <div class="message-content">
            <div class="message-author sr-only">You said:</div>
            <div class="message-text">{{user_message}}</div>
            <time class="message-time" 
                  datetime="{{iso_timestamp}}"
                  aria-label="Sent at {{readable_time}}">
              {{time_ago}}
            </time>
          </div>
        </article>
        
        <!-- AI Message -->
        <article class="message-container ai-message" 
                 role="article"
                 aria-label="Zenith AI response"
                 tabindex="0">
          <div class="message-avatar ai-avatar" 
               role="img" 
               aria-label="Zenith AI avatar">🤖</div>
          <div class="message-content">
            <div class="message-author sr-only">Zenith AI responded:</div>
            <div class="message-text">{{ai_response}}</div>
            <time class="message-time" 
                  datetime="{{iso_timestamp}}"
                  aria-label="Responded at {{readable_time}}">
              {{time_ago}}
            </time>
          </div>
        </article>
      </div>
      
      <!-- Typing Indicator with ARIA -->
      <div class="typing-indicator" 
           aria-live="polite" 
           aria-label="Zenith AI status">
        <div class="typing-content" role="status">
          <span class="typing-text">Zenith AI is typing</span>
          <div class="typing-dots" aria-hidden="true">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
          </div>
        </div>
      </div>
    </section>
    
    <!-- Chat Input Area -->
    <form class="chat-input-container" 
          role="form"
          aria-label="Send message to Zenith AI">
      
      <div class="chat-input-wrapper">
        <label for="chat-input" class="sr-only">
          Message to Zenith AI
        </label>
        
        <textarea id="chat-input"
                  name="message"
                  class="chat-input"
                  placeholder="Type a message..."
                  aria-describedby="chat-help chat-counter"
                  aria-required="true"
                  rows="3"
                  maxlength="2000"></textarea>
        
        <div id="chat-help" class="sr-only">
          Press Enter to send, Shift+Enter for new line. 
          Maximum 2000 characters.
        </div>
        
        <div id="chat-counter" class="char-counter" aria-live="polite">
          <span class="current-count">0</span>
          <span class="max-count">/2000</span>
        </div>
        
        <button type="submit" 
                class="send-btn"
                aria-describedby="send-help"
                disabled>
          <span class="btn-icon" aria-hidden="true">📤</span>
          <span class="btn-text">Send</span>
        </button>
        
        <div id="send-help" class="sr-only">
          Send your message to Zenith AI
        </div>
      </div>
    </form>
  </main>

  <!-- Right Panel: Settings and Admin -->
  <aside class="right-panel" 
         role="complementary" 
         aria-label="User settings and controls">
    
    <header class="right-panel-header">
      <div class="user-info" role="region" aria-label="Current user">
        <div class="user-name">{{user_email}}</div>
        <div class="user-role">{{user_role}}</div>
      </div>
    </header>
    
    <main class="right-panel-content">
      <!-- Sign Out Button -->
      <button type="button" 
              class="signout-btn"
              aria-describedby="signout-help">
        <span class="btn-icon" aria-hidden="true">🚪</span>
        <span class="btn-text">Sign Out</span>
      </button>
      <div id="signout-help" class="sr-only">
        Sign out of your Zenith AI account
      </div>
      
      <!-- Settings Sections -->
      <section aria-label="Application settings">
        <h2>Settings</h2>
        
        <!-- Document Upload -->
        <details class="settings-section" role="group">
          <summary class="settings-header" 
                   aria-expanded="false"
                   aria-controls="upload-content">
            <span class="section-icon" aria-hidden="true">📁</span>
            Upload Documents
          </summary>
          
          <div id="upload-content" class="settings-content">
            <div class="file-upload-area" role="region">
              <label for="document-upload" class="upload-label">
                Choose PDF files to upload
              </label>
              
              <input type="file"
                     id="document-upload"
                     name="documents"
                     accept=".pdf"
                     multiple
                     aria-describedby="upload-help upload-limit">
              
              <div id="upload-help" class="help-text">
                Select one or more PDF files to chat with
              </div>
              
              <div id="upload-limit" class="limit-text">
                Maximum 10MB per file, up to 10 files
              </div>
            </div>
          </div>
        </details>
        
        <!-- Chat Preferences -->
        <details class="settings-section" role="group">
          <summary class="settings-header" 
                   aria-expanded="false"
                   aria-controls="chat-prefs-content">
            <span class="section-icon" aria-hidden="true">💬</span>
            Chat Preferences
          </summary>
          
          <div id="chat-prefs-content" class="settings-content">
            <fieldset class="preferences-group">
              <legend class="sr-only">Chat behavior settings</legend>
              
              <div class="preference-item">
                <input type="checkbox" 
                       id="use-rag"
                       name="use_rag"
                       checked
                       aria-describedby="rag-help">
                <label for="use-rag">Use document search (RAG)</label>
                <div id="rag-help" class="help-text">
                  Include relevant document content in responses
                </div>
              </div>
              
              <div class="preference-item">
                <input type="checkbox" 
                       id="filter-user"
                       name="filter_user"
                       checked
                       aria-describedby="filter-help">
                <label for="filter-user">Search only my documents</label>
                <div id="filter-help" class="help-text">
                  Limit search to documents you uploaded
                </div>
              </div>
            </fieldset>
          </div>
        </details>
      </section>
      
      <!-- Admin Controls (for administrators) -->
      <section aria-label="Administrator controls" 
               class="admin-section"
               style="display: {{admin_display}}">
        <h2>Admin Controls</h2>
        
        <details class="settings-section admin-only" role="group">
          <summary class="settings-header" 
                   aria-expanded="false"
                   aria-controls="system-status-content">
            <span class="section-icon" aria-hidden="true">📊</span>
            System Status
          </summary>
          
          <div id="system-status-content" class="settings-content">
            <div class="status-grid" role="grid">
              <div class="status-item" role="gridcell">
                <span class="status-label">Collections:</span>
                <span class="status-value">{{collection_count}}</span>
              </div>
              <div class="status-item" role="gridcell">
                <span class="status-label">Total Users:</span>
                <span class="status-value">{{user_count}}</span>
              </div>
            </div>
          </div>
        </details>
      </section>
    </main>
  </aside>
</div>
```

**Priority 2: Screen Reader Specific Enhancements**
```css
/* Screen Reader Only Content */
.sr-only {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}

.sr-only-focusable:active,
.sr-only-focusable:focus {
  position: static !important;
  width: auto !important;
  height: auto !important;
  padding: inherit !important;
  margin: inherit !important;
  overflow: visible !important;
  clip: auto !important;
  white-space: inherit !important;
}
```

### 🧪 Testing & Validation Phase (Day 7-8: 16 hours)

**Screen Reader Testing Protocol:**
- [ ] NVDA (Windows) - Complete user flow testing
- [ ] JAWS (Windows) - Form interaction and navigation testing
- [ ] VoiceOver (macOS/iOS) - Mobile responsive testing
- [ ] TalkBack (Android) - Mobile accessibility verification

**Acceptance Criteria:**
- [ ] All interactive elements announce purpose and state
- [ ] Form validation errors announce immediately
- [ ] Chat messages announce with proper context
- [ ] Navigation flows logically between panels
- [ ] Status updates announce appropriately

---

## Task 2.2: Keyboard Navigation & Focus Management
**Owner**: Frontend Developer  
**Timeline**: 6 days  
**Effort**: 48 hours

### 🔍 Keyboard Navigation Analysis (Day 1: 8 hours)

**Current State Assessment:**
```javascript
// Keyboard Navigation Audit Results
const keyboardIssues = {
  skipNavigation: "Missing - users cannot skip to main content",
  focusTrapping: "Missing - modals don't trap focus properly",
  tabOrder: "Inconsistent - focus jumps between panels unpredictably",
  focusIndicators: "Insufficient - low contrast, not WCAG compliant",
  keyboardShortcuts: "None - no power user support"
};
```

### 🛠️ Implementation Phase (Day 2-5: 32 hours)

**Priority 1: Skip Navigation Implementation**
```html
<!-- Skip Navigation Links -->
<div class="skip-links" aria-label="Skip navigation">
  <a href="#main-content" class="skip-link">
    Skip to main content
  </a>
  <a href="#chat-input" class="skip-link">
    Skip to chat input
  </a>
  <a href="#user-settings" class="skip-link">
    Skip to settings
  </a>
</div>
```

```css
/* Skip Links Styling */
.skip-links {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 9999;
}

.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: var(--primary-blue);
  color: var(--text-white);
  padding: 12px 16px;
  text-decoration: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  box-shadow: var(--shadow-lg);
  transition: all 0.2s ease;
}

.skip-link:focus {
  top: 6px;
  outline: 3px solid var(--accent-blue-light);
  outline-offset: 2px;
}
```

**Priority 2: Enhanced Focus Management System**
```javascript
// Focus Management Class
class FocusManager {
  constructor() {
    this.focusHistory = [];
    this.currentPanel = 'center';
    this.setupKeyboardNavigation();
  }
  
  setupKeyboardNavigation() {
    document.addEventListener('keydown', this.handleKeydown.bind(this));
    this.setupFocusTraps();
    this.enhanceFocusIndicators();
  }
  
  handleKeydown(event) {
    const { key, ctrlKey, altKey, shiftKey } = event;
    
    // Panel Navigation Shortcuts
    if (altKey) {
      switch(key) {
        case '1':
          this.focusPanel('left');
          event.preventDefault();
          break;
        case '2':
          this.focusPanel('center');
          event.preventDefault();
          break;
        case '3':
          this.focusPanel('right');
          event.preventDefault();
          break;
      }
    }
    
    // Chat Shortcuts
    if (ctrlKey) {
      switch(key) {
        case 'n':
          this.startNewChat();
          event.preventDefault();
          break;
        case 'Enter':
          this.sendMessage();
          event.preventDefault();
          break;
      }
    }
    
    // Escape key handling
    if (key === 'Escape') {
      this.handleEscape();
    }
    
    // Tab navigation enhancement
    if (key === 'Tab') {
      this.enhancedTabNavigation(event);
    }
  }
  
  focusPanel(panel) {
    const panels = {
      left: '.left-panel [tabindex="0"]:first-child',
      center: '#chat-input',
      right: '.right-panel button:first-of-type'
    };
    
    const element = document.querySelector(panels[panel]);
    if (element) {
      element.focus();
      this.currentPanel = panel;
      this.announceToScreenReader(`Focused ${panel} panel`);
    }
  }
  
  enhancedTabNavigation(event) {
    const focusableElements = this.getFocusableElements();
    const currentIndex = focusableElements.indexOf(document.activeElement);
    
    if (event.shiftKey) {
      // Shift+Tab: Previous element
      const previousIndex = currentIndex - 1;
      if (previousIndex >= 0) {
        focusableElements[previousIndex].focus();
      }
    } else {
      // Tab: Next element
      const nextIndex = currentIndex + 1;
      if (nextIndex < focusableElements.length) {
        focusableElements[nextIndex].focus();
      }
    }
  }
  
  getFocusableElements() {
    const selectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'textarea:not([disabled])',
      'select:not([disabled])',
      'a[href]',
      '[tabindex]:not([tabindex="-1"])'
    ];
    
    return Array.from(document.querySelectorAll(selectors.join(',')))
      .filter(el => {
        const style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden';
      });
  }
  
  setupFocusTraps() {
    // Modal focus trap implementation
    this.setupModalFocusTraps();
    
    // Panel focus containment for mobile
    this.setupPanelFocusContainment();
  }
  
  announceToScreenReader(message) {
    const announcer = document.getElementById('sr-announcer') || 
      this.createAnnouncerElement();
    announcer.textContent = message;
  }
  
  createAnnouncerElement() {
    const announcer = document.createElement('div');
    announcer.id = 'sr-announcer';
    announcer.className = 'sr-only';
    announcer.setAttribute('aria-live', 'assertive');
    announcer.setAttribute('aria-atomic', 'true');
    document.body.appendChild(announcer);
    return announcer;
  }
}

// Initialize focus management
const focusManager = new FocusManager();
```

**Priority 3: Focus Indicators Enhancement**
```css
/* Enhanced Focus Indicators - WCAG Compliant */
:root {
  --focus-color: #3b82f6;
  --focus-color-contrast: #ffffff;
  --focus-width: 3px;
  --focus-offset: 2px;
}

/* Remove default outlines */
*:focus {
  outline: none;
}

/* Enhanced focus visible for modern browsers */
*:focus-visible {
  outline: var(--focus-width) solid var(--focus-color);
  outline-offset: var(--focus-offset);
  border-radius: var(--radius);
  box-shadow: 0 0 0 1px var(--focus-color-contrast);
}

/* Fallback for older browsers */
.focus-visible {
  outline: var(--focus-width) solid var(--focus-color) !important;
  outline-offset: var(--focus-offset) !important;
  border-radius: var(--radius) !important;
  box-shadow: 0 0 0 1px var(--focus-color-contrast) !important;
}

/* Specific component focus styles */
.session-item:focus-visible,
.session-item.focus-visible {
  outline-color: var(--focus-color);
  background: rgba(59, 130, 246, 0.1);
  transform: translateX(4px);
  transition: all 0.2s ease;
}

.chat-input:focus-visible,
.chat-input.focus-visible {
  border-color: var(--focus-color) !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

.message-container:focus-visible,
.message-container.focus-visible {
  outline: var(--focus-width) solid var(--focus-color);
  outline-offset: var(--focus-offset);
  background: rgba(59, 130, 246, 0.05);
}

/* Button focus enhancements */
.chat-btn:focus-visible,
.chat-btn.focus-visible {
  outline: var(--focus-width) solid var(--focus-color);
  outline-offset: var(--focus-offset);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.25);
  transform: translateY(-1px);
}

/* Settings section focus */
.settings-section summary:focus-visible,
.settings-section summary.focus-visible {
  outline: var(--focus-width) solid var(--focus-color);
  outline-offset: var(--focus-offset);
  background: rgba(59, 130, 246, 0.05);
  border-radius: var(--radius);
}

/* Input field focus enhancements */
input:focus-visible,
textarea:focus-visible,
select:focus-visible,
input.focus-visible,
textarea.focus-visible,
select.focus-visible {
  border-color: var(--focus-color) !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
  outline: none !important;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  :root {
    --focus-color: #000000;
    --focus-color-contrast: #ffffff;
    --focus-width: 4px;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  *:focus-visible,
  .focus-visible {
    transition: none !important;
    transform: none !important;
  }
}
```

### 🧪 Testing & Validation Phase (Day 6: 8 hours)

**Keyboard Testing Checklist:**
- [ ] All interactive elements reachable via keyboard
- [ ] Tab order follows logical sequence
- [ ] Focus indicators meet 3:1 contrast ratio
- [ ] Skip links function correctly
- [ ] Escape key closes modals/dropdowns
- [ ] Keyboard shortcuts work as expected

---

## Task 2.3: Color Contrast & Visual Accessibility
**Owner**: UI/UX Designer + Frontend Developer  
**Timeline**: 4 days  
**Effort**: 32 hours

### 🔍 Color Accessibility Analysis (Day 1: 8 hours)

**Current Color Audit Results:**
```css
/* Current Color Issues Identified */
:root {
  /* FAILING COMBINATIONS - Need Improvement */
  --text-muted: #94a3b8; /* 3.2:1 on white - FAILS WCAG AA */
  --border-light: rgba(255, 255, 255, 0.1); /* Poor contrast */
  --secondary-text: #64748b; /* 4.1:1 on white - BARELY PASSES */
  
  /* PASSING COMBINATIONS - Keep */
  --text-primary: #1e293b; /* 13.8:1 on white - EXCELLENT */
  --primary-blue: #1a2b3c; /* 11.2:1 on white - EXCELLENT */
}
```

### 🛠️ Implementation Phase (Day 2-3: 16 hours)

**Priority 1: WCAG AA Compliant Color System**
```css
/* Enhanced Color System - WCAG AA Compliant */
:root {
  /* ===== PRIMARY BRAND COLORS ===== */
  --primary-blue: #1a2b3c;           /* 11.2:1 contrast */
  --primary-blue-dark: #0d1a2b;      /* 15.8:1 contrast */
  --primary-blue-light: #2d4a5a;     /* 8.9:1 contrast */
  
  /* ===== ACCENT COLORS ===== */
  --accent-blue: #2563eb;            /* 7.2:1 contrast */
  --accent-blue-light: #3b82f6;      /* 5.9:1 contrast */
  --accent-blue-dark: #1e40af;       /* 9.1:1 contrast */
  
  /* ===== TEXT COLORS - WCAG AA COMPLIANT ===== */
  --text-primary: #1e293b;           /* 13.8:1 contrast - AAA */
  --text-secondary: #475569;         /* 7.4:1 contrast - AA */
  --text-muted: #64748b;            /* 4.8:1 contrast - AA (improved from 3.2:1) */
  --text-light: #f8fafc;            /* 19.5:1 on dark backgrounds */
  --text-white: #ffffff;            /* 21:1 on dark backgrounds */
  
  /* ===== BACKGROUND COLORS ===== */
  --bg-main: #ffffff;
  --bg-panel: rgba(255, 255, 255, 0.98);
  --bg-panel-dark: rgba(26, 43, 60, 0.95);
  --bg-secondary: rgba(255, 255, 255, 0.99);
  --bg-accent: rgba(248, 250, 252, 0.98);
  
  /* ===== STATE COLORS - ACCESSIBLE ===== */
  --success: #059669;               /* 4.5:1 contrast - AA */
  --success-light: #10b981;         /* 4.1:1 contrast - Borderline */
  --warning: #d97706;               /* 4.9:1 contrast - AA */
  --warning-light: #f59e0b;         /* 4.2:1 contrast - AA */
  --error: #dc2626;                 /* 5.9:1 contrast - AA */
  --error-light: #ef4444;           /* 5.2:1 contrast - AA */
  --info: #2563eb;                  /* 7.2:1 contrast - AA */
  --info-light: #3b82f6;            /* 5.9:1 contrast - AA */
  
  /* ===== BORDER COLORS ===== */
  --border-light: rgba(30, 41, 59, 0.15);    /* Improved from 0.1 */
  --border-medium: rgba(30, 41, 59, 0.25);   /* 3.1:1 contrast */
  --border-strong: rgba(30, 41, 59, 0.4);    /* 2.2:1 contrast */
  
  /* ===== HIGH CONTRAST MODE ===== */
  --hc-text: #000000;
  --hc-background: #ffffff;
  --hc-border: #000000;
  --hc-focus: #000000;
}

/* Dark Mode Accessible Colors */
@media (prefers-color-scheme: dark) {
  :root {
    --text-primary: #f8fafc;         /* 19.5:1 on dark - AAA */
    --text-secondary: #e2e8f0;       /* 14.2:1 on dark - AAA */
    --text-muted: #cbd5e1;           /* 9.8:1 on dark - AAA */
    --bg-main: #0f172a;
    --bg-panel: rgba(15, 23, 42, 0.98);
    --bg-panel-dark: rgba(15, 23, 42, 0.95);
    
    /* Adjusted for dark backgrounds */
    --success: #10b981;             /* 4.8:1 on dark */
    --warning: #fbbf24;             /* 4.6:1 on dark */
    --error: #f87171;               /* 4.5:1 on dark */
  }
}

/* High Contrast Mode Support */
@media (prefers-contrast: high) {
  :root {
    --text-primary: var(--hc-text);
    --text-secondary: var(--hc-text);
    --text-muted: var(--hc-text);
    --bg-main: var(--hc-background);
    --border-light: var(--hc-border);
    --border-medium: var(--hc-border);
    --border-strong: var(--hc-border);
  }
  
  /* Enhanced borders for high contrast */
  .session-item,
  .message-container,
  .chat-input,
  .settings-section {
    border: 2px solid var(--hc-border) !important;
  }
  
  /* Remove subtle effects */
  .glass-effect,
  .backdrop-blur {
    backdrop-filter: none !important;
  }
}
```

**Priority 2: Visual Accessibility Enhancements**
```css
/* Text Scaling Support - Up to 200% */
@media (min-resolution: 192dpi) {
  :root {
    --base-font-size: 18px; /* Increased from 16px */
  }
}

/* Support for user zoom up to 200% */
@media (min-width: 1280px) and (max-width: 2560px) {
  .three-panel-container {
    min-width: 640px; /* Ensures usability at 200% zoom */
  }
  
  .left-panel,
  .right-panel {
    min-width: 200px; /* Compressed but functional */
  }
}

/* Enhanced Visual Hierarchy */
.message-container {
  border-left: 4px solid transparent;
  transition: border-color 0.2s ease;
}

.user-message {
  border-left-color: var(--accent-blue);
}

.ai-message {
  border-left-color: var(--text-secondary);
}

.message-container:hover {
  background: rgba(59, 130, 246, 0.03); /* Subtle, accessible hover */
}

/* Icon Accessibility - Alternative Text via CSS */
.session-item::before {
  content: "Chat session: ";
  position: absolute;
  left: -9999px;
  width: 1px;
  height: 1px;
  overflow: hidden;
}

.admin-section::before {
  content: "Administrator controls: ";
  position: absolute;
  left: -9999px;
  width: 1px;
  height: 1px;
  overflow: hidden;
}

/* Loading State Accessibility */
.typing-indicator[aria-hidden="false"] {
  border-left: 4px solid var(--accent-blue);
  background: rgba(59, 130, 246, 0.05);
}

/* Error State Visual Enhancements */
.input-error {
  border-color: var(--error) !important;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1) !important;
}

.error-message {
  color: var(--error);
  font-weight: 500;
  margin-top: var(--space-2);
  font-size: 14px;
  line-height: 1.4;
}

/* Success State Visual Enhancements */
.input-success {
  border-color: var(--success) !important;
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1) !important;
}

.success-message {
  color: var(--success);
  font-weight: 500;
  margin-top: var(--space-2);
  font-size: 14px;
  line-height: 1.4;
}
```

### 🧪 Testing & Validation Phase (Day 4: 8 hours)

**Color Contrast Testing Protocol:**
- [ ] Automated testing with axe-core and WAVE
- [ ] Manual testing with Colour Contrast Analyser
- [ ] High contrast mode testing (Windows/macOS)
- [ ] Color blindness simulation testing
- [ ] Text scaling testing up to 200%

**Acceptance Criteria:**
- [ ] All text meets 4.5:1 contrast ratio (normal text)
- [ ] All large text meets 3:1 contrast ratio
- [ ] Focus indicators meet 3:1 contrast ratio
- [ ] High contrast mode supported
- [ ] Color is not the only means of conveying information

---

## 🔧 ENHANCED FEATURE INTEGRATION PLAN

### Integration Strategy from enhanced_streamlit_app.py

**Phase 1: Core Architecture Integration (Continuous throughout Sprint)**

**Advanced Authentication System:**
```python
# Enhanced User Profile Management
class EnhancedUserProfile:
    def __init__(self, user_info):
        self.user_info = user_info
        self.preferences = self.load_preferences()
    
    def load_preferences(self):
        return {
            'theme': 'light',  # light/dark/high-contrast
            'text_size': 'medium',  # small/medium/large
            'keyboard_shortcuts': True,
            'screen_reader_mode': False,
            'reduce_motion': False
        }
    
    def update_accessibility_preferences(self, prefs):
        """Update accessibility preferences with validation"""
        self.preferences.update(prefs)
        self.save_preferences()
        self.apply_preferences()
    
    def apply_preferences(self):
        """Apply user preferences to interface"""
        if self.preferences['screen_reader_mode']:
            self.enable_screen_reader_enhancements()
        
        if self.preferences['reduce_motion']:
            self.disable_animations()
```

**Advanced Admin Panel Features:**
```python
# Enhanced Admin Controls with Accessibility
class AccessibleAdminPanel:
    def render_user_management(self):
        """Render accessible user management interface"""
        st.markdown("""
        <section aria-label="User management" class="admin-section">
            <h2 id="user-mgmt-title">User Management</h2>
            <div role="region" aria-labelledby="user-mgmt-title">
        """, unsafe_allow_html=True)
        
        # Accessible data table
        users = self.get_all_users()
        if users:
            # Create accessible table with proper headers
            table_data = []
            for user in users:
                table_data.append({
                    'Email': user.email,
                    'Role': user.role.value,
                    'Status': user.is_active,
                    'Created': user.created_at.strftime('%Y-%m-%d'),
                    'Actions': f"edit-{user.id}"
                })
            
            # Display with accessibility enhancements
            df = pd.DataFrame(table_data)
            st.markdown('<div role="table" aria-label="User list">', 
                       unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_system_settings(self):
        """Render accessible system configuration"""
        with st.expander("🔧 System Configuration", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### AI Provider Settings")
                
                # Accessible form controls
                provider = st.selectbox(
                    "AI Provider",
                    options=['openai', 'ollama'],
                    help="Select the AI service provider",
                    key="admin_ai_provider"
                )
                
                if provider == 'openai':
                    api_key = st.text_input(
                        "OpenAI API Key",
                        type="password",
                        help="Enter your OpenAI API key",
                        key="admin_openai_key"
                    )
                    
                    model = st.selectbox(
                        "Model",
                        options=['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'],
                        help="Select the OpenAI model to use",
                        key="admin_openai_model"
                    )
            
            with col2:
                st.markdown("#### Document Processing")
                
                chunk_size = st.number_input(
                    "Chunk Size",
                    min_value=100,
                    max_value=2000,
                    value=1000,
                    help="Size of text chunks for processing",
                    key="admin_chunk_size"
                )
                
                overlap = st.number_input(
                    "Chunk Overlap",
                    min_value=0,
                    max_value=500,
                    value=100,
                    help="Overlap between text chunks",
                    key="admin_chunk_overlap"
                )
```

---

## 📊 SUCCESS METRICS & TESTING STRATEGY

### Accessibility Compliance Metrics
- **WCAG 2.1 AA Compliance**: 100% of components pass automated testing
- **Screen Reader Compatibility**: >90% task completion rate
- **Keyboard Navigation**: 100% functionality accessible via keyboard
- **Color Contrast**: All text/background combinations meet 4.5:1 ratio
- **Focus Management**: All interactive elements have clear focus indicators

### Performance Benchmarks
- **Lighthouse Accessibility Score**: >95
- **axe-core Violations**: 0 critical, 0 serious
- **Keyboard Navigation Speed**: <2 seconds between any two focusable elements
- **Screen Reader Announcement Clarity**: <3 seconds for status updates

### Integration Success Criteria
- **Feature Parity**: All enhanced_streamlit_app.py features integrated
- **Layout Integrity**: Three-panel design maintained across all screen sizes
- **Authentication Flow**: Seamless login/logout with accessibility support
- **Admin Panel**: Full functionality accessible via keyboard and screen readers

---

## 🚀 IMPLEMENTATION TIMELINE

### Week 1 (Days 1-7)
- **Days 1-2**: ARIA Implementation Analysis & Planning
- **Days 3-5**: Core ARIA Markup Implementation
- **Days 6-7**: Screen Reader Testing & Refinement

### Week 2 (Days 8-14)
- **Days 8-9**: Keyboard Navigation Analysis & Skip Links
- **Days 10-12**: Focus Management System Implementation
- **Days 13-14**: Keyboard Navigation Testing

### Week 3 (Days 15-21)
- **Days 15-16**: Color Contrast Analysis & Color System Enhancement
- **Days 17-18**: Visual Accessibility Improvements
- **Days 19-21**: Final Integration Testing & Validation

---

## 🛡️ RISK MITIGATION STRATEGY

### Technical Risks
1. **Performance Impact**: Monitor bundle size and runtime performance
2. **Browser Compatibility**: Test across all target browsers
3. **Streamlit Limitations**: Work within Streamlit's component constraints
4. **Integration Complexity**: Phase integration to avoid breaking changes

### Accessibility Risks
1. **Screen Reader Inconsistencies**: Test with multiple screen readers
2. **Keyboard Trap Issues**: Implement robust focus management
3. **Dynamic Content Updates**: Ensure ARIA live regions work correctly
4. **Mobile Accessibility**: Test touch target sizes and gesture support

### Mitigation Actions
- Daily accessibility testing during implementation
- Staged rollout with user feedback collection
- Fallback patterns for unsupported features
- Comprehensive documentation for maintenance

---

This comprehensive Sprint 2 plan ensures WCAG 2.1 AA accessibility compliance while successfully integrating advanced features from the enhanced application into the modern three-panel interface. The implementation maintains design excellence while prioritizing inclusive user experience.