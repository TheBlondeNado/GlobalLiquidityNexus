# � Global Liquidity Nexus (GLN)

A Streamlit application demonstrating native atomic interoperability and advanced features on the **XRP Ledger (XRPL)** testnet.

## 📋 Overview

Global Liquidity Nexus is an educational testnet demo that showcases next-generation blockchain capabilities including:

- **KYC Credential Issuance** (XLS-70) - Issue verified know-your-customer credentials on-chain
- **Permissioned Domains** (XLS-80) - Create domains with credential-based access controls
- **Atomic Settlement** - Leverage XRPL escrow transactions for atomic payment paths
- **Multi-Signature Governance** - Set up multi-sig wallets for secure consensus-based transactions

## ✨ Features

### 1. Issue KYC Credential (XLS-70)
Issue cryptographic credentials linked to wallet addresses, enabling compliant transactions and access control across the network.

**Working Implementation:**
- Generate test wallets or import existing seeds
- Create CredentialCreate transactions on XRPL testnet
- Real transaction submission with hash tracking
- Credential expiration and type configuration

### 2. Create Permissioned Domain (XLS-80)
Establish domains that enforce credential requirements, allowing only KYC-verified participants to transact within that domain.

**Current Implementation:**
- Domain configuration with credential requirements
- AccountSet transactions storing domain data on-chain
- Hash generation for domain integrity
- Ready for future PermissionedDomainSet implementation

### 3. Atomic Settlement Path ⚡
Create escrowed payment paths that ensure atomicity—funds only transfer when all conditions are met.

**Working End-to-End Implementation:**
- Full XRPL EscrowCreate transaction building
- Conditional escrow with time locks and fulfillment conditions
- Real testnet transaction submission
- EscrowFinish workflow demonstration
- Transaction status tracking and history

### 4. Multi-Signature Governance
Guidance on setting up multi-signature wallets for distributed governance and enhanced security.

**Implementation:**
- Multi-sig wallet generation tools
- Signer configuration and quorum setup
- XUMM integration guidance

### 5. Mobile Wallet Integration 📱
One-click transaction creation with XUMM deep-linking for seamless mobile wallet signing.

**XUMM Integration Features:**
- Direct payload creation for mobile signing
- QR code generation for wallet scanning
- Deep-link support for XUMM app
- Payload status tracking and callbacks
- Compatible with all transaction types
- Security best practices documentation

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd GlobalLiquidityNexus
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env with your configuration
```

### XUMM Integration Setup (Optional)

For mobile wallet integration:

1. Get XUMM API credentials from [XUMM Developer Console](https://apps.xumm.dev/)
2. Add to your `.env` file:
```bash
XUMM_API_KEY=your_api_key
XUMM_API_SECRET=your_api_secret
```

## 🔄 Working End-to-End Flows

### Mobile Wallet Transaction Demo

1. **Configure XUMM**: Add API credentials to `.env` file
2. **Generate Payload**: Click "📲 Create via XUMM" on any transaction
3. **Scan QR Code**: Use XUMM app to scan the generated QR code
4. **Sign Transaction**: Approve the transaction in XUMM
5. **Verify**: Transaction is submitted to XRPL testnet

### Atomic Settlement Path Demo

1. **Generate Test Wallets**: Create two test wallets in the sidebar
2. **Fund Wallets**: Use the [XRP Testnet Faucet](https://xrpl.org/xrp-testnet-faucet.html) to get test XRP
3. **Create Escrow**: 
   - Go to "Atomic Settlement" tab
   - Enter destination address from second wallet
   - Set amount (e.g., 1 XRP) and time conditions
   - Click "Create Atomic Escrow"
4. **Verify Transaction**: Check transaction hash and status
5. **Finish Escrow**: Use second wallet to finish the escrow after finish time

### Credential Issuance Demo

1. **Generate Wallet**: Create or import a wallet
2. **Issue Credential**: 
   - Go to "Issue Credential" tab
   - Enter subject address and credential details
   - Click "Issue Credential"
3. **View Transaction**: Check the credential transaction on XRPL testnet

### Testing Transactions

- All transactions are submitted to XRPL testnet
- Transaction hashes are displayed for verification
- Use [XRP Explorer](https://testnet.xrpl.org/) to view transactions
- No real XRP value - only testnet tokens

## �️ Technical Implementation

### XRPL Integration
- **xrpl-py**: Official Python SDK for XRPL
- **Real Transactions**: All features submit actual transactions to testnet
- **Wallet Management**: Secure key generation and seed import
- **Transaction Building**: Proper XRPL transaction construction
- **Status Tracking**: Transaction hash storage and status monitoring

### Mobile Wallet Integration
- **xumm-sdk-py**: Official XUMM Python SDK for payload creation
- **Deep Linking**: Direct integration with XUMM mobile app
- **QR Code Generation**: Visual QR codes for easy scanning
- **Payload Management**: Secure payload creation and status tracking
- **Callback Support**: Transaction status updates via webhooks

### Key Components
- **CredentialCreate**: XLS-70 compliant credential issuance
- **EscrowCreate/EscrowFinish**: Atomic settlement with conditions
- **AccountSet**: Domain configuration storage
- **SignerListSet**: Multi-signature wallet setup guidance
- **XUMM Payloads**: Mobile wallet transaction signing

### Security Features
- Client-side transaction signing
- No private key storage on server
- Testnet-only operations
- Clear transaction previews before submission

## 📦 Dependencies

- **streamlit** - Web UI framework
- **xrpl-py** - XRPL Python client library
- **xumm-sdk-py** - XUMM wallet integration SDK
- **qrcode** - QR code generation
- **python-dotenv** - Environment variable management
- **requests** - HTTP client library
- **streamlit-option-menu** - Additional UI components

## ⚠️ Disclaimer

This is an **educational testnet demo**. 

- **No real value** - Uses XRPL testnet tokens only
- **Development only** - Not suitable for production
- **Educational purpose** - Designed to teach XRPL concepts

## 🔐 Security Notes

For real applications:
- Store private keys securely (never in code)
- Use hardware wallets for high-value transactions
- Implement proper KYC/AML procedures
- Audit smart contract logic thoroughly

## 📚 Resources

- [XRP Ledger Documentation](https://xrpl.org/)
- [XRPL Python Library](https://xrpl-py.readthedocs.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [XUMM SDK](https://xumm.dev/)

## 📝 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please follow standard git workflow and ensure code is well-documented.

---

**GLN Testnet Demo** • Explore the future of blockchain interoperability on XRPL
