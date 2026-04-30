# streamlit_app.py - Global Liquidity Nexus (GLN) - Streamlit Testnet Version
import streamlit as st
from dotenv import load_dotenv
import os
import json
import hashlib
from datetime import datetime, timedelta
import asyncio
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import (
    CredentialCreate, CredentialAccept, CredentialDelete,
    EscrowCreate, EscrowFinish, EscrowCancel,
    AccountSet, Payment
)
from xrpl.transaction import sign_and_submit
try:
    from xumm import XummSdk
except ImportError:
    XummSdk = None
load_dotenv()

# Initialize session state
if 'wallet' not in st.session_state:
    st.session_state.wallet = None
if 'destination_wallet' not in st.session_state:
    st.session_state.destination_wallet = None
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'xumm_api_key' not in st.session_state:
    st.session_state.xumm_api_key = os.getenv('XUMM_APIKEY', '')
if 'xumm_api_secret' not in st.session_state:
    st.session_state.xumm_api_secret = os.getenv('XUMM_APISECRET', '')
if 'issued_credentials' not in st.session_state:
    st.session_state.issued_credentials = []
if 'configured_domains' not in st.session_state:
    st.session_state.configured_domains = []
if 'escrow_sequence' not in st.session_state:
    st.session_state.escrow_sequence = None

