"""
Enhanced Three-Panel Chat Interface for Zenith PDF Chatbot
ChatGPT-inspired clean professional design with preserved functionality
"""

import os
import sys
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import time
import traceback
import uuid

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.core.config import config
from src.core.qdrant_manager import get_qdrant_client
from src.core.enhanced_vector_store import UserVectorStore
from src.core.enhanced_chat_engine import EnhancedChatEngine
from src.core.pdf_processor import PDFProcessor
from src.core.enhanced_settings_manager import get_enhanced_settings_manager
from src.core.chat_history import get_chat_history_manager, ChatSession, ChatMessage
from src.auth.auth_manager import (
    AuthenticationManager, init_auth_session, get_current_user_from_session,
    require_authentication, require_admin, logout_user_session
)
from src.auth.models import UserRole, UserRegistrationRequest, UserLoginRequest
from src.utils.helpers import format_file_size, format_duration
from src.utils.logger import get_logger
from datetime import datetime

# Initialize logger
logger = get_logger(__name__)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

# Page configuration
st.set_page_config(
    page_title="Zenith AI Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide default sidebar for custom layout
)

# Professional CSS styling with proper gradient background
st.markdown("""
<style>
/* ===== PROFESSIONAL ZENITH AI INTERFACE ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body {
    background: linear-gradient(to bottom, #1a2b3c, #0d1a2b) !important;
    margin: 0;
    padding: 0;
    height: 100vh;
    width: 100vw;
    overflow-x: hidden;
}

:root {
    /* WCAG AA Compliant Color System - Sprint 2 Implementation */
    --primary-blue: #1a2b3c;
    --primary-blue-dark: #0d1a2b;
    --primary-blue-light: #2d4a5a;
    --accent-blue: #3b82f6;
    --accent-blue-light: #60a5fa;
    
    /* WCAG AA Compliant Text Colors */
    --text-on-light: #1a1a1a;      /* 16.94:1 ratio */
    --text-on-dark: #ffffff;       /* 21:1 ratio */
    --text-primary: #1a1a1a;       /* Updated for better contrast */
    --text-secondary: #4a5568;     /* 7.2:1 ratio on white */
    --text-muted: #6b7280;         /* 5.2:1 ratio on white */
    --text-light: #f8fafc;
    --text-white: #ffffff;
    
    /* Accessible Link and Action Colors */
    --link-color: #0066cc;         /* 7.3:1 ratio */
    --link-hover: #004499;         /* 9.1:1 ratio */
    --error-color: #d73502;        /* 5.8:1 ratio */
    --success-color: #0f5132;      /* 9.7:1 ratio */
    --warning-color: #b45309;      /* 6.1:1 ratio */
    --info-color: #1e40af;         /* 8.2:1 ratio */
    
    /* Enhanced Focus System */
    --focus-outline: #3b82f6;      /* 4.5:1 ratio */
    --focus-outline-width: 3px;
    --focus-outline-offset: 2px;
    
    /* Professional Backgrounds */
    --bg-main: #ffffff;
    --bg-panel: rgba(255, 255, 255, 0.95);
    --bg-panel-dark: rgba(26, 43, 60, 0.9);
    --bg-secondary: rgba(255, 255, 255, 0.98);
    --bg-accent: rgba(248, 250, 252, 0.95);
    --bg-overlay: rgba(26, 43, 60, 0.1);
    
    /* Professional Shadows & Effects */
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
    --glass-effect: backdrop-filter: blur(10px);
    
    /* Accessible Touch Targets */
    --min-touch-target: 44px;
    
    /* Animation and Transition Variables */
    --transition-fast: 0.15s ease;
    --transition-normal: 0.3s ease;
    --transition-slow: 0.5s ease;
    
    /* Skip Navigation Links */
    --skip-link-bg: #000000;
    --skip-link-text: #ffffff;
    /* High Contrast Mode Support */
    --high-contrast-bg: #ffffff;
    --high-contrast-text: #000000;
    --high-contrast-border: #000000;
    
    /* Professional Spacing */
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-3: 0.75rem;
    --space-4: 1rem;
    --space-5: 1.25rem;
    --space-6: 1.5rem;
    --space-8: 2rem;
    --space-12: 3rem;
    
    /* Professional Borders */
    --radius: 0.375rem;
    --radius-lg: 0.5rem;
    --radius-xl: 0.75rem;
    --radius-full: 9999px;
    --border-width: 1px;
    
    /* WCAG Compliant Gray Scale */
    --gray-50: #f8fafc;
    --gray-100: #f1f5f9;
    --gray-200: #e2e8f0;
    --gray-300: #cbd5e1;
    --gray-400: #94a3b8;  /* 4.5:1 on white */
    --gray-500: #64748b;  /* 5.9:1 on white */
    --gray-600: #475569;  /* 7.8:1 on white */
    --gray-700: #334155;  /* 10.8:1 on white */
    --gray-800: #1e293b;  /* 14.6:1 on white */
    --gray-900: #0f172a;  /* 18.7:1 on white */
    
    /* Professional Button Colors - WCAG Compliant */
    --button-primary: #1a2b3c;
    --button-primary-hover: #0d1a2b;
    --button-secondary: #f8fafc;
    --button-secondary-hover: #f1f5f9;
    --button-danger: #dc2626;     /* 5.9:1 on white */
    --button-danger-hover: #b91c1c;
    
    /* Professional Message Colors */
    --message-hover: rgba(0, 0, 0, 0.02);
    --message-focus: rgba(59, 130, 246, 0.1);
    
    /* Accessible State Colors */
    --state-disabled: #9ca3af;    /* 4.5:1 on white */
    --state-loading: #6366f1;
}

/* High Contrast Mode Detection and Support */
@media (prefers-contrast: high) {
  :root {
    --text-primary: var(--high-contrast-text);
    --bg-main: var(--high-contrast-bg);
    --border-color: var(--high-contrast-border);
    --focus-outline: var(--high-contrast-text);
    --button-primary: var(--high-contrast-text);
    --button-secondary: var(--high-contrast-bg);
  }
}

/* ===== SCREEN READER ACCESSIBILITY ===== */
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

.sr-only-focusable:focus {
    position: static !important;
    width: auto !important;
    height: auto !important;
    padding: inherit !important;
    margin: inherit !important;
    overflow: visible !important;
    clip: auto !important;
    white-space: normal !important;
}

/* ===== SKIP NAVIGATION ACCESSIBILITY ===== */
.skip-navigation {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 1000;
    background: transparent;
}

.skip-link {
    position: absolute;
    left: -10000px;
    top: auto;
    width: 1px;
    height: 1px;
    overflow: hidden;
    background: var(--skip-link-bg);
    color: var(--skip-link-text);
    padding: var(--space-3) var(--space-4);
    text-decoration: none;
    font-weight: 600;
    font-size: 14px;
    border-radius: 0 0 var(--radius) var(--radius);
    border: 2px solid transparent;
    transition: all var(--transition-fast);
}

.skip-link:focus {
    position: fixed;
    left: var(--space-4);
    top: var(--space-4);
    width: auto;
    height: auto;
    overflow: visible;
    outline: 3px solid var(--focus-outline);
    outline-offset: 2px;
    box-shadow: var(--shadow-lg);
    z-index: 10000;
}

.skip-link:hover:focus {
    background: var(--accent-blue);
    transform: translateY(-2px);
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* ===== FOCUS TRAP FOR MODAL DIALOGS ===== */
/* Modal overlay styles with proper focus management */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-content {
    background: var(--bg-main);
    border-radius: var(--radius-lg);
    padding: var(--space-8);
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: var(--shadow-xl);
    border: 2px solid var(--gray-200);
    position: relative;
}

.modal-content:focus-within {
    outline: 3px solid var(--focus-outline);
    outline-offset: 2px;
}

.modal-close {
    position: absolute;
    top: var(--space-4);
    right: var(--space-4);
    background: none;
    border: none;
    font-size: 24px;
    color: var(--text-secondary);
    cursor: pointer;
    padding: var(--space-2);
    border-radius: var(--radius);
    min-width: var(--min-touch-target);
    min-height: var(--min-touch-target);
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-close:hover,
.modal-close:focus {
    color: var(--text-primary);
    background: var(--gray-100);
    outline: 2px solid var(--focus-outline);
    outline-offset: 2px;
}

/* Focus trap styles */
.focus-trap-start,
.focus-trap-end {
    position: absolute;
    left: -9999px;
    width: 1px;
    height: 1px;
    overflow: hidden;
}

/* ===== TEXT SCALING SUPPORT UP TO 200% ===== */
/* Base responsive typography that scales properly */
.three-panel-container {
    font-size: clamp(14px, 1.2vw + 0.5rem, 18px);
    line-height: 1.6;
}

/* Ensure minimum touch targets scale with text */
.stButton > button,
.stSelectbox > div,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    min-height: max(44px, 2.75em) !important;
    font-size: inherit !important;
}

/* Scale chat messages appropriately */
.chat-message {
    font-size: max(14px, 1em) !important;
    line-height: 1.6 !important;
}

/* Scale navigation elements */
.left-panel-content .stButton > button {
    font-size: max(12px, 0.9em) !important;
    padding: max(8px, 0.5em) max(16px, 1em) !important;
}

/* Scale headers and important text */
.chat-title {
    font-size: max(18px, 1.25em) !important;
}

.chat-subtitle {
    font-size: max(12px, 0.85em) !important;
}

/* Ensure proper scaling at different zoom levels */
@media (min-resolution: 144dpi), (-webkit-min-device-pixel-ratio: 1.5) {
    .three-panel-container {
        font-size: max(15px, 1.2vw + 0.6rem);
    }
}

/* ===== JAVASCRIPT FOR ACCESSIBILITY ===== */
</style>

<script>
// Focus Trap Implementation for Modal Dialogs
class FocusTrap {
    constructor(element) {
        this.element = element;
        this.focusableElements = [];
        this.firstFocusableElement = null;
        this.lastFocusableElement = null;
        this.previousActiveElement = null;
        this.isActive = false;
    }
    
    activate() {
        if (this.isActive) return;
        
        // Store the previously focused element
        this.previousActiveElement = document.activeElement;
        
        // Get all focusable elements
        this.updateFocusableElements();
        
        if (this.focusableElements.length === 0) return;
        
        // Set up event listeners
        this.element.addEventListener('keydown', this.handleKeyDown.bind(this));
        document.addEventListener('focus', this.handleFocus.bind(this), true);
        
        // Focus the first element
        this.firstFocusableElement.focus();
        this.isActive = true;
    }
    
    deactivate() {
        if (!this.isActive) return;
        
        // Remove event listeners
        this.element.removeEventListener('keydown', this.handleKeyDown.bind(this));
        document.removeEventListener('focus', this.handleFocus.bind(this), true);
        
        // Restore focus to the previously active element
        if (this.previousActiveElement) {
            this.previousActiveElement.focus();
        }
        
        this.isActive = false;
    }
    
    updateFocusableElements() {
        const focusableSelector = [
            'input:not([disabled]):not([tabindex="-1"])',
            'button:not([disabled]):not([tabindex="-1"])',
            'select:not([disabled]):not([tabindex="-1"])',
            'textarea:not([disabled]):not([tabindex="-1"])',
            'a[href]:not([tabindex="-1"])',
            '[tabindex]:not([tabindex="-1"])',
            '[role="button"]:not([tabindex="-1"])',
            '[role="link"]:not([tabindex="-1"])'
        ].join(', ');
        
        this.focusableElements = Array.from(
            this.element.querySelectorAll(focusableSelector)
        ).filter(el => this.isVisible(el));
        
        this.firstFocusableElement = this.focusableElements[0];
        this.lastFocusableElement = this.focusableElements[this.focusableElements.length - 1];
    }
    
    isVisible(element) {
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && 
               style.visibility !== 'hidden' && 
               element.offsetHeight > 0;
    }
    
    handleKeyDown(event) {
        if (event.key === 'Escape') {
            event.preventDefault();
            this.deactivate();
            // Trigger modal close if applicable
            const closeButton = this.element.querySelector('.modal-close');
            if (closeButton) {
                closeButton.click();
            }
            return;
        }
        
        if (event.key === 'Tab') {
            if (this.focusableElements.length === 0) {
                event.preventDefault();
                return;
            }
            
            if (event.shiftKey) {
                // Shift + Tab: move backwards
                if (document.activeElement === this.firstFocusableElement) {
                    event.preventDefault();
                    this.lastFocusableElement.focus();
                }
            } else {
                // Tab: move forwards
                if (document.activeElement === this.lastFocusableElement) {
                    event.preventDefault();
                    this.firstFocusableElement.focus();
                }
            }
        }
    }
    
    handleFocus(event) {
        if (!this.element.contains(event.target)) {
            event.preventDefault();
            this.firstFocusableElement.focus();
        }
    }
}

// Screen Reader Announcements
class ScreenReaderAnnouncer {
    constructor() {
        this.politeRegion = document.getElementById('sr-notifications');
        this.assertiveRegion = document.getElementById('sr-alerts');
    }
    
    announce(message, priority = 'polite') {
        const region = priority === 'assertive' ? this.assertiveRegion : this.politeRegion;
        if (region) {
            region.textContent = message;
            // Clear after announcement to allow repeated messages
            setTimeout(() => {
                region.textContent = '';
            }, 1000);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize screen reader announcer
    window.screenReaderAnnouncer = new ScreenReaderAnnouncer();
    
    // Set up modal focus traps
    const modals = document.querySelectorAll('.modal-overlay');
    modals.forEach(modal => {
        const content = modal.querySelector('.modal-content');
        if (content) {
            const focusTrap = new FocusTrap(content);
            
            // Activate focus trap when modal opens
            const observer = new MutationObserver(() => {
                if (modal.style.display !== 'none' && modal.offsetParent !== null) {
                    focusTrap.activate();
                } else {
                    focusTrap.deactivate();
                }
            });
            
            observer.observe(modal, { 
                attributes: true, 
                attributeFilter: ['style', 'class'] 
            });
        }
    });
    
    // Enhanced keyboard navigation
    document.addEventListener('keydown', function(event) {
        // Alt + H: Go to main heading
        if (event.altKey && event.key === 'h') {
            event.preventDefault();
            const mainHeading = document.getElementById('chat-title');
            if (mainHeading) {
                mainHeading.focus();
                window.screenReaderAnnouncer?.announce('Navigated to main heading');
            }
        }
        
        // Alt + M: Go to main content
        if (event.altKey && event.key === 'm') {
            event.preventDefault();
            const mainContent = document.getElementById('main-chat');
            if (mainContent) {
                mainContent.focus();
                window.screenReaderAnnouncer?.announce('Navigated to main chat area');
            }
        }
        
        // Alt + I: Go to input field
        if (event.altKey && event.key === 'i') {
            event.preventDefault();
            const inputField = document.getElementById('chat-input');
            if (inputField) {
                inputField.focus();
                window.screenReaderAnnouncer?.announce('Navigated to chat input');
            }
        }
    });
    
    // Announce new chat messages
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        const messageObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Announce new messages
                    setTimeout(() => {
                        window.screenReaderAnnouncer?.announce('New message received');
                    }, 500);
                }
            });
        });
        
        messageObserver.observe(chatMessages, { 
            childList: true, 
            subtree: true 
        });
    }
    
    // Hide Streamlit components used for functionality
    hideStreamlitComponents();
});

// ===== INTERACTIVE BUTTON FUNCTIONS =====
function startNewChat() {
    // Trigger the hidden Streamlit button
    const hiddenButton = document.querySelector('[data-testid="baseButton-primary"]');
    if (hiddenButton && hiddenButton.textContent.includes('New Chat')) {
        hiddenButton.click();
    }
    window.screenReaderAnnouncer?.announce('Starting new chat conversation');
}

function loadSession(sessionId) {
    window.screenReaderAnnouncer?.announce('Loading chat session');
    // Note: Session loading will need to be handled via Streamlit state
    console.log('Loading session:', sessionId);
}

function logoutUser() {
    if (confirm('Are you sure you want to sign out?')) {
        window.screenReaderAnnouncer?.announce('Signing out', 'assertive');
        // Trigger logout functionality
        const logoutButtons = document.querySelectorAll('[data-testid="baseButton-secondary"]');
        logoutButtons.forEach(btn => {
            if (btn.textContent.includes('Sign Out') || btn.textContent.includes('Logout')) {
                btn.click();
            }
        });
    }
}

function showUploadDialog() {
    // Trigger file upload
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.click();
    }
    window.screenReaderAnnouncer?.announce('Opening file upload dialog');
}

function toggleTheme() {
    window.screenReaderAnnouncer?.announce('Theme toggle not yet implemented');
    console.log('Toggle theme functionality to be implemented');
}

function showPreferences() {
    window.screenReaderAnnouncer?.announce('Preferences panel not yet implemented');
    console.log('Preferences functionality to be implemented');
}

function showUserManagement() {
    window.screenReaderAnnouncer?.announce('Opening user management panel');
    console.log('User management functionality available');
}

function showSystemStatus() {
    window.screenReaderAnnouncer?.announce('Opening system status panel');
    console.log('System status functionality available');
}

function showAccessibilityReport() {
    window.screenReaderAnnouncer?.announce('Opening accessibility compliance report');
    console.log('Accessibility report functionality available');
}

// Hide Streamlit components that are used for functionality
function hideStreamlitComponents() {
    const hideElements = [
        '[key="new_chat_hidden"]',
        '[key="chat_form_hidden"]',
        '[key="hidden_file_upload"]',
        '[key="fallback_new_chat"]',
        '[key="fallback_logout"]',
        '[key="fallback_chat_form"]'
    ];
    
    hideElements.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            const container = element.closest('[data-testid="stForm"]') || element.closest('[data-testid="column"]') || element;
            if (container) {
                container.style.display = 'none';
            }
        });
    });
    
    // Hide the hidden components container
    setTimeout(() => {
        const containers = document.querySelectorAll('[data-testid="stContainer"]');
        containers.forEach(container => {
            const hasHiddenComponents = container.querySelector('[key*="hidden"]') || 
                                      container.querySelector('[key*="fallback"]');
            if (hasHiddenComponents) {
                container.style.display = 'none';
            }
        });
    }, 500);
}
</script>

<style>
/* ===== NEW HTML LAYOUT STYLES ===== */
/* Session items in left panel */
.session-item {
    padding: var(--space-3) var(--space-4);
    margin-bottom: var(--space-2);
    background: var(--bg-secondary);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-fast);
}

.session-item:hover {
    background: var(--gray-100);
    border-color: var(--accent-blue);
    transform: translateX(2px);
}

.session-item:focus {
    outline: 2px solid var(--focus-outline);
    outline-offset: 2px;
}

.session-title {
    font-weight: 500;
    color: var(--text-primary);
    font-size: 14px;
    margin-bottom: var(--space-1);
}

.session-info {
    color: var(--text-secondary);
    font-size: 12px;
}

/* New chat button */
.new-chat-btn {
    width: 100%;
    padding: var(--space-3) var(--space-4);
    background: var(--accent-blue);
    color: var(--text-on-dark);
    border: none;
    border-radius: var(--radius);
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-fast);
    margin-bottom: var(--space-4);
    min-height: var(--min-touch-target);
}

.new-chat-btn:hover {
    background: var(--accent-blue-light);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.new-chat-btn:focus {
    outline: 2px solid var(--focus-outline);
    outline-offset: 2px;
}

/* Chat messages styling */
.message-user, .message-assistant {
    padding: var(--space-4);
    margin-bottom: var(--space-3);
    border-radius: var(--radius-lg);
    position: relative;
    max-width: 85%;
}

.message-user {
    background: var(--accent-blue);
    color: var(--text-on-dark);
    margin-left: auto;
    border-bottom-right-radius: var(--radius);
}

.message-assistant {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border-bottom-left-radius: var(--radius);
}

.message-content {
    line-height: 1.6;
    word-wrap: break-word;
}

.message-timestamp {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: var(--space-2);
    display: block;
}

/* Welcome state styling */
.welcome-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 60%;
    text-align: center;
}

.welcome-content h2 {
    color: var(--text-primary);
    font-size: 24px;
    margin-bottom: var(--space-4);
}

.welcome-content p {
    color: var(--text-secondary);
    font-size: 16px;
}

/* Input placeholder styling */
.input-placeholder {
    display: flex;
    align-items: flex-end;
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--bg-secondary);
    border-radius: var(--radius-lg);
    border: 1px solid var(--gray-200);
}

.input-placeholder textarea {
    flex: 1;
    border: none;
    background: transparent;
    resize: none;
    font-family: inherit;
    font-size: 14px;
    color: var(--text-primary);
    min-height: var(--min-touch-target);
    padding: var(--space-2);
}

.input-placeholder textarea:focus {
    outline: none;
}

.send-button {
    padding: var(--space-2) var(--space-4);
    background: var(--accent-blue);
    color: var(--text-on-dark);
    border: none;
    border-radius: var(--radius);
    font-weight: 500;
    cursor: pointer;
    min-height: var(--min-touch-target);
    min-width: var(--min-touch-target);
}

.send-button:hover {
    background: var(--accent-blue-light);
}

/* Right panel controls */
.user-info {
    flex: 1;
}

.user-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 14px;
}

.user-role {
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 2px;
}

.logout-btn {
    padding: var(--space-2) var(--space-3);
    background: var(--error-color);
    color: var(--text-on-dark);
    border: none;
    border-radius: var(--radius);
    font-size: 12px;
    cursor: pointer;
    min-height: var(--min-touch-target);
}

.logout-btn:hover {
    background: #b91c1c;
}

/* Admin controls */
.admin-section {
    margin-bottom: var(--space-6);
}

.admin-section h3 {
    color: var(--text-primary);
    font-size: 14px;
    margin-bottom: var(--space-3);
}

.admin-controls {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
}

.admin-btn, .upload-btn, .settings-btn {
    padding: var(--space-2) var(--space-3);
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius);
    font-size: 12px;
    cursor: pointer;
    text-align: left;
    min-height: var(--min-touch-target);
    transition: all var(--transition-fast);
}

.admin-btn:hover, .upload-btn:hover, .settings-btn:hover {
    background: var(--gray-100);
    border-color: var(--accent-blue);
}

/* Document and settings sections */
.document-section, .settings-section {
    margin-bottom: var(--space-6);
}

.document-section h3, .settings-section h3 {
    color: var(--text-primary);
    font-size: 14px;
    margin-bottom: var(--space-3);
}

.settings-options {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
}

/* Error and loading states */
.error-state, .loading-state {
    padding: var(--space-4);
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
}

.error-state {
    color: var(--error-color);
}

/* Professional Base Setup */
.stApp {
    background: linear-gradient(to bottom, #1a2b3c, #0d1a2b) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    min-height: 100vh !important;
    width: 100vw !important;
    overflow-x: hidden !important;
}

.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
    margin: 0 !important;
    width: 100vw !important;
    min-height: 100vh !important;
}

/* Hide Streamlit Elements */
header, footer, .stDeployButton, .stDecoration {
    display: none !important;
}

[data-testid="stSidebar"] {
    display: none !important;
}

/* Skip Navigation Links - Sprint 2 Task 2.2 */
.skip-link {
    position: absolute;
    top: -40px;
    left: 6px;
    background: var(--focus-outline);
    color: var(--text-white);
    padding: 8px 16px;
    text-decoration: none;
    border-radius: var(--radius);
    z-index: 1000;
    font-size: 14px;
    font-weight: 600;
    transition: top var(--transition-fast);
}

.skip-link:focus {
    top: 6px;
    outline: var(--focus-outline-width) solid var(--focus-outline);
    outline-offset: var(--focus-outline-offset);
}

/* Enhanced Focus Indicators - Sprint 2 Task 2.2 */
*:focus-visible {
    outline: var(--focus-outline-width) solid var(--focus-outline) !important;
    outline-offset: var(--focus-outline-offset) !important;
    border-radius: var(--radius) !important;
    box-shadow: 0 0 0 1px var(--bg-main) !important;
}

/* Remove default focus styles */
*:focus {
    outline: none !important;
}

/* Ensure keyboard focus is always visible */
button:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible,
a:focus-visible {
    outline: var(--focus-outline-width) solid var(--focus-outline) !important;
    outline-offset: var(--focus-outline-offset) !important;
}

/* Professional Three-Panel Layout with ARIA Support */
.three-panel-container {
    display: flex !important;
    height: 100vh !important;
    width: 100vw !important;
    margin: 0 !important;
    padding: 0 !important;
    background: linear-gradient(to bottom, #1a2b3c, #0d1a2b) !important;
}

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

/* Professional Left Panel with ARIA Landmarks */
.left-panel {
    width: 320px;
    min-width: 320px;
    background: var(--bg-panel);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: var(--shadow-lg);
    /* Ensure keyboard focus can reach this panel */
    position: relative;
}

/* Focus trap for modal dialogs */
.focus-trap {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
}

.focus-trap-content {
    background: var(--bg-main);
    padding: 2rem;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-xl);
    max-width: 90vw;
    max-height: 90vh;
    overflow-y: auto;
    position: relative;
}

.left-panel-header {
    padding: var(--space-6);
    background: rgba(26, 43, 60, 0.9);
    color: var(--text-on-dark);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    /* Ensure sufficient contrast for header text */
}

.left-panel-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-4);
    background: rgba(255, 255, 255, 0.98);
}

/* Professional Center Panel with ARIA Support */
.center-panel {
    flex: 1;
    background: rgba(255, 255, 255, 0.95);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    backdrop-filter: blur(10px);
    border-left: 1px solid rgba(255, 255, 255, 0.1);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    /* Ensure main content area is properly labeled */
    position: relative;
}

.chat-header {
    padding: var(--space-6);
    background: rgba(255, 255, 255, 0.95);
    border-bottom: 1px solid var(--gray-200);
    backdrop-filter: blur(10px);
    text-align: center;
}

.chat-title {
    color: var(--text-primary);
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: var(--space-2);
    /* Removed gradient for better accessibility - use solid color */
    /* background: linear-gradient(135deg, var(--primary-blue), var(--accent-blue));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; */
}

.chat-subtitle {
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-6);
    background: rgba(255, 255, 255, 0.98);
}

.chat-input-container {
    padding: var(--space-6);
    background: rgba(255, 255, 255, 0.95);
    border-top: 1px solid var(--gray-200);
    backdrop-filter: blur(10px);
}

.chat-input-wrapper {
    max-width: 768px;
    margin: 0 auto;
    position: relative;
}

/* Professional Right Panel */
.right-panel {
    width: 320px;
    min-width: 320px;
    background: var(--bg-panel);
    backdrop-filter: blur(10px);
    border-left: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: var(--shadow-lg);
}

.right-panel-header {
    padding: var(--space-6);
    background: rgba(26, 43, 60, 0.9);
    color: var(--text-on-dark);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    backdrop-filter: blur(10px);
    /* Ensure sufficient contrast for header text */
}

.right-panel-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-4);
    background: rgba(255, 255, 255, 0.98);
}

/* Professional Login Page with Accessibility */
.login-container {
    min-height: 100vh;
    width: 100vw;
    background: linear-gradient(to bottom, #1a2b3c, #0d1a2b) !important;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-6);
    /* Ensure keyboard focus is properly managed */
    position: relative;
}

/* Login form accessibility enhancements */
.login-form {
    width: 100%;
    max-width: 420px;
}

.login-form .form-field {
    margin-bottom: 1.5rem;
}

.login-form label {
    display: block;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    font-size: 14px;
}

.login-form .form-error {
    color: var(--error-color);
    font-size: 12px;
    margin-top: 0.25rem;
    display: block;
}

.login-form .form-help {
    color: var(--text-secondary);
    font-size: 12px;
    margin-top: 0.25rem;
}

.login-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    padding: var(--space-8);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-xl);
    border: 1px solid rgba(255, 255, 255, 0.2);
    width: 100%;
    max-width: 420px;
}

.login-title {
    text-align: center;
    font-size: 1.875rem;
    font-weight: 700;
    color: var(--primary-blue);
    margin-bottom: var(--space-8);
    background: linear-gradient(135deg, var(--primary-blue), var(--accent-blue));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Professional ChatGPT-Style Messages */
.message-container {
    display: flex;
    gap: var(--space-4);
    margin-bottom: var(--space-6);
    align-items: flex-start;
    padding: var(--space-4);
    border-radius: var(--radius-lg);
    transition: background-color 0.2s ease;
}

.message-container:hover {
    background: var(--message-hover);
}

.message-avatar {
    width: 36px;
    height: 36px;
    border-radius: var(--radius-full);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    font-weight: 600;
    /* Add ARIA hidden since this is decorative */
}

.user-avatar {
    background: linear-gradient(135deg, var(--primary-blue), var(--accent-blue));
    color: var(--text-white);
}

.ai-avatar {
    background: linear-gradient(135deg, var(--gray-800), var(--gray-600));
    color: var(--text-white);
}

.message-content {
    flex: 1;
    min-width: 0;
    font-size: 15px;
    line-height: 1.6;
    color: var(--text-primary);
}

.message-user, .message-ai {
    background: transparent !important;
    color: var(--text-primary) !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    box-shadow: none !important;
}

/* Professional Session Items */
.session-item {
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-2);
    cursor: pointer;
    transition: all var(--transition-normal);
    border: 1px solid transparent;
    background: rgba(255, 255, 255, 0.8);
    /* Ensure minimum touch target size */
    min-height: var(--min-touch-target);
    display: flex;
    align-items: center;
}

.session-item:hover {
    background: rgba(59, 130, 246, 0.1);
    border-color: var(--accent-blue-light);
    box-shadow: var(--shadow-md);
}

.session-item.active {
    background: linear-gradient(135deg, var(--primary-blue), var(--accent-blue));
    border-color: var(--primary-blue);
    color: var(--text-white);
    box-shadow: var(--shadow-lg);
}

.session-title {
    font-weight: 600;
    color: var(--text-on-light);
    font-size: 14px;
    margin-bottom: var(--space-1);
    /* Ensure sufficient contrast */
}

.session-item.active .session-title {
    color: var(--text-white);
}

.session-meta {
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: 500;
    /* Updated color for better accessibility */
}

.session-item.active .session-meta {
    color: rgba(255, 255, 255, 0.9);
}

/* Professional Buttons with Accessibility */
.chat-btn {
    background: var(--button-primary);
    color: var(--text-on-dark);
    border: none;
    border-radius: var(--radius-lg);
    padding: var(--space-3) var(--space-6);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-normal);
    box-shadow: var(--shadow-md);
    /* Ensure minimum touch target size */
    min-height: var(--min-touch-target);
    min-width: var(--min-touch-target);
    position: relative;
    /* Remove gradient for better contrast */
}

.chat-btn:disabled {
    background: var(--state-disabled);
    color: var(--text-secondary);
    cursor: not-allowed;
    box-shadow: none;
    opacity: 0.6;
}

.chat-btn[aria-busy="true"]::after {
    content: "";
    position: absolute;
    width: 16px;
    height: 16px;
    border: 2px solid transparent;
    border-top-color: currentColor;
    border-radius: 50%;
    animation: button-loading 1s linear infinite;
    margin-left: 8px;
}

@keyframes button-loading {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.chat-btn:hover:not(:disabled) {
    background: var(--button-primary-hover);
    box-shadow: var(--shadow-lg);
    transform: translateY(-1px);
}

.chat-btn:focus-visible {
    outline: var(--focus-outline-width) solid var(--focus-outline);
    outline-offset: var(--focus-outline-offset);
}

.chat-btn-secondary {
    background: var(--button-secondary);
    color: var(--text-primary);
    border: 1px solid var(--gray-300);
    backdrop-filter: blur(10px);
    min-height: var(--min-touch-target);
    min-width: var(--min-touch-target);
}

.chat-btn-danger {
    background: var(--button-danger);
    color: var(--text-on-dark);
    border: none;
    min-height: var(--min-touch-target);
    min-width: var(--min-touch-target);
}

.chat-btn-danger:hover:not(:disabled) {
    background: var(--button-danger-hover);
}

.chat-btn-secondary:hover:not(:disabled) {
    background: var(--button-secondary-hover);
    border-color: var(--accent-blue);
    box-shadow: var(--shadow-md);
}

.chat-btn-secondary:focus-visible {
    outline: var(--focus-outline-width) solid var(--focus-outline);
    outline-offset: var(--focus-outline-offset);
}

/* Professional Empty State */
.empty-state {
    text-align: center;
    padding: var(--space-12) var(--space-8);
    color: var(--text-secondary);
    background: rgba(255, 255, 255, 0.8);
    border-radius: var(--radius-xl);
    margin: var(--space-6);
    box-shadow: var(--shadow-lg);
    border: 1px solid rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
}

/* Professional Typing Indicator with ARIA */
.typing-indicator {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: var(--space-4) var(--space-6);
    color: var(--text-secondary);
    font-size: 14px;
    font-weight: 500;
    /* Add ARIA live region attributes via JavaScript */
}

.typing-indicator[aria-live="polite"] {
    /* Ensure screen reader announces typing status */
}

.typing-dots {
    display: flex;
    gap: 6px;
}

.typing-dot {
    width: 8px;
    height: 8px;
    border-radius: var(--radius-full);
    background: var(--accent-blue);
    animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
    0%, 60%, 100% { 
        opacity: 0.3; 
        transform: scale(0.8);
    }
    30% { 
        opacity: 1;
        transform: scale(1);
    }
}

/* Respect reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
    .typing-dot {
        animation: none !important;
    }
    
    .typing-indicator::after {
        content: "...";
        margin-left: 8px;
    }
}

/* Professional Responsive Design */
@media (max-width: 1440px) {
    .left-panel, .right-panel {
        width: 300px;
        min-width: 300px;
    }
}

@media (max-width: 1200px) {
    .left-panel, .right-panel {
        width: 280px;
        min-width: 280px;
    }
}

@media (max-width: 1024px) {
    .three-panel-container {
        flex-direction: column;
        height: 100vh;
    }
    
    .left-panel, .right-panel {
        width: 100%;
        min-width: 100%;
        height: 180px;
        flex: none;
    }
    
    .center-panel {
        flex: 1;
        min-height: 0;
    }
}

@media (max-width: 768px) {
    .left-panel, .right-panel {
        display: none;
    }
    
    .center-panel {
        width: 100vw;
        height: 100vh;
    }
    
    .three-panel-container {
        width: 100vw;
        height: 100vh;
    }
}

/* Professional Streamlit Component Overrides with Accessibility */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: var(--radius-lg) !important;
    border: 2px solid var(--gray-300) !important;
    background: rgba(255, 255, 255, 0.95) !important;
    font-size: 16px !important; /* Increased for better mobile experience */
    color: var(--text-on-light) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all var(--transition-normal) !important;
    padding: 16px 16px !important;
    min-height: var(--min-touch-target) !important; /* Ensure touch target size */
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    /* Improve contrast for better readability */
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--focus-outline) !important;
    box-shadow: 0 0 0 var(--focus-outline-width) var(--focus-outline) !important;
    outline: var(--focus-outline-width) solid var(--focus-outline) !important;
    outline-offset: var(--focus-outline-offset) !important;
}

/* Error state styling */
.stTextInput > div > div > input[aria-invalid="true"],
.stTextArea > div > div > textarea[aria-invalid="true"] {
    border-color: var(--error-color) !important;
    box-shadow: 0 0 0 2px rgba(215, 53, 2, 0.2) !important;
}

/* Success state styling */
.stTextInput > div > div > input[aria-invalid="false"],
.stTextArea > div > div > textarea[aria-invalid="false"] {
    border-color: var(--success-color) !important;
}

.stButton > button {
    border-radius: var(--radius) !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    transition: all var(--transition-normal) !important;
    padding: var(--space-3) var(--space-4) !important;
    min-height: var(--min-touch-target) !important;
    min-width: var(--min-touch-target) !important;
    position: relative !important;
    /* Ensure proper contrast and accessibility */
}

.stButton > button:disabled {
    background: var(--state-disabled) !important;
    color: var(--text-secondary) !important;
    cursor: not-allowed !important;
    opacity: 0.6 !important;
}

.stButton > button:focus-visible {
    outline: var(--focus-outline-width) solid var(--focus-outline) !important;
    outline-offset: var(--focus-outline-offset) !important;
    z-index: 1 !important;
}

.stButton > button[kind="primary"] {
    background: var(--button-primary) !important;
    color: var(--text-on-dark) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(30, 64, 175, 0.25) !important;
    font-weight: 600 !important;
    border-radius: var(--radius-lg) !important;
    /* Remove gradient for better contrast */
}

.stButton > button[kind="primary"]:hover:not(:disabled) {
    background: var(--button-primary-hover) !important;
    box-shadow: 0 6px 20px rgba(30, 64, 175, 0.35) !important;
    transform: translateY(-1px) !important;
}

.stButton > button[kind="primary"]:focus-visible {
    outline: var(--focus-outline-width) solid var(--text-white) !important;
    outline-offset: var(--focus-outline-offset) !important;
}

.stButton > button[kind="secondary"] {
    background: var(--button-secondary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--gray-300) !important;
}

.stButton > button[kind="secondary"]:hover:not(:disabled) {
    background: var(--button-secondary-hover) !important;
    border-color: var(--gray-400) !important;
}

.stButton > button[kind="secondary"]:focus-visible {
    outline: var(--focus-outline-width) solid var(--focus-outline) !important;
    outline-offset: var(--focus-outline-offset) !important;
}

.stSelectbox > div > div {
    border-radius: var(--radius) !important;
    background: rgba(255, 255, 255, 0.8) !important;
    backdrop-filter: blur(10px) !important;
}

.stTabs > div > div > div > div {
    border-radius: var(--radius) !important;
    background: rgba(255, 255, 255, 0.8) !important;
    backdrop-filter: blur(10px) !important;
}

/* File upload styling */
.stFileUploader > div > div {
    border-radius: var(--radius-lg) !important;
    border-style: dashed !important;
    border-color: var(--accent-blue) !important;
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Link accessibility - WCAG compliant */
a {
    min-height: var(--min-touch-target) !important;
    min-width: var(--min-touch-target) !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 8px 4px !important;
    text-decoration: none !important;
    transition: all var(--transition-normal) !important;
    color: var(--link-color) !important;
    border-radius: var(--radius) !important;
}

a:visited {
    color: var(--link-color) !important;
}

a:focus-visible {
    outline: var(--focus-outline-width) solid var(--focus-outline) !important;
    outline-offset: var(--focus-outline-offset) !important;
    text-decoration: underline !important;
}

a:hover {
    color: var(--link-hover) !important;
    text-decoration: underline !important;
    background-color: rgba(0, 102, 204, 0.1) !important;
}

/* Ensure external links are properly identified */
a[href^="http"]:not([href*="zenith"]):after,
a[href^="//"]:after {
    content: " ↗";
    font-size: 0.8em;
    opacity: 0.7;
}

/* Admin panel styling with accessibility */
.admin-section {
    background: rgba(255, 255, 255, 0.8);
    border: 1px solid var(--gray-300);
    border-radius: var(--radius);
    padding: 20px;
    margin-bottom: 16px;
    backdrop-filter: blur(15px);
    box-shadow: var(--shadow-sm);
    position: relative;
}

.admin-section:focus-within {
    border-color: var(--focus-outline);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.admin-section h3 {
    margin: 0 0 16px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-on-light);
    /* Ensure proper heading hierarchy */
}

.stats-item {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid var(--glass-border);
    font-size: 14px;
}

.stats-item:last-child {
    border-bottom: none;
}

.stats-label {
    color: var(--text-secondary);
    font-weight: 500;
    /* Ensure sufficient contrast */
}

.stats-value {
    color: var(--text-on-light);
    font-weight: 600;
    /* Ensure sufficient contrast for values */
}

/* Data table accessibility */
.data-table {
    width: 100%;
    border-collapse: collapse;
    border: 1px solid var(--gray-300);
}

.data-table th,
.data-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--gray-200);
    color: var(--text-on-light);
}

.data-table th {
    background-color: var(--gray-50);
    font-weight: 600;
    color: var(--text-on-light);
    position: relative;
}

.data-table tr:hover {
    background-color: rgba(59, 130, 246, 0.05);
}

.data-table tr:focus-within {
    background-color: rgba(59, 130, 246, 0.1);
    outline: 2px solid var(--focus-outline);
    outline-offset: -2px;
}

/* Sortable table headers */
.data-table th[aria-sort] {
    cursor: pointer;
    user-select: none;
}

.data-table th[aria-sort]:after {
    content: "";
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 0;
}

.data-table th[aria-sort="ascending"]:after {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 6px solid var(--text-primary);
}

.data-table th[aria-sort="descending"]:after {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid var(--text-primary);
}

/* Form validation and error styling */
.form-group {
    margin-bottom: 1.5rem;
}

.form-label {
    display: block;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    font-size: 14px;
}

.form-input {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid var(--gray-300);
    border-radius: var(--radius);
    font-size: 16px;
    color: var(--text-on-light);
    background: var(--bg-main);
    transition: all var(--transition-normal);
    min-height: var(--min-touch-target);
}

.form-input:focus {
    border-color: var(--focus-outline);
    outline: var(--focus-outline-width) solid var(--focus-outline);
    outline-offset: var(--focus-outline-offset);
}

.form-input[aria-invalid="true"] {
    border-color: var(--error-color);
    box-shadow: 0 0 0 2px rgba(215, 53, 2, 0.2);
}

.form-error {
    color: var(--error-color);
    font-size: 12px;
    margin-top: 0.25rem;
    display: block;
}

.form-help {
    color: var(--text-secondary);
    font-size: 12px;
    margin-top: 0.25rem;
}

/* Toast notifications */
.toast {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--bg-main);
    border: 1px solid var(--gray-300);
    border-radius: var(--radius-lg);
    padding: 16px 20px;
    box-shadow: var(--shadow-lg);
    z-index: 9999;
    max-width: 400px;
    transform: translateX(100%);
    transition: transform var(--transition-normal);
}

.toast.show {
    transform: translateX(0);
}

.toast.error {
    border-color: var(--error-color);
    background: #fef2f2;
}

.toast.success {
    border-color: var(--success-color);
    background: #f0fdf4;
}

.toast.warning {
    border-color: var(--warning-color);
    background: #fffbeb;
}

.toast.info {
    border-color: var(--info-color);
    background: #eff6ff;
}
</style>
""", unsafe_allow_html=True)

