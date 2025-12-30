import streamlit as st


def render_choice():
    st.markdown("### ⚠️ Failed Timeline Alert")

    # Large container for the scenario description
    with st.container():
        st.info("The following scenario describes a catastrophic failure based on your current plan.")
        st.markdown("""
        **Scenario:** Your primary server fails during the peak hours of your product launch. 
        Your backup recovery plan takes 4 hours, during which you lose 40% of your potential users.
        """)

    st.markdown("---")

    # Radio options in a clean list
    choice = st.radio("**What is your immediate contingency?**",
                      ["Deploy automated failover (Extra $2k/mo)",
                       "Implement manual hot-swap protocols",
                       "Accept the risk and focus on PR recovery",
                       "Other"],
                      index=0)

    if choice == "Other":
        st.text_input("Custom Response", placeholder="Describe your alternative action...")

    st.write("##")  # Spacer

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Commit Decision", type="primary", use_container_width=True):
            st.session_state.page = "DASHBOARD"
            st.rerun()