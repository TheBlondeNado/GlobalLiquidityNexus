# streamlit_app.py - Global Liquidity Nexus (GLN) - Streamlit Testnet Version
import streamlit as st
from dotenv import load_dotenv
import os
import json
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
st.session_state.xumm_api_key = st.sidebar.text_input(
    "XUMM API Key",
    value=st.session_state.xumm_api_key,
    type="password",
    key="xumm_api_key"
)
st.session_state.xumm_api_secret = st.sidebar.text_input(
    "XUMM API Secret",
    value=st.session_state.xumm_api_secret,
    type="password",
    key="xumm_api_secret"
)
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
tab1, tab2, tab3, tab4 = st.tabs([
    "Issue Credential",
    "Permissioned Domain",
    "Atomic Settlement",
    "Multi-Sig"
])

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
        **Atomic Settlement** ensures that funds only transfer when all conditions are met.
        This demo creates an escrow that can only be released by the recipient.
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Escrow Setup")
            destination = st.text_input(
                "Destination Address",
                placeholder="r...",
                help="Address that can finish the escrow"
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
            st.subheader("Settlement Conditions")
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

        # Create escrow button
        if st.button("🔐 Create Atomic Escrow", type="primary", use_container_width=True):
            if not destination:
                st.error("Please enter a destination address")
            elif amount_xrp <= 0:
                st.error("Please enter a valid amount")
            else:
                # Build EscrowCreate transaction
                tx = EscrowCreate(
                    account=st.session_state.wallet.classic_address,
                    destination=destination,
                    amount=amount_drops,
                    finish_after=int(finish_after.timestamp()),
                    cancel_after=int(cancel_after.timestamp())
                )

                with st.spinner("Creating atomic escrow..."):
                    tx_hash, response = submit_transaction(tx, st.session_state.wallet)

                if tx_hash:
                    st.success(f"✅ Atomic escrow created! TX: {tx_hash}")
                    st.balloons()

                    with st.expander("Escrow Details"):
                        st.json({
                            "TransactionType": "EscrowCreate",
                            "Account": st.session_state.wallet.classic_address,
                            "Destination": destination,
                            "Amount": f"{amount_xrp} XRP ({amount_drops} drops)",
                            "FinishAfter": finish_after.isoformat(),
                            "CancelAfter": cancel_after.isoformat(),
                            "Hash": tx_hash
                        })

                    st.info("💡 The escrow is now locked. Only the destination address can finish it after the finish time.")

                    # Store escrow sequence for finishing
                    if 'escrow_sequence' not in st.session_state:
                        st.session_state.escrow_sequence = None
                    # Note: In a real app, you'd get the sequence from the transaction response
                    # For demo purposes, we'll use a placeholder
                    st.session_state.escrow_sequence = 12345  # Placeholder

                    # Show finish escrow option
                    st.markdown("---")
                    st.subheader("🏁 Finish Escrow (Destination Only)")

                    if st.session_state.destination_wallet:
                        st.info("A destination wallet is imported and can finish the escrow.")
                        if st.button("✅ Finish Escrow with Destination Wallet", use_container_width=True, key="finish_escrow"):
                            if st.session_state.escrow_sequence:
                                finish_tx = EscrowFinish(
                                    account=st.session_state.destination_wallet.classic_address,
                                    owner=st.session_state.wallet.classic_address,
                                    offer_sequence=st.session_state.escrow_sequence
                                )

                                with st.spinner("Submitting EscrowFinish..."):
                                    tx_hash, response = submit_transaction(finish_tx, st.session_state.destination_wallet)

                                if tx_hash:
                                    st.success(f"✅ Escrow finished! TX: {tx_hash}")
                                    st.balloons()
                                else:
                                    st.error("❌ Escrow finish failed")
                            else:
                                st.error("❌ Escrow sequence not available")
                    else:
                        st.warning("Import the destination wallet seed in the sidebar to finish the escrow from that address.")
                        st.code(f"Destination account: {destination}")
                        st.code("EscrowFinish must be signed by the destination account and submitted from that wallet.")

                else:
                    st.error("❌ Escrow creation failed")

        if xumm_credentials_available():
            if st.button("📲 Create via XUMM", key="escrow_xumm", use_container_width=True):
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
