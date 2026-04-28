import streamlit as st
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import CredentialCreate, PermissionedDomainSet, EscrowCreate
from xrpl.utils import str_to_hex
import qrcode
from io import BytesIO
import os
from dotenv import load_doten
# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="GLN - Global Liquidity Nexus",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 Global Liquidity Nexus (GLN)")
st.markdown("**Testnet Demo** — Native XRPL Atomic Interoperability")

# Sidebar
st.sidebar.header("Connection")
testnet_url = st.sidebar.text_input(
    "XRPL Testnet URL", 
    value="wss://s.altnet.rippletest.net:51233"
)

# Initialize client
client = JsonRpcClient(testnet_url)

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
            try:
                tx = CredentialCreate(
                    account="rIssuer...",  # You can change this later
                    subject=subject_address,
                    credential_type=str_to_hex("GLN_KYC_TESTNET_2026"),
                    expiration=xrpl.utils.time_to_ripple_time(30 * 24 * 60 * 60)  # 30 days from now
                )
                st.success("✅ Credential transaction prepared!")
                st.json(tx.to_dict())
                st.info("Copy this transaction and sign it using the XUMM app.")
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.header("Create Permissioned Domain (XLS-80)")
    domain_name = st.text_input("Domain Name", value="GLN-TEST-DOMAIN")
    
    if st.button("Create Permissioned Domain", type="primary", use_container_width=True):
        try:
            tx = PermissionedDomainSet(
                domain_name=domain_name,
                accepted_credentials=[{
                    "CredentialType": str_to_hex("GLN_KYC_TESTNET_2026")
                }]
            )
            st.success("✅ Permissioned Domain transaction prepared!")
            st.json(tx.to_dict())
            st.info("Sign this transaction using XUMM.")
        except Exception as e:
            st.error(f"Error: {e}")

with tab3:
    st.header("Atomic Settlement Path")
    destination = st.text_input("Destination Address", placeholder="r...")
    amount = st.text_input("Amount in drops", value="1000")
    
    if st.button("Create Atomic Escrow Path", type="primary", use_container_width=True):
        if not destination:
            st.error("Please enter a destination address")
        else:
            try:
                condition = xrpl.crypto.generate_xrp_condition_and_fulfillment()[0]
                
                tx = EscrowCreate(
                    destination=destination,
                    amount=amount,
                    condition=condition,
                    cancel_after=xrpl.utils.time_to_ripple_time(3600)  # 1 hour
                )
                st.success("✅ Atomic Escrow Path created!")
                st.json(tx.to_dict())
                st.info("Sign this transaction using XUMM.")
            except Exception as e:
                st.error(f"Error: {e}")

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
    
    if st.button("Show Example SignerListSet Structure"):
        example = {
            "TransactionType": "SignerListSet",
            "SignerQuorum": 2,
            "SignerEntries": [
                {"SignerEntry": {"Account": "rsigner1...", "SignerWeight": 1}},
                {"SignerEntry": {"Account": "rsigner2...", "SignerWeight": 1}}
            ]
        }
        st.json(example)

# Footer
st.markdown("---")
st.caption("GLN Testnet Demo • Educational Purpose Only • No Real Value")

# Optional QR Code Helper
if st.button("Generate Example XUMM QR Code"):
    qr = qrcode.make("https://xumm.app")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), caption="Example XUMM QR Code")
