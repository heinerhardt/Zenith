"""
Fix for Force Reinitialize infinite loop issue in Zenith app
This script provides the corrected code for the Force Reinitialize button
"""

def fixed_force_reinitialize_button():
    """
    Fixed implementation of the Force Reinitialize button
    Replace the existing button code with this version
    """
    
    # Add proper state management to prevent infinite reinitialization
    reinit_key = "force_reinit_in_progress"
    
    # Only show button if not currently processing
    if not st.session_state.get(reinit_key, False):
        if st.button("🔄 Force Reinitialize", help="Force reinitialize all providers", use_container_width=True, key="force_reinit_btn"):
            # Set processing flag immediately
            st.session_state[reinit_key] = True
            
            # Show immediate feedback
            st.info("🔄 Starting provider reinitialization...")
            
            # Perform reinitialization with proper error handling
            with st.spinner("🔄 Reinitializing all providers..."):
                try:
                    settings_manager = get_enhanced_settings_manager()
                    success, message = settings_manager.force_reinitialize_providers()
                    
                    if success:
                        st.success(f"✅ {message}")
                        # Add a small delay to ensure user sees the success message
                        time.sleep(1)
                    else:
                        st.error(f"❌ {message}")
                        
                except Exception as e:
                    st.error(f"❌ Force reinitialization failed: {e}")
                    logger.error(f"Force reinitialization error: {e}")
                
                finally:
                    # Always clear the flag, regardless of success or failure
                    if reinit_key in st.session_state:
                        del st.session_state[reinit_key]
                    
                    # Force a rerun to update the UI after clearing the flag
                    st.rerun()
    else:
        # Show processing state
        st.info("🔄 Reinitialization in progress... Please wait.")
        # Automatically clear stuck states after timeout
        if 'reinit_start_time' not in st.session_state:
            st.session_state['reinit_start_time'] = time.time()
        elif time.time() - st.session_state['reinit_start_time'] > 30:  # 30 second timeout
            # Clear stuck state
            if reinit_key in st.session_state:
                del st.session_state[reinit_key]
            if 'reinit_start_time' in st.session_state:
                del st.session_state['reinit_start_time']
            st.warning("⚠️ Reinitialization timed out. Please try again.")
            st.rerun()


# Alternative simplified version that's even more robust
def simplified_force_reinitialize_button():
    """
    Simplified version that prevents all issues
    """
    
    # Use a simple boolean flag with automatic timeout
    if st.button("🔄 Force Reinitialize", help="Force reinitialize all providers", use_container_width=True):
        
        # Perform reinitialization immediately without complex state management
        with st.spinner("🔄 Reinitializing all providers..."):
            try:
                settings_manager = get_enhanced_settings_manager()
                success, message = settings_manager.force_reinitialize_providers()
                
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
                    
            except Exception as e:
                st.error(f"❌ Force reinitialization failed: {e}")
                logger.error(f"Force reinitialization error: {e}")


print("Fix code ready. Apply the simplified_force_reinitialize_button() version to your Streamlit app.")