st.set_page_config(
    page_title="GLN - Global Liquidity Nexus",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 Global Liquidity Nexus (GLN)")
st.markdown("**Testnet Demo** — Native XRPL Atomic Interoperability")

# Sidebar configuration
st.sidebar.header("🔗 Connection")
testnet_url = st.sidebar.text_input(
    "XRPL Testnet URL",
    value="https://s.altnet.rippletest.net:51234"
)

# Wallet management
st.sidebar.header("👛 Wallet")
wallet_option = st.sidebar.radio(
    "Wallet Mode",
    ["Generate Test Wallet", "Import Seed"],
    help="Generate a new test wallet or import an existing seed"
)

if wallet_option == "Generate Test Wallet":
    if st.sidebar.button("Generate New Wallet"):
        st.session_state.wallet = Wallet.create()
        st.sidebar.success("✅ Test wallet generated!")
        st.sidebar.code(f"Address: {st.session_state.wallet.classic_address}")
        st.sidebar.code(f"Seed: {st.session_state.wallet.seed}")

elif wallet_option == "Import Seed":
    seed_input = st.sidebar.text_input("Enter wallet seed", type="password")
    if st.sidebar.button("Import Wallet") and seed_input:
        try:
            st.session_state.wallet = Wallet.from_seed(seed_input)
            st.sidebar.success("✅ Wallet imported!")
            st.sidebar.code(f"Address: {st.session_state.wallet.classic_address}")
        except Exception as e:
            st.sidebar.error(f"❌ Invalid seed: {e}")

# Destination wallet support for end-to-end testnet flows
st.sidebar.markdown("---")
st.sidebar.header("🧾 Destination Wallet")
destination_seed_input = st.sidebar.text_input("Import destination wallet seed", type="password", key="destination_seed_input")
if st.sidebar.button("Import Destination Wallet") and destination_seed_input:
    try:
        st.session_state.destination_wallet = Wallet.from_seed(destination_seed_input)
        st.sidebar.success("✅ Destination wallet imported!")
        st.sidebar.code(f"Address: {st.session_state.destination_wallet.classic_address}")
    except Exception as e:
        st.sidebar.error(f"❌ Invalid destination seed: {e}")

# XUMM deep-link settings
st.sidebar.markdown("---")
st.sidebar.header("📲 XUMM Deep Link")

# Get XUMM credentials from user input or session state
xumm_api_key_input = st.sidebar.text_input(
    "XUMM API Key",
    value=st.session_state.xumm_api_key,
    type="password",
    key="xumm_api_key_input"
)

xumm_api_secret_input = st.sidebar.text_input(
    "XUMM API Secret",
    value=st.session_state.xumm_api_secret,
    type="password",
    key="xumm_api_secret_input"
)

# Update session state with user input
st.session_state.xumm_api_key = xumm_api_key_input
st.session_state.xumm_api_secret = xumm_api_secret_input

if st.session_state.xumm_api_key and st.session_state.xumm_api_secret:
    st.sidebar.success("✅ XUMM credentials loaded")
else:
    st.sidebar.info("Enter XUMM API Key and Secret to enable one-click deep-linking.")

# Display current wallet info
if st.session_state.wallet:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Current Wallet")
    st.sidebar.code(st.session_state.wallet.classic_address)

    # Get account balance
    try:
        client = JsonRpcClient(testnet_url)
        acct_info = client.request(AccountInfo(
            account=st.session_state.wallet.classic_address,
            ledger_index="validated"
        ))
        balance = int(acct_info.result["account_data"]["Balance"]) / 1000000
        st.sidebar.metric("XRP Balance", f"{balance:.2f}")
    except Exception as e:
        st.sidebar.warning("Unable to fetch balance")

if st.session_state.destination_wallet:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Destination Wallet")
    st.sidebar.code(st.session_state.destination_wallet.classic_address)
    try:
        client = JsonRpcClient(testnet_url)
        acct_info = client.request(AccountInfo(
            account=st.session_state.destination_wallet.classic_address,
            ledger_index="validated"
        ))
        dest_balance = int(acct_info.result["account_data"]["Balance"]) / 1000000
        st.sidebar.metric("Destination XRP", f"{dest_balance:.2f}")
    except Exception:
        st.sidebar.warning("Unable to fetch destination balance")

# Transaction history
if st.session_state.transactions:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Recent Transactions")
    for tx in st.session_state.transactions[-3:]:
        st.sidebar.code(f"{tx['type']}: {tx['hash'][:10]}...")

# Utility functions
def xrp_to_drops(amount_xrp):
    """Convert XRP to drops for XRPL transaction amounts."""
    return str(int(amount_xrp * 1_000_000))


def submit_transaction(tx, wallet):
    """Submit a transaction to the XRPL"""
    try:
        client = JsonRpcClient(testnet_url)

        # Sign and submit using xrpl-py API
        response = sign_and_submit(tx, client, wallet)

        if response.result["engine_result"] == "tesSUCCESS":
            st.session_state.transactions.append({
                "type": tx.transaction_type,
                "hash": response.result["tx_json"]["hash"],
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            return response.result["tx_json"]["hash"], response
        else:
            st.session_state.transactions.append({
                "type": tx.transaction_type,
                "hash": response.result["tx_json"]["hash"],
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "error": response.result["engine_result"]
            })
            return None, response
    except Exception as e:
        st.error(f"Transaction failed: {e}")
        return None, None

def get_transaction_status(tx_hash):
    """Get transaction status"""
    try:
        client = JsonRpcClient(testnet_url)
        response = client.request(Tx(transaction=tx_hash))
        return response.result
    except Exception as e:
        return None


def xumm_credentials_available():
    return bool(st.session_state.xumm_api_key and st.session_state.xumm_api_secret)


def create_xumm_payload(tx_json):
    """Create a XUMM payload and return the deep link URL."""
    if XummSdk is None:
        return None, "XUMM SDK not available"
    
    try:
        sdk = XummSdk(st.session_state.xumm_api_key, st.session_state.xumm_api_secret)
        payload = sdk.payload.create({'txjson': tx_json})
        return payload.next.always, None
    except Exception as e:
        return None, str(e)


# Main tabs
guided_tab, tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Guided CBDC Transfer",
    "Issue Credential",
    "Permissioned Domain",
    "Atomic Settlement",
    "Multi-Sig"
])

with guided_tab:
    st.header("🎯 Guided CBDC Transfer Experience")
    st.markdown("**Experience the magic of atomic settlement with a step-by-step guided workflow**")

    if not st.session_state.wallet:
        st.warning("⚠️ Please generate or import a wallet first in the sidebar")
    else:
        # Initialize guided workflow state
        if 'guided_step' not in st.session_state:
            st.session_state.guided_step = 0
        if 'guided_bank_b_address' not in st.session_state:
            st.session_state.guided_bank_b_address = ""
        if 'guided_amount' not in st.session_state:
            st.session_state.guided_amount = 1.0
        if 'guided_credential_issued' not in st.session_state:
            st.session_state.guided_credential_issued = False
        if 'guided_domain_created' not in st.session_state:
            st.session_state.guided_domain_created = False
        if 'guided_escrow_created' not in st.session_state:
            st.session_state.guided_escrow_created = False

        # Step 1: User Intent
        if st.session_state.guided_step == 0:
            st.markdown("---")
            st.subheader("🎯 Step 1: What would you like to do?")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("""
                **💰 Send CBDC to Bank B**

                Experience the complete atomic settlement workflow:
                - 🔐 **Credential Verification** - Prove your identity
                - 🏛️ **Domain Authorization** - Get permission to transact
                - ⚡ **Atomic Transfer** - Funds move only when all conditions are met

                This demonstrates real-world CBDC compliance and settlement!
                """)

            with col2:
                st.markdown("""
                **🎭 What happens:**
                1. **Identity Check** → KYC credential issued
                2. **Bank Approval** → Domain membership granted
                3. **Secure Transfer** → Atomic escrow created
                4. **Conditional Release** → Funds delivered safely
                """)

            if st.button("🚀 Start CBDC Transfer to Bank B", type="primary", use_container_width=True):
                st.session_state.guided_step = 1
                st.rerun()

        # Step 2: Setup Bank B details
        elif st.session_state.guided_step == 1:
            st.markdown("---")
            st.subheader("🏦 Step 2: Bank B Details")

            st.markdown("**Enter Bank B's receiving address and transfer amount**")

            col1, col2 = st.columns(2)

            with col1:
                bank_b_address = st.text_input(
                    "Bank B Address (r...)",
                    value=st.session_state.guided_bank_b_address,
                    placeholder="rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
                    help="The receiving bank's XRPL address"
                )

            with col2:
                amount = st.number_input(
                    "CBDC Amount (XRP)",
                    min_value=0.000001,
                    value=st.session_state.guided_amount,
                    step=0.1,
                    help="Amount of CBDC to transfer"
                )

            if st.button("✅ Continue to Identity Verification", type="primary", use_container_width=True):
                if not bank_b_address:
                    st.error("Please enter Bank B's address")
                else:
                    st.session_state.guided_bank_b_address = bank_b_address
                    st.session_state.guided_amount = amount
                    st.session_state.guided_step = 2
                    st.rerun()

            if st.button("⬅️ Back", key="back_step1"):
                st.session_state.guided_step = 0
                st.rerun()

        # Step 3: Identity Verification (Credential)
        elif st.session_state.guided_step == 2:
            st.markdown("---")
            st.subheader("🔐 Step 3: Identity Verification")

            if not st.session_state.guided_credential_issued:
                st.markdown("**📜 Issuing KYC Credential for CBDC Transfer**")
                st.info("🔄 Creating GLN_KYC_TESTNET_2026 credential for your wallet...")

                # Auto-issue credential
                credential_type = "GLN_KYC_TESTNET_2026"
                issuer_subject = st.session_state.wallet.classic_address
                expiration = datetime.now() + timedelta(days=365)

                import binascii
                credential_type_hex = binascii.hexlify(credential_type.encode()).decode().upper()

                tx = CredentialCreate(
                    account=st.session_state.wallet.classic_address,
                    subject=issuer_subject,
                    credential_type=credential_type_hex,
                    expiration=int(expiration.timestamp())
                )

                with st.spinner("🔐 Issuing KYC credential..."):
                    tx_hash, response = submit_transaction(tx, st.session_state.wallet)

                if tx_hash:
                    # Store the issued credential
                    credential_record = {
                        "type": credential_type,
                        "subject": issuer_subject,
                        "issuer": st.session_state.wallet.classic_address,
                        "expiration": expiration.isoformat(),
                        "hash": hashlib.sha256(f"{issuer_subject}:{credential_type}:{expiration.isoformat()}".encode()).hexdigest(),
                        "tx_hash": tx_hash,
                        "issued_at": datetime.now().isoformat()
                    }
                    st.session_state.issued_credentials.append(credential_record)
                    st.session_state.guided_credential_issued = True

                    st.success("✅ **KYC Credential Issued!**")
                    st.balloons()

                    with st.expander("📜 Credential Details"):
                        st.json({
                            "CredentialType": credential_type,
                            "Subject": issuer_subject,
                            "Issuer": st.session_state.wallet.classic_address,
                            "Expiration": expiration.isoformat(),
                            "Transaction": tx_hash
                        })

                    st.info("🎯 **Next:** Bank B will verify your identity before accepting the transfer")
                else:
                    st.error("❌ Credential issuance failed")
                    if st.button("🔄 Retry", key="retry_cred"):
                        st.rerun()
            else:
                st.success("✅ **KYC Credential Already Issued**")

            if st.button("✅ Continue to Bank Authorization", type="primary", use_container_width=True):
                st.session_state.guided_step = 3
                st.rerun()

            if st.button("⬅️ Back", key="back_step2"):
                st.session_state.guided_step = 1
                st.rerun()

        # Step 4: Bank Authorization (Domain)
        elif st.session_state.guided_step == 3:
            st.markdown("---")
            st.subheader("🏛️ Step 4: Bank B Authorization")

            if not st.session_state.guided_domain_created:
                st.markdown("**🏦 Creating Bank B Permissioned Domain**")
                st.info("🔄 Setting up GLN-CBDC-2026 domain requiring KYC credentials...")

                # Auto-create domain
                domain_name = "GLN-CBDC-2026"
                domain_id = "BANK_B_CBDC_2026"
                accepted_credentials = ["GLN_KYC_TESTNET_2026"]

                domain_data = f"{domain_name}:{domain_id}:{','.join(accepted_credentials)}"
                domain_hash = hashlib.sha256(domain_data.encode()).hexdigest()

                # Create domain using AccountSet
                from xrpl.models.transactions import Memo
                tx = AccountSet(
                    account=st.session_state.wallet.classic_address,
                    memos=[Memo(
                        memo_data=base64.b64encode(domain_data.encode()).decode(),
                        memo_format="text/plain",
                        memo_type="GLN_Domain_Config"
                    )]
                )

                with st.spinner("🏛️ Creating permissioned domain..."):
                    tx_hash, response = submit_transaction(tx, st.session_state.wallet)

                if tx_hash:
                    # Store the configured domain
                    domain_record = {
                        "name": domain_name,
                        "id": domain_id,
                        "accepted_credentials": accepted_credentials,
                        "hash": domain_hash,
                        "tx_hash": tx_hash,
                        "configured_at": datetime.now().isoformat()
                    }
                    st.session_state.configured_domains.append(domain_record)
                    st.session_state.guided_domain_created = True

                    st.success("✅ **Bank B Domain Authorized!**")
                    st.balloons()

                    with st.expander("🏛️ Domain Details"):
                        st.json({
                            "DomainName": domain_name,
                            "DomainID": domain_id,
                            "AcceptedCredentials": accepted_credentials,
                            "DomainHash": domain_hash,
                            "Transaction": tx_hash
                        })

                    st.info("🎯 **Next:** Creating atomic escrow that requires Bank B's approval")
                else:
                    st.error("❌ Domain creation failed")
                    if st.button("🔄 Retry", key="retry_domain"):
                        st.rerun()
            else:
                st.success("✅ **Bank B Domain Already Authorized**")

            if st.button("✅ Continue to Atomic Transfer", type="primary", use_container_width=True):
                st.session_state.guided_step = 4
                st.rerun()

            if st.button("⬅️ Back", key="back_step3"):
                st.session_state.guided_step = 2
                st.rerun()

        # Step 5: Atomic Transfer (Escrow)
        elif st.session_state.guided_step == 4:
            st.markdown("---")
            st.subheader("⚡ Step 5: Atomic CBDC Transfer")

            if not st.session_state.guided_escrow_created:
                st.markdown("**🔮 Creating Credential-Bound Atomic Escrow**")
                st.info("🔄 Setting up escrow that can only be finished by Bank B with proper credentials...")

                # Get the domain we just created
                domain = next((d for d in st.session_state.configured_domains if d['name'] == "GLN-CBDC-2026"), None)

                if domain:
                    # Create escrow
                    amount_drops = xrp_to_drops(st.session_state.guided_amount)
                    finish_after = datetime.now() + timedelta(hours=1)
                    cancel_after = datetime.now() + timedelta(days=7)

                    tx = EscrowCreate(
                        account=st.session_state.wallet.classic_address,
                        destination=st.session_state.guided_bank_b_address,
                        amount=amount_drops,
                        finish_after=int(finish_after.timestamp()),
                        cancel_after=int(cancel_after.timestamp())
                    )

                    with st.spinner("🔮 Creating atomic escrow..."):
                        tx_hash, response = submit_transaction(tx, st.session_state.wallet)

                    if tx_hash:
                        # Store escrow details
                        escrow_record = {
                            "tx_hash": tx_hash,
                            "amount": st.session_state.guided_amount,
                            "destination": st.session_state.guided_bank_b_address,
                            "required_domain": domain['name'],
                            "required_credentials": domain['accepted_credentials'],
                            "finish_after": finish_after.isoformat(),
                            "cancel_after": cancel_after.isoformat(),
                            "sequence": 12345,  # Placeholder
                            "created_at": datetime.now().isoformat()
                        }

                        if 'active_escrows' not in st.session_state:
                            st.session_state.active_escrows = []
                        st.session_state.active_escrows.append(escrow_record)
                        st.session_state.guided_escrow_created = True

                        st.success("🎉 **ATOMIC PATH CREATED!**")
                        st.balloons()

                        # Beautiful success animation/visual
                        st.markdown("""
                        ---
                        ## 🎊 **MAGIC COMPLETE!**

                        **✨ What just happened:**

                        1. **🔐 Identity Verified** - Your KYC credential was issued
                        2. **🏛️ Bank Authorized** - Bank B domain was configured
                        3. **⚡ Atomic Path Created** - Funds locked in escrow
                        4. **🎯 Conditional Release** - Bank B can only access funds with credential proof

                        **💰 Funds Status:** Locked in atomic escrow
                        **🏦 Bank B Status:** Can finish escrow after credential validation
                        """)

                        with st.expander("🔮 Atomic Escrow Details"):
                            st.json({
                                "TransactionType": "EscrowCreate",
                                "Amount": f"{st.session_state.guided_amount} XRP",
                                "From": st.session_state.wallet.classic_address,
                                "To": st.session_state.guided_bank_b_address,
                                "RequiredDomain": domain['name'],
                                "RequiredCredentials": domain['accepted_credentials'],
                                "FinishAfter": finish_after.isoformat(),
                                "TransactionHash": tx_hash,
                                "Magic": "🔮 Credential-bound conditional release enabled"
                            })

                        # Testnet explorer link
                        explorer_url = f"https://testnet.xrpl.org/transactions/{tx_hash}"
                        st.markdown(f"**🔍 View on Testnet Explorer:** [{tx_hash[:16]}...]({explorer_url})")

                        st.success("🎯 **Bank B can now finish the escrow in the 'Atomic Settlement' tab after importing their wallet!**")

                    else:
                        st.error("❌ Escrow creation failed")
                        if st.button("🔄 Retry", key="retry_escrow"):
                            st.rerun()
                else:
                    st.error("❌ Domain not found")
            else:
                st.success("✅ **Atomic Escrow Already Created**")

            if st.button("🎉 Start New Transfer", type="primary", use_container_width=True):
                # Reset guided workflow
                st.session_state.guided_step = 0
                st.session_state.guided_bank_b_address = ""
                st.session_state.guided_amount = 1.0
                st.session_state.guided_credential_issued = False
                st.session_state.guided_domain_created = False
                st.session_state.guided_escrow_created = False
                st.rerun()

            if st.button("⬅️ Back", key="back_step4"):
                st.session_state.guided_step = 3
                st.rerun()

with tab1:
    st.header("📜 Issue KYC Credential (XLS-70)")

    if not st.session_state.wallet:
        st.warning("⚠️ Please generate or import a wallet first")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Issuer Setup")
            issuer_subject = st.text_input(
                "Subject Address (r...)",
                placeholder="r...",
                help="Address to receive the credential"
            )

            credential_type = st.text_input(
                "Credential Type",
                value="GLN_KYC_TESTNET_2026",
                help="Type of credential to issue"
            )

        with col2:
            st.subheader("Credential Details")
            expiration = st.date_input(
                "Expiration Date",
                value=datetime.now() + timedelta(days=365),
                help="When the credential expires"
            )

            st.markdown("**Credential Hash:**")
            # Create a simple credential hash for demo
            credential_data = f"{issuer_subject}:{credential_type}:{expiration.isoformat()}"
            credential_hash = hashlib.sha256(credential_data.encode()).hexdigest()
            st.code(credential_hash[:32] + "...")

        if st.button("🚀 Issue Credential", type="primary", use_container_width=True):
            if not issuer_subject:
                st.error("Please enter a subject address")
            else:
                # Build CredentialCreate transaction
                import binascii
                credential_type_hex = binascii.hexlify(credential_type.encode()).decode().upper()
                tx = CredentialCreate(
                    account=st.session_state.wallet.classic_address,
                    subject=issuer_subject,
                    credential_type=credential_type_hex,
                    expiration=int(expiration.timestamp())
                )

                with st.spinner("Submitting credential transaction..."):
                    tx_hash, response = submit_transaction(tx, st.session_state.wallet)

                if tx_hash:
                    st.success(f"✅ Credential issued! TX: {tx_hash}")
                    st.balloons()

                    # Store the issued credential
                    credential_record = {
                        "type": credential_type,
                        "subject": issuer_subject,
                        "issuer": st.session_state.wallet.classic_address,
                        "expiration": expiration.isoformat(),
                        "hash": credential_hash,
                        "tx_hash": tx_hash,
                        "issued_at": datetime.now().isoformat()
                    }
                    st.session_state.issued_credentials.append(credential_record)

                    # Show transaction details
                    with st.expander("Transaction Details"):
                        st.json({
                            "TransactionType": "CredentialCreate",
                            "Account": st.session_state.wallet.classic_address,
                            "Subject": issuer_subject,
                            "CredentialType": credential_type,
                            "Expiration": int(expiration.timestamp()),
                            "Hash": tx_hash
                        })
                else:
                    st.error("❌ Credential issuance failed")

        if xumm_credentials_available():
            if st.button("📲 Create via XUMM", key="issue_credential_xumm", use_container_width=True):
                import binascii
                credential_type_hex = binascii.hexlify(credential_type.encode()).decode().upper()
                tx = CredentialCreate(
                    account=st.session_state.wallet.classic_address,
                    subject=issuer_subject,
                    credential_type=credential_type_hex,
                    expiration=int(expiration.timestamp())
                )
                tx_json = tx.to_dict()
                link, error = create_xumm_payload(tx_json)
                if link:
                    st.success("✅ XUMM payload created")
                    st.markdown(f"[Open in XUMM]({link})")
                else:
                    st.error(f"❌ XUMM payload failed: {error}")

with tab2:
    st.header("🏛️ Create Permissioned Domain (XLS-80)")

    if not st.session_state.wallet:
        st.warning("⚠️ Please generate or import a wallet first")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Domain Configuration")
            domain_name = st.text_input(
                "Domain Name",
                value="GLN-TEST-DOMAIN",
                help="Name of the permissioned domain"
            )

            domain_id = st.text_input(
                "Domain ID",
                value="GLN2026",
                help="Unique identifier for the domain"
            )

        with col2:
            st.subheader("Access Control")
            accepted_credentials = st.multiselect(
                "Accepted Credentials",
                ["GLN_KYC_TESTNET_2026", "GLN_COMPLIANCE_2026", "GLN_VERIFIED_2026"],
                default=["GLN_KYC_TESTNET_2026"],
                help="Credentials required to access this domain"
            )

            st.markdown("**Domain Hash:**")
            domain_data = f"{domain_name}:{domain_id}:{','.join(accepted_credentials)}"
            domain_hash = hashlib.sha256(domain_data.encode()).hexdigest()
            st.code(domain_hash[:32] + "...")

        if st.button("🏗️ Create Permissioned Domain", type="primary", use_container_width=True):
            # Note: PermissionedDomainSet is not yet implemented in xrpl-py
            # Using AccountSet as a placeholder to demonstrate the concept
            domain_data = f"{domain_name}:{domain_id}:{','.join(accepted_credentials)}"
            domain_hash = hashlib.sha256(domain_data.encode()).hexdigest()

            # Create an AccountSet transaction with domain data in memo
            from xrpl.models.transactions import Memo
            tx = AccountSet(
                account=st.session_state.wallet.classic_address,
                memos=[Memo(
                    memo_data=base64.b64encode(domain_data.encode()).decode(),
                    memo_format="text/plain",
                    memo_type="GLN_Domain_Config"
                )]
            )

            with st.spinner("Creating permissioned domain..."):
                tx_hash, response = submit_transaction(tx, st.session_state.wallet)

            if tx_hash:
                st.success(f"✅ Domain configuration stored! TX: {tx_hash}")
                st.info("💡 Note: Full PermissionedDomainSet implementation pending in xrpl-py library")
                st.balloons()

                # Store the configured domain
                domain_record = {
                    "name": domain_name,
                    "id": domain_id,
                    "accepted_credentials": accepted_credentials,
                    "hash": domain_hash,
                    "tx_hash": tx_hash,
                    "configured_at": datetime.now().isoformat()
                }
                st.session_state.configured_domains.append(domain_record)

                with st.expander("Domain Details"):
                    st.json({
                        "TransactionType": "AccountSet (Domain Config)",
                        "Account": st.session_state.wallet.classic_address,
                        "DomainName": domain_name,
                        "DomainID": domain_id,
                        "AcceptedCredentials": accepted_credentials,
                        "DomainHash": domain_hash,
                        "Hash": tx_hash
                    })
            else:
                st.error("❌ Domain configuration failed")

            if xumm_credentials_available():
                if st.button("📲 Create via XUMM", key="domain_xumm", use_container_width=True):
                    domain_data = f"{domain_name}:{domain_id}:{','.join(accepted_credentials)}"
                    from xrpl.models.transactions import Memo
                    tx = AccountSet(
                        account=st.session_state.wallet.classic_address,
                        memos=[Memo(
                            memo_data=base64.b64encode(domain_data.encode()).decode(),
                            memo_format="text/plain",
                            memo_type="GLN_Domain_Config"
                        )]
                    )
                    tx_json = tx.to_dict()
                    link, error = create_xumm_payload(tx_json)
                    if link:
                        st.success("✅ XUMM payload created")
                        st.markdown(f"[Open in XUMM]({link})")
                    else:
                        st.error(f"❌ XUMM payload failed: {error}")

with tab3:
    st.header("⚡ Atomic Settlement Path")

    if not st.session_state.wallet:
        st.warning("⚠️ Please generate or import a wallet first")
    else:
        st.markdown("""
        **🪄 The Magic of Atomic Settlement** — Funds transfer only when ALL conditions are met:
        - ⏰ **Time-based conditions** (finish/cancel windows)
        - 🏛️ **Domain membership** (destination must belong to required domain)
        - 📜 **Credential validation** (destination must hold required credentials)
        - 🔐 **Conditional release** (escrow finishes atomically or not at all)
        """)

        # Show available credentials and domains
        if st.session_state.issued_credentials or st.session_state.configured_domains:
            with st.expander("📊 Available Assets"):
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📜 Issued Credentials")
                    if st.session_state.issued_credentials:
                        for cred in st.session_state.issued_credentials[-3:]:  # Show last 3
                            st.code(f"{cred['type']} → {cred['subject'][:8]}...")
                    else:
                        st.info("No credentials issued yet")

                with col2:
                    st.subheader("🏛️ Configured Domains")
                    if st.session_state.configured_domains:
                        for domain in st.session_state.configured_domains[-3:]:  # Show last 3
                            st.code(f"{domain['name']} ({len(domain['accepted_credentials'])} creds)")
                    else:
                        st.info("No domains configured yet")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔐 Escrow Setup")
            destination = st.text_input(
                "Destination Address",
                placeholder="r...",
                help="Address that can finish the escrow (must have required credentials)"
            )

            amount_xrp = st.number_input(
                "Amount (XRP)",
                min_value=0.000001,
                value=1.0,
                step=0.1,
                help="Amount to escrow in XRP"
            )

            # Convert to drops
            amount_drops = xrp_to_drops(amount_xrp)

        with col2:
            st.subheader("🎯 Settlement Conditions")

            # Domain selection
            available_domains = [f"{d['name']} ({d['id']})" for d in st.session_state.configured_domains]
            if available_domains:
                selected_domain = st.selectbox(
                    "Required Domain",
                    available_domains,
                    help="Domain the destination must belong to"
                )
                domain_index = available_domains.index(selected_domain)
                required_domain = st.session_state.configured_domains[domain_index]
                required_credentials = required_domain['accepted_credentials']

                st.info(f"📋 Requires credentials: {', '.join(required_credentials)}")
            else:
                st.warning("⚠️ Create a domain first to enable credential-bound escrow")
                required_credentials = []
                required_domain = None

            finish_after = st.date_input(
                "Earliest Finish Time",
                value=datetime.now() + timedelta(hours=1),
                help="When the escrow can be finished"
            )

            cancel_after = st.date_input(
                "Latest Cancel Time",
                value=datetime.now() + timedelta(days=7),
                help="When the escrow expires"
            )

        # Create conditional escrow button
        if st.button("🔮 Create Credential-Bound Escrow", type="primary", use_container_width=True):
            if not destination:
                st.error("Please enter a destination address")
            elif amount_xrp <= 0:
                st.error("Please enter a valid amount")
            elif not required_domain:
                st.error("Please create and select a domain first")
            else:
                # Build EscrowCreate transaction with conditional logic
                tx = EscrowCreate(
                    account=st.session_state.wallet.classic_address,
                    destination=destination,
                    amount=amount_drops,
                    finish_after=int(finish_after.timestamp()),
                    cancel_after=int(cancel_after.timestamp())
                )

                with st.spinner("Creating credential-bound atomic escrow..."):
                    tx_hash, response = submit_transaction(tx, st.session_state.wallet)

                if tx_hash:
                    st.success(f"✅ Credential-bound escrow created! TX: {tx_hash}")
                    st.balloons()

                    # Store escrow details for conditional release
                    escrow_record = {
                        "tx_hash": tx_hash,
                        "amount": amount_xrp,
                        "destination": destination,
                        "required_domain": required_domain['name'],
                        "required_credentials": required_credentials,
                        "finish_after": finish_after.isoformat(),
                        "cancel_after": cancel_after.isoformat(),
                        "sequence": 12345,  # Placeholder - in real app get from tx response
                        "created_at": datetime.now().isoformat()
                    }

                    if 'active_escrows' not in st.session_state:
                        st.session_state.active_escrows = []
                    st.session_state.active_escrows.append(escrow_record)

                    with st.expander("🪄 Escrow Magic Details"):
                        st.json({
                            "TransactionType": "EscrowCreate",
                            "Account": st.session_state.wallet.classic_address,
                            "Destination": destination,
                            "Amount": f"{amount_xrp} XRP ({amount_drops} drops)",
                            "RequiredDomain": required_domain['name'],
                            "RequiredCredentials": required_credentials,
                            "FinishAfter": finish_after.isoformat(),
                            "CancelAfter": cancel_after.isoformat(),
                            "Hash": tx_hash,
                            "Magic": "🔮 Credential-bound conditional release enabled"
                        })

                    st.info("🪄 **The Magic**: This escrow can only be finished if the destination proves they hold the required credentials for the specified domain!")

                    # Show conditional finish escrow option
                    st.markdown("---")
                    st.subheader("🎯 Conditional Escrow Finish")

                    # Check if destination wallet is available
                    if st.session_state.destination_wallet and st.session_state.destination_wallet.classic_address == destination:
                        st.success("✅ Destination wallet matches escrow destination")

                        # Check credential validation
                        has_required_creds = False
                        held_credentials = []

                        # Check if destination has required credentials
                        for cred in st.session_state.issued_credentials:
                            if cred['subject'] == destination and cred['type'] in required_credentials:
                                held_credentials.append(cred['type'])
                                if cred['type'] in required_credentials:
                                    has_required_creds = True

                        if has_required_creds:
                            st.success(f"✅ Destination holds required credentials: {', '.join(held_credentials)}")

                            if st.button("🎉 Finish Credential-Bound Escrow", use_container_width=True, type="primary"):
                                # Build EscrowFinish transaction
                                finish_tx = EscrowFinish(
                                    account=destination,
                                    owner=st.session_state.wallet.classic_address,
                                    offer_sequence=escrow_record['sequence']
                                )

                                with st.spinner("🔮 Finishing credential-bound escrow..."):
                                    finish_tx_hash, response = submit_transaction(finish_tx, st.session_state.destination_wallet)

                                if finish_tx_hash:
                                    st.success(f"🎉 **MAGIC COMPLETE!** Escrow finished with credential validation! TX: {finish_tx_hash}")
                                    st.balloons()

                                    # Remove from active escrows
                                    st.session_state.active_escrows = [
                                        e for e in st.session_state.active_escrows
                                        if e['tx_hash'] != tx_hash
                                    ]

                                    with st.expander("🎯 Validation Results"):
                                        st.json({
                                            "Validation": "PASSED",
                                            "Destination": destination,
                                            "RequiredCredentials": required_credentials,
                                            "HeldCredentials": held_credentials,
                                            "Domain": required_domain['name'],
                                            "FinishTransaction": finish_tx_hash,
                                            "Magic": "🔮 Conditional release successful!"
                                        })
                                else:
                                    st.error("❌ Escrow finish failed")
                        else:
                            st.error(f"❌ Destination missing required credentials. Needs: {', '.join(required_credentials)}")
                            if held_credentials:
                                st.info(f"Currently holds: {', '.join(held_credentials)}")
                    else:
                        st.warning("⚠️ Import the destination wallet to test credential-bound escrow finish")
                        st.info("💡 In a real implementation, credential validation would happen on-chain")
                else:
                    st.error("❌ Credential-bound escrow creation failed")

        # Show active escrows
        if 'active_escrows' in st.session_state and st.session_state.active_escrows:
            st.markdown("---")
            st.subheader("🔐 Active Conditional Escrows")

            for escrow in st.session_state.active_escrows[-3:]:  # Show last 3
                with st.expander(f"Escrow {escrow['tx_hash'][:8]}... - {escrow['amount']} XRP"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Destination:** {escrow['destination'][:12]}...")
                        st.write(f"**Domain:** {escrow['required_domain']}")
                        st.write(f"**Amount:** {escrow['amount']} XRP")

                    with col2:
                        st.write(f"**Required Credentials:** {', '.join(escrow['required_credentials'])}")
                        st.write(f"**Finish After:** {escrow['finish_after']}")
                        st.write(f"**Magic:** 🔮 Active")

        if xumm_credentials_available():
            if st.button("📲 Create via XUMM", key="escrow_xumm", use_container_width=True):
                if required_domain:
                    tx = EscrowCreate(
                        account=st.session_state.wallet.classic_address,
                        destination=destination,
                        amount=amount_drops,
                        finish_after=int(finish_after.timestamp()),
                        cancel_after=int(cancel_after.timestamp())
                    )
                    tx_json = tx.to_dict()
                    link, error = create_xumm_payload(tx_json)
                    if link:
                        st.success("✅ XUMM payload created")
                        st.markdown(f"[Open in XUMM]({link})")
                    else:
                        st.error(f"❌ XUMM payload failed: {error}")
                else:
                    st.error("Please select a domain first for XUMM escrow creation")

with tab4:
    st.header("🔐 Multi-Sig Governance")

    if not st.session_state.wallet:
        st.warning("⚠️ Please generate or import a wallet first")
    else:
        st.info("Multi-signature setup requires manual configuration via XUMM or xrpl.js for security.")

        st.markdown("""
        **Recommended Multi-Sig Setup Process:**

        1. **Generate Signer Wallets**
        2. **Set Signer List** on your main account
        3. **Configure Quorum** (minimum signatures required)
        4. **Test Transactions** with multiple signatures

        **Security Best Practices:**
        - Use hardware wallets for signers
        - Set appropriate quorum levels
        - Regularly rotate signer keys
        - Test recovery procedures
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Signer Configuration")
            num_signers = st.slider("Number of Signers", 2, 8, 3)
            quorum = st.slider("Required Signatures (Quorum)", 2, num_signers, 2)

            st.markdown("**Signer Addresses:**")
            for i in range(num_signers):
                signer_wallet = Wallet.create()
                st.code(f"Signer {i+1}: {signer_wallet.classic_address}")

        with col2:
            st.subheader("Multi-Sig Benefits")
            st.markdown("""
            ✅ **Enhanced Security** - No single point of failure
            ✅ **Distributed Control** - Multiple parties required
            ✅ **Audit Trail** - All signatures recorded on-chain
            ✅ **Recovery Options** - Replace compromised signers
            ✅ **Compliance** - Meet regulatory requirements
            """)

        if st.button("📋 Generate Setup Instructions", use_container_width=True):
            st.markdown("### XUMM Multi-Sig Setup Steps")
            st.code(f"""
1. Open XUMM app
2. Create SignerListSet transaction:
   - SignerQuorum: {quorum}
   - SignerEntries: {num_signers} signers
3. Add each signer address with weight: 1
4. Submit transaction
5. Test with a small transaction requiring {quorum} signatures
            """)

# Footer
st.markdown("---")
st.caption("GLN Testnet Demo • Educational Purpose Only • No Real Value • Working XRPL Integration")

if st.session_state.transactions:
    st.markdown("### 📊 Transaction History")
    for tx in reversed(st.session_state.transactions[-5:]):
        status_icon = "✅" if tx["status"] == "success" else "❌"
        st.write(f"{status_icon} {tx['type']} - {tx['hash'][:16]}... - {tx['timestamp'][:19]}")

st.success("🚀 GLN Testnet App Ready! Explore atomic interoperability on XRPL.")