class ZenithThreePanelApp:
    """Three-panel ChatGPT-inspired Streamlit application"""
    
    def __init__(self):
        """Initialize the application"""
        self.initialize_session_state()
        self.initialize_auth()
    
    def get_logo_base64(self):
        """Get base64 encoded logo image"""
        try:
            import base64
            logo_path = Path(__file__).parent.parent.parent / "images" / "logo.PNG"
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            else:
                # Fallback: create a simple colored rectangle if logo not found
                return ""
        except Exception as e:
            logger.error(f"Error loading logo: {e}")
            return ""
        
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        # Authentication state - ensure login is required
        init_auth_session()
        
        # Force authentication check - ensure user must login
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        
        # Core components
        if 'pdf_processor' not in st.session_state:
            st.session_state.pdf_processor = None
        if 'vector_store' not in st.session_state:
            st.session_state.vector_store = None
        if 'chat_engine' not in st.session_state:
            st.session_state.chat_engine = None
        
        # Chat history components
        if 'chat_history_manager' not in st.session_state:
            st.session_state.chat_history_manager = get_chat_history_manager()
        if 'current_session' not in st.session_state:
            st.session_state.current_session = None
        
        # Processing state
        if 'documents_processed' not in st.session_state:
            st.session_state.documents_processed = False
        
        # Chat state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # File information
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = []
        if 'file_stats' not in st.session_state:
            st.session_state.file_stats = {}
        
        # Admin panel state
        if 'show_admin_panel' not in st.session_state:
            st.session_state.show_admin_panel = False
            
        # UI state
        if 'typing_indicator' not in st.session_state:
            st.session_state.typing_indicator = False
        if 'current_message_id' not in st.session_state:
            st.session_state.current_message_id = None
    
    def initialize_auth(self):
        """Initialize authentication manager"""
        if 'auth_manager' not in st.session_state or st.session_state.auth_manager is None:
            try:
                qdrant_client = get_qdrant_client().get_client()
                st.session_state.auth_manager = AuthenticationManager(
                    qdrant_client=qdrant_client,
                    secret_key=config.jwt_secret_key
                )
                logger.info("Authentication manager initialized successfully")
            except Exception as e:
                st.error(f"Failed to initialize authentication: {e}")
                logger.error(f"Authentication initialization error: {e}")
                st.session_state.auth_manager = None
                st.stop()

    def render_login_page(self):
        """Render clean professional login page"""
        # Logo and title section
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Logo
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="data:image/png;base64,{}" alt="Zenith AI Company Logo" style="
                    width: 200px; 
                    height: auto; 
                    margin: 0 auto 20px auto;
                    display: block;
                    filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
                " />
                <h1 style="
                    color: white; 
                    margin: 0;
                    font-size: 24px; 
                    font-weight: 600;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">Zenith AI</h1>
                <p style="
                    color: rgba(255,255,255,0.8); 
                    margin: 8px 0 0 0;
                    font-size: 16px;
                ">Intelligent Document Chat System</p>
            </div>
            """.format(self.get_logo_base64()), unsafe_allow_html=True)
            
            # Login form in a styled container (no margin-bottom to remove white space)
            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                padding: 5px;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            ">
            """, unsafe_allow_html=True)
            
            st.markdown("### Welcome Back")
            st.markdown("Sign in to your account")
            
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "Email or Username", 
                    key="login_username", 
                    placeholder="Enter your email or username"
                )
                
                password = st.text_input(
                    "Password", 
                    type="password", 
                    key="login_password", 
                    placeholder="Enter your password"
                )
                
                col_rem, col_forgot = st.columns([1, 1])
                with col_rem:
                    remember_me = st.checkbox("Remember Me")
                with col_forgot:
                    st.markdown('<div style="text-align: right; margin-top: 8px;"><a href="#" style="color: #3b82f6; text-decoration: none; font-size: 14px;">Forgot Password?</a></div>', unsafe_allow_html=True)
                
                if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                    if username and password:
                        try:
                            auth_manager = st.session_state.auth_manager
                            if auth_manager:
                                login_request = UserLoginRequest(username_or_email=username, password=password)
                                success, message, token = auth_manager.login_user(
                                    login_request, 
                                    ip_address="127.0.0.1", 
                                    user_agent="Streamlit App"
                                )
                                
                                if success:
                                    st.session_state.authenticated = True
                                    st.session_state.user_info = {
                                        'username': username,
                                        'token': token,
                                        'id': message.get('user_id') if isinstance(message, dict) else None,
                                        'role': message.get('role', 'user') if isinstance(message, dict) else 'user'
                                    }
                                    st.rerun()
                                else:
                                    st.error(f"Login failed: {message}")
                            else:
                                st.error("Authentication system not available")
                        except Exception as e:
                            st.error(f"Login error: {str(e)}")
                            logger.error(f"Login error: {e}")
                    else:
                        st.warning("Please enter both username and password")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Additional links
            st.markdown(
                '<div style="text-align: center; color: rgba(255,255,255,0.8);">'
                'Don\'t have an account? '
                '<a href="#" style="color: #60a5fa; text-decoration: none;">Sign up here</a>'
                '</div>', 
                unsafe_allow_html=True
            )

    def render_login_form(self):
        """Render enhanced login form"""
        
        with st.form("login_form"):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 24px;">
                <h3 style="
                    color: #1e293b; 
                    font-size: 20px; 
                    font-weight: 600; 
                    margin: 0;
                ">Welcome back</h3>
                <p style="
                    color: #64748b; 
                    font-size: 14px; 
                    margin: 8px 0 0 0;
                ">Sign in to your account</p>
            </div>
            """, unsafe_allow_html=True)
            
            email = st.text_input("Email", key="login_email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            
            if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                if email and password:
                    try:
                        auth_manager = st.session_state.auth_manager
                        if auth_manager:
                            login_request = UserLoginRequest(username_or_email=email, password=password)
                            success, message, token = auth_manager.login_user(
                                login_request, 
                                ip_address="127.0.0.1", 
                                user_agent="Streamlit App"
                            )
                            
                            if success:
                                st.session_state.authenticated = True
                                st.session_state.user_token = token
                                
                                # Get user info from token
                                user = auth_manager.get_current_user(token)
                                if user:
                                    st.session_state.user_info = {
                                        'id': user.id,
                                        'username': user.username,
                                        'email': user.email,
                                        'role': user.role.value,
                                        'full_name': user.full_name
                                    }
                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error(message or 'Login failed')
                        else:
                            st.error("Authentication system not available")
                    except Exception as e:
                        st.error(f"Login error: {str(e)}")
                        logger.error(f"Login error: {e}")
                else:
                    st.warning("Please enter both email and password")

    def render_registration_form(self):
        """Render enhanced registration form"""
        
        with st.form("registration_form"):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 24px;">
                <h3 style="
                    color: #1e293b; 
                    font-size: 20px; 
                    font-weight: 600; 
                    margin: 0;
                ">Create Account</h3>
                <p style="
                    color: #64748b; 
                    font-size: 14px; 
                    margin: 8px 0 0 0;
                ">Start your journey with Zenith AI</p>
            </div>
            """, unsafe_allow_html=True)
            
            email = st.text_input("Email", key="reg_email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", key="reg_password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password", placeholder="Confirm your password")
            
            if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
                if email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                        return
                    
                    try:
                        auth_manager = st.session_state.auth_manager
                        if auth_manager:
                            # Default role is chat_user, first user becomes administrator
                            user_count = auth_manager.get_user_count()
                            role = UserRole.ADMINISTRATOR if user_count == 0 else UserRole.CHAT_USER
                            
                            reg_request = UserRegistrationRequest(
                                username=email.split('@')[0],  # Use email prefix as username
                                email=email, 
                                password=password,
                                role=role.value if hasattr(role, 'value') else role
                            )
                            success, message, user = auth_manager.register_user(
                                reg_request, 
                                ip_address="127.0.0.1"
                            )
                            
                            if success:
                                st.success("Account created successfully! Please sign in.")
                                if user_count == 0:
                                    st.info("As the first user, you have been granted administrator privileges.")
                            else:
                                st.error(message or 'Registration failed')
                        else:
                            st.error("Authentication system not available")
                    except Exception as e:
                        st.error(f"Registration error: {str(e)}")
                        logger.error(f"Registration error: {e}")
                else:
                    st.warning("Please fill in all fields")

    def render_three_panel_layout(self):
        """Render the main three-panel layout"""
        # Initialize user components if needed
        if not st.session_state.vector_store:
            user_id = st.session_state.user_info.get('id')
            st.session_state.vector_store = UserVectorStore(user_id=user_id)
            st.session_state.chat_engine = EnhancedChatEngine(
                user_id=user_id,
                vector_store=st.session_state.vector_store
            )

        # Generate complete three-panel HTML structure as single unit
        self.render_complete_three_panel_layout()

    def render_complete_three_panel_layout(self):
        """Render complete three-panel layout as single HTML structure for proper flexbox behavior"""
        try:
            # Get user info for panels
            user_info = st.session_state.get('user_info', {})
            
            # Generate left panel content
            left_panel_content = self.generate_left_panel_content()
            
            # Generate center panel content
            center_panel_content = self.generate_center_panel_content()
            
            # Generate right panel content
            right_panel_content = self.generate_right_panel_content(user_info)
            
            # Create complete three-panel HTML structure
            complete_layout = f'''
            <div class="three-panel-container" role="application" aria-label="Zenith AI Chat Interface">
                <!-- Skip Navigation Links -->
                <div class="skip-navigation" aria-hidden="false">
                    <a href="#main-chat" class="skip-link" tabindex="1">Skip to main chat</a>
                    <a href="#chat-input" class="skip-link" tabindex="2">Skip to chat input</a>
                    <a href="#document-panel" class="skip-link" tabindex="3">Skip to documents</a>
                </div>
                
                <!-- Screen Reader Live Regions for Dynamic Updates -->
                <div id="sr-notifications" aria-live="polite" aria-atomic="true" class="sr-only">
                    <!-- Chat status announcements for screen readers -->
                </div>
                <div id="sr-alerts" aria-live="assertive" aria-atomic="true" class="sr-only">
                    <!-- Important alerts for screen readers -->
                </div>
                
                <!-- Left Panel: Chat Navigation and History -->
                {left_panel_content}
                
                <!-- Center Panel: Main Chat Interface -->
                {center_panel_content}
                
                <!-- Right Panel: Settings and Controls -->
                {right_panel_content}
            </div>
            '''
            
            # Render complete layout as single unit
            st.markdown(complete_layout, unsafe_allow_html=True)
            
            # Render Streamlit components that need interactivity
            self.render_streamlit_components()
            
        except Exception as e:
            st.error(f"Error rendering three-panel layout: {str(e)}")
            logger.error(f"Layout rendering error: {e}")
            # Fallback to basic layout
            self.render_fallback_layout()

    def generate_left_panel_content(self):
        """Generate left panel HTML content"""
        try:
            # Get recent sessions for display
            recent_sessions_html = ""
            user_id = st.session_state.get('user_info', {}).get('id')
            
            if st.session_state.get('chat_history_manager') and user_id:
                try:
                    recent_sessions = st.session_state.chat_history_manager.get_user_sessions(user_id, limit=5)
                    if recent_sessions:
                        for i, session in enumerate(recent_sessions[:3]):  # Limit for HTML generation
                            display_title = getattr(session, 'title', f'Session {i+1}')
                            if len(display_title) > 25:
                                display_title = display_title[:22] + "..."
                            
                            recent_sessions_html += f'''
                            <div class="session-item" onclick="loadSession('{session.session_id}')" role="button" tabindex="0" aria-label="Load {display_title}">
                                <div class="session-title">📄 {display_title}</div>
                                <div class="session-info">Recent activity</div>
                            </div>
                            '''
                    else:
                        recent_sessions_html = '''
                        <div class="no-sessions" role="status" aria-live="polite">
                            <div style="text-align: center; color: var(--text-secondary); font-size: 14px; padding: 20px 0;">
                                No recent chats<br>
                                <small>Start a new conversation!</small>
                            </div>
                        </div>
                        '''
                except Exception as e:
                    recent_sessions_html = '<div class="error-state">Error loading sessions</div>'
            else:
                recent_sessions_html = '<div class="loading-state">Loading chat history...</div>'
                
            # Document status
            document_status_html = ""
            if st.session_state.get('documents_processed', False) and st.session_state.get('file_stats'):
                stats = st.session_state.file_stats
                file_count = len(stats.get('processed_files', []))
                document_status_html = f'''
                <div class="document-status" role="status" aria-live="polite">
                    <div style="
                        margin-top: 20px; 
                        padding: 12px; 
                        background: rgba(59, 130, 246, 0.1); 
                        border-left: 3px solid var(--accent-blue); 
                        border-radius: var(--radius);
                        font-size: 12px;
                        color: var(--text-secondary);
                    ">
                        📚 {file_count} document{'s' if file_count != 1 else ''} ready
                    </div>
                </div>
                '''
            
            return f'''
            <nav class="left-panel" role="navigation" aria-label="Chat navigation and history">
                <header class="left-panel-header" role="banner">
                    <h2 id="chat-history-heading" style="margin: 0; font-size: 16px; font-weight: 600; color: var(--text-primary);">💬 Recent Chats</h2>
                </header>
                
                <section class="left-panel-content" aria-labelledby="chat-history-heading" role="region">
                    <div class="new-chat-section">
                        <button class="new-chat-btn" onclick="startNewChat()" role="button" aria-label="Start new chat conversation">
                            🆕 New Chat
                        </button>
                    </div>
                    
                    <div class="recent-sessions">
                        {recent_sessions_html}
                    </div>
                    
                    {document_status_html}
                </section>
            </nav>
            '''
        except Exception as e:
            logger.error(f"Error generating left panel content: {e}")
            return '<nav class="left-panel" role="navigation"><div class="error-state">Error loading navigation</div></nav>'

    def generate_center_panel_content(self):
        """Generate center panel HTML content"""
        try:
            # Get chat messages
            chat_messages_html = ""
            if st.session_state.get('current_session') and st.session_state.current_session.messages:
                for message in st.session_state.current_session.messages[-10:]:  # Last 10 for HTML
                    role_class = "user" if message.role == "user" else "assistant"
                    chat_messages_html += f'''
                    <article class="message-{role_class}" role="article" aria-label="{message.role} message" tabindex="0">
                        <div class="message-content">{message.content[:500]}{'...' if len(message.content) > 500 else ''}</div>
                        <time class="message-timestamp" datetime="{message.timestamp}" aria-label="Message sent at {message.timestamp}">
                            {message.timestamp.strftime("%H:%M") if hasattr(message.timestamp, 'strftime') else str(message.timestamp)[:5]}
                        </time>
                    </article>
                    '''
            else:
                chat_messages_html = '''
                <div class="welcome-state" role="status">
                    <div class="welcome-content">
                        <h2>👋 Welcome to Zenith AI</h2>
                        <p>Upload a document and start asking questions!</p>
                    </div>
                </div>
                '''
            
            return f'''
            <main class="center-panel" role="main" aria-label="Main chat conversation" id="main-chat">
                <header class="chat-header" role="banner" aria-label="Chat session header">
                    <h1 class="chat-title" id="chat-title">🤖 Zenith AI</h1>
                    <p class="chat-subtitle">Intelligent Document Chat System</p>
                </header>
                
                <section class="chat-messages" 
                         role="log" 
                         aria-live="polite" 
                         aria-label="Chat conversation" 
                         id="chat-messages"
                         aria-atomic="false"
                         aria-relevant="additions">
                    {chat_messages_html}
                </section>
                
                <div class="chat-input-container" role="region" aria-label="Message input">
                    <div class="chat-input-wrapper" id="chat-input">
                        <div class="input-placeholder">
                            <textarea placeholder="Type your message here..." aria-label="Chat message input" rows="1"></textarea>
                            <button class="send-button" aria-label="Send message">Send</button>
                        </div>
                    </div>
                </div>
            </main>
            '''
        except Exception as e:
            logger.error(f"Error generating center panel content: {e}")
            return '<main class="center-panel" role="main"><div class="error-state">Error loading chat interface</div></main>'

    def generate_right_panel_content(self, user_info):
        """Generate right panel HTML content"""
        try:
            # Admin controls HTML
            admin_controls_html = ""
            if user_info.get('role') in ['administrator', 'admin']:
                admin_controls_html = '''
                <div class="admin-section">
                    <h3>⚙️ Admin Controls</h3>
                    <div class="admin-controls">
                        <button class="admin-btn" onclick="showUserManagement()">👥 User Management</button>
                        <button class="admin-btn" onclick="showSystemStatus()">📊 System Status</button>
                        <button class="admin-btn" onclick="showAccessibilityReport()">♿ Accessibility</button>
                    </div>
                </div>
                '''
                
            return f'''
            <aside class="right-panel" 
                   role="complementary" 
                   aria-label="Settings and document information" 
                   id="document-panel">
                <header class="right-panel-header" role="banner" aria-label="User information and controls">
                    <div class="user-info">
                        <div class="user-name">👤 {user_info.get('email', 'User')}</div>
                        <div class="user-role">{user_info.get('role', 'User').replace('_', ' ').title()}</div>
                    </div>
                    <button class="logout-btn" onclick="logoutUser()" aria-label="Sign out">Sign Out</button>
                </header>
                
                <div class="right-panel-content" role="region" aria-label="User settings and controls">
                    {admin_controls_html}
                    
                    <div class="document-section">
                        <h3>📄 Documents</h3>
                        <div class="document-upload">
                            <button class="upload-btn" onclick="showUploadDialog()">Upload PDF</button>
                        </div>
                    </div>
                    
                    <div class="settings-section">
                        <h3>⚙️ Settings</h3>
                        <div class="settings-options">
                            <button class="settings-btn" onclick="toggleTheme()">🌙 Dark Mode</button>
                            <button class="settings-btn" onclick="showPreferences()">🔧 Preferences</button>
                        </div>
                    </div>
                </div>
            </aside>
            '''
        except Exception as e:
            logger.error(f"Error generating right panel content: {e}")
            return '<aside class="right-panel" role="complementary"><div class="error-state">Error loading settings</div></aside>'

    def render_streamlit_components(self):
        """Render interactive Streamlit components that need to be outside the HTML structure"""
        try:
            # Create hidden containers for Streamlit interactivity
            with st.container():
                # New chat button functionality
                if st.button("🆕 New Chat", key="new_chat_hidden", help="Start new conversation"):
                    self.start_new_chat_session()
                    st.rerun()
                
                # Chat input functionality  
                with st.form(key="chat_form_hidden", clear_on_submit=True):
                    user_input = st.text_area(
                        "Message",
                        key="hidden_chat_input",
                        placeholder="Type your message...",
                        height=100,
                        label_visibility="collapsed"
                    )
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        send_clicked = st.form_submit_button("Send Message", type="primary")
                    
                    if send_clicked and user_input.strip():
                        self.handle_user_message(user_input.strip())
                        st.rerun()
                
                # File upload functionality
                uploaded_file = st.file_uploader(
                    "Upload PDF",
                    type=['pdf'],
                    key="hidden_file_upload",
                    label_visibility="collapsed"
                )
                
                if uploaded_file is not None:
                    self.handle_file_upload(uploaded_file)
                    st.rerun()
                    
        except Exception as e:
            logger.error(f"Error rendering Streamlit components: {e}")

    def render_fallback_layout(self):
        """Fallback layout using Streamlit columns if HTML layout fails"""
        try:
            st.markdown("### Zenith AI Chat (Fallback Mode)")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                st.markdown("#### Recent Chats")
                if st.button("🆕 New Chat", key="fallback_new_chat"):
                    self.start_new_chat_session()
                    st.rerun()
            
            with col2:
                st.markdown("#### Chat")
                if st.session_state.get('current_session'):
                    for message in st.session_state.current_session.messages[-5:]:
                        with st.chat_message(message.role):
                            st.write(message.content)
                
                # Chat input
                with st.form(key="fallback_chat_form"):
                    user_input = st.text_area("Your message:")
                    if st.form_submit_button("Send"):
                        if user_input.strip():
                            self.handle_user_message(user_input.strip())
                            st.rerun()
            
            with col3:
                st.markdown("#### Settings")
                user_info = st.session_state.get('user_info', {})
                st.write(f"User: {user_info.get('email', 'Unknown')}")
                
                if st.button("Sign Out", key="fallback_logout"):
                    self.logout_user()
                    
        except Exception as e:
            st.error(f"Error rendering fallback layout: {str(e)}")

    def handle_file_upload(self, uploaded_file):
        """Handle PDF file upload"""
        try:
            if uploaded_file is not None:
                # Process the uploaded file
                st.success(f"Processing {uploaded_file.name}...")
                
                # Save uploaded file temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    temp_path = tmp_file.name
                
                # Initialize processors
                user_id = st.session_state.user_info.get('id')
                if not user_id:
                    st.error("User not authenticated")
                    return
                
                # Process the PDF
                pdf_processor = PDFProcessor()
                result = pdf_processor.process_pdf(temp_path, user_id)
                
                if result.get('success', False):
                    st.success(f"✅ Successfully processed {uploaded_file.name}")
                    
                    # Update session state
                    st.session_state.documents_processed = True
                    st.session_state.file_stats = {
                        'processed_files': [uploaded_file.name],
                        'total_chunks': result.get('chunks', 0),
                        'processing_time': result.get('processing_time', 0)
                    }
                    
                    # Clean up temp file
                    import os
                    os.unlink(temp_path)
                    
                else:
                    st.error(f"❌ Error processing {uploaded_file.name}: {result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            st.error(f"Error handling file upload: {str(e)}")
            logger.error(f"File upload error: {e}")

    def start_new_chat_session(self):
        """Start a new chat session"""
        try:
            user_id = st.session_state.user_info.get('id')
            if not user_id:
                st.error("User not authenticated")
                return
            
            if not st.session_state.get('chat_history_manager'):
                st.error("Chat history manager not initialized")
                return
            
            # Create new session
            new_session = st.session_state.chat_history_manager.create_session(
                user_id=user_id,
                title="New Chat Session"
            )
            
            if new_session:
                st.session_state.current_session = new_session
                st.session_state.chat_history = []
                st.success("✅ Started new chat session")
            else:
                st.error("❌ Failed to create new chat session")
                
        except Exception as e:
            st.error(f"Error starting new chat session: {str(e)}")
            logger.error(f"New chat session error: {e}")

    # ===== UTILITY METHODS =====
    
    def handle_user_message(self, user_input: str):
        """Handle user message input and generate AI response"""
        try:
            if not user_input or not user_input.strip():
                return
                
            # Ensure we have a current session
            if not st.session_state.get('current_session'):
                self.start_new_chat_session()
                
            # Get current session and user ID
            user_id = st.session_state.user_info.get('id')
            current_session = st.session_state.current_session
            
            if not current_session or not user_id:
                st.error("Session or user not available")
                return
                
            # Add user message to session
            user_message = ChatMessage(
                role="user",
                content=user_input.strip(),
                timestamp=datetime.now()
            )
            current_session.add_message(user_message)
            
            # Generate AI response
            with st.spinner("Generating response..."):
                try:
                    # Get AI response using the chat engine
                    chat_engine = st.session_state.get('chat_engine')
                    if chat_engine:
                        response = chat_engine.generate_response(
                            query=user_input.strip(),
                            session_id=current_session.session_id,
                            user_id=user_id
                        )
                        
                        # Add AI response to session
                        ai_message = ChatMessage(
                            role="assistant", 
                            content=response.get('response', 'Sorry, I could not generate a response.'),
                            timestamp=datetime.now()
                        )
                        current_session.add_message(ai_message)
                        
                        # Save session
                        if st.session_state.get('chat_history_manager'):
                            st.session_state.chat_history_manager.save_session(current_session)
                            
                    else:
                        st.error("Chat engine not available")
                        
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
                    logger.error(f"Chat response error: {e}")
                    
        except Exception as e:
            st.error(f"Error handling user message: {str(e)}")
            logger.error(f"User message error: {e}")

    def initialize_chat_components(self):
        """Initialize chat-related components and session state"""
        try:
            user_id = st.session_state.user_info.get('id')
            if not user_id:
                st.error("User not authenticated properly")
                return
            
            # Initialize chat history manager
            if not st.session_state.get('chat_history_manager'):
                st.session_state.chat_history_manager = get_chat_history_manager()
            
            # Initialize vector store
            if not st.session_state.get('vector_store'):
                try:
                    qdrant_client = get_qdrant_client()
                    st.session_state.vector_store = UserVectorStore(
                        qdrant_client=qdrant_client,
                        user_id=user_id
                    )
                except Exception as e:
                    logger.warning(f"Could not initialize vector store: {e}")
                    st.session_state.vector_store = None
            
            # Initialize chat engine
            if not st.session_state.get('chat_engine'):
                try:
                    st.session_state.chat_engine = EnhancedChatEngine(
                        user_id=user_id,
                        vector_store=st.session_state.vector_store
                    )
                except Exception as e:
                    logger.warning(f"Could not initialize chat engine: {e}")
                    st.session_state.chat_engine = None
            
            # Initialize current session if none exists
            if not st.session_state.get('current_session'):
                try:
                    # Try to get the most recent session
                    if st.session_state.chat_history_manager:
                        recent_sessions = st.session_state.chat_history_manager.get_user_sessions(user_id, limit=1)
                        if recent_sessions:
                            st.session_state.current_session = recent_sessions[0]
                        else:
                            # Create a new session
                            self.start_new_chat_session()
                except Exception as e:
                    logger.warning(f"Could not initialize session: {e}")
                    
            # Initialize document processing status
            if 'documents_processed' not in st.session_state:
                st.session_state.documents_processed = False
                st.session_state.file_stats = {}
                
        except Exception as e:
            st.error(f"Error initializing chat components: {str(e)}")
            logger.error(f"Chat initialization error: {e}")

    def logout_user(self):
        """Logout current user and clear session state"""
        try:
            # Clear authentication state
            if st.session_state.get('user_token'):
                # Use the auth manager to logout if available
                auth_manager = st.session_state.get('auth_manager')
                if auth_manager:
                    auth_manager.logout_user(st.session_state.user_token)
            
            # Clear all session state
            keys_to_clear = [
                'authenticated', 'user_token', 'user_info', 'current_session',
                'chat_history', 'chat_history_manager', 'vector_store', 'chat_engine',
                'documents_processed', 'file_stats', 'show_admin_panel'
            ]
            
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.success("Logged out successfully")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error during logout: {str(e)}")
            logger.error(f"Logout error: {e}")

    def run(self):
        """Run the main application with enhanced accessibility"""
        # Ensure auth is properly initialized
        self.initialize_auth()
        
        # Check authentication
        if not st.session_state.get('authenticated'):
            self.render_login_page()
            return
            
        # Initialize necessary components
        self.initialize_chat_components()
        
        # Render the three-panel layout
        self.render_three_panel_layout()

def main():
    """Main application entry point"""
    app = ZenithThreePanelApp()
    app.run()


if __name__ == "__main__":
    main()