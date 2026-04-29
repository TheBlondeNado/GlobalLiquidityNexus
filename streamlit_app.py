# app.py - Global Liquidity Nexus (GLN) - Streamlit Testnet Version
import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="GLN - Global Liquidity Nexus",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 Global Liquidity Nexus (GLN)")
st.markdown("**Testnet Demo** — Native XRPL Atomic Interoperability")

st.sidebar.header("Connection")
testnet_url = st.sidebar.text_input(
    "XRPL Testnet URL", 
    value="wss://s.altnet.rippletest.net:51233"
)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Issue Credential", 
    "Permissioned Domain", 
    "Atomic Settlement", 
    "Multi-Sig"
])

with tab1:
    st.header("Issue KYC Credential (XLS-70)")
    subject_address = st.text_input("Subject Address (starts with r...)", placeholder="r...")
    
    if st.button("Issue Credential via XUMM", type="primary", use_container_width=True):
        if not subject_address:
            st.error("Please enter a subject address")
        else:
            st.success("✅ Credential transaction prepared!")
            st.info("In a real implementation, this would generate a CredentialCreate transaction for XUMM signing.")
            st.code(f"""
TransactionType: CredentialCreate
Subject: {subject_address}
CredentialType: GLN_KYC_TESTNET_2026
""", language="json")

with tab2:
    st.header("Create Permissioned Domain (XLS-80)")
    domain_name = st.text_input("Domain Name", value="GLN-TEST-DOMAIN")
    
    if st.button("Create Permissioned Domain", type="primary", use_container_width=True):
        st.success("✅ Permissioned Domain transaction prepared!")
        st.info("This would create a PermissionedDomainSet transaction.")
        st.code(f"""
TransactionType: PermissionedDomainSet
DomainName: {domain_name}
AcceptedCredentials: GLN_KYC_TESTNET_2026
""", language="json")

with tab3:
    st.header("Atomic Settlement Path")
    destination = st.text_input("Destination Address", placeholder="r...")
    amount = st.text_input("Amount in drops", value="1000")
    
    if st.button("Create Atomic Escrow Path", type="primary", use_container_width=True):
        if not destination:
            st.error("Please enter a destination address")
        else:
            st.success("✅ Atomic Escrow Path created!")
            st.info("This would create an EscrowCreate transaction with condition for atomic settlement.")
            st.code(f"""
TransactionType: EscrowCreate
Destination: {destination}
Amount: {amount}
""", language="json")

with tab4:
    st.header("Multi-Sig Governance")
    st.info("Multi-signature setup on XRPL is best done manually via the XUMM app for security on testnet.")
    
    st.markdown("""
    **Recommended Steps:**
    1. Open XUMM app
    2. Create a new transaction of type `SignerListSet`
    3. Set `SignerQuorum` to 2 (or higher)
    4. Add your signer accounts
    """)

# Footer
st.markdown("---")
st.caption("GLN Testnet Demo • Educational Purpose Only • No Real Value • Streamlit Version")

st.success("App is running! Use the tabs above to explore GLN features.")
