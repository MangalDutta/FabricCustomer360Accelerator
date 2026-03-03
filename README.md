# Customer 360 Conversational Analytics Solution Accelerator

[![Deploy](https://img.shields.io/badge/Deploy-Quick%20Start-blue)](../../actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Solution Overview

An enterprise-grade **AI-Powered Customer 360 Conversational Analytics Platform** that enables business users to ask natural language questions about customer data using **Microsoft Fabric Data Agents** and **Azure AI Foundry**.

### Business Problem

- Customer data scattered across systems
- Sales teams need instant customer insights
- Executives ask ad-hoc analytical questions
- Long dependency on BI teams for every query
- No conversational access to enterprise data

### Solution

Transform traditional BI dashboards into an AI-powered conversational data platform using:
- **Microsoft Fabric Lakehouse** for unified customer data
- **Fabric Data Agent** for natural language to SQL/DAX translation
- **Azure AI Foundry Agent** for intelligent orchestration
- **React Chat Interface** for conversational queries
- **Embedded Power BI** for visual analytics

---

## 🏗️ Architecture

```
Customer CSV → Fabric Lakehouse → Delta Table → Fabric Data Agent
                                                      ↓
                                           Azure AI Foundry Agent
                                                      ↓
                                              Backend FastAPI
                                                      ↓
                                   React Chat App + Embedded Power BI
```

### Components Deployed

**Azure Infrastructure:**
- Azure Container Registry (Private, RBAC-only)
- App Service Plan (Linux)
- Backend App Service (Python FastAPI)
- Frontend App Service (React)
- Key Vault (RBAC-enabled)
- Virtual Network with subnets
- User-assigned Managed Identities
- Application Insights (optional)

**Microsoft Fabric:**
- Lakehouse with Customer360 table
- Fabric Data Agent bound to lakehouse

**Azure AI Foundry:**
- Agent with Fabric tool integration

---

## 🚀 Quick Deploy

### Prerequisites

1. **Azure Subscription** with:
   - Contributor access to a resource group
   - Ability to create Entra app registrations

2. **Microsoft Fabric** with:
   - Fabric capacity or trial enabled
   - Workspace created (note the display name)

3. **Azure AI Foundry** with:
   - AI Foundry project created
   - Supported region (e.g., East US, West Europe, Central India)

4. **GitHub Account** with ability to fork repos

### Deployment Steps

#### Step 1: Fork This Repository

1. Click **Fork** in the top-right corner
2. Choose your GitHub organization/account
3. Click **Create fork**

#### Step 2: Configure Azure OIDC Authentication

1. **Create Entra App Registration:**

```cmd
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"

az ad app create --display-name "github-customer360-deploy"
```

2. **Get the Client ID:**

```cmd
az ad app list --display-name "github-customer360-deploy" --query "[0].appId" -o tsv
```

Copy this value as `<CLIENT_ID>`.

3. **Create Service Principal:**

```cmd
az ad sp create --id "<CLIENT_ID>"
```

4. **Assign Role to Resource Group:**

```cmd
az role assignment create \
  --assignee "<CLIENT_ID>" \
  --role "Contributor" \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP_NAME>"
```

5. **Add Federated Credential:**

- Go to **Azure Portal** → **Entra ID** → **App registrations**
- Find `github-customer360-deploy`
- Go to **Certificates & secrets** → **Federated credentials**
- Click **Add credential**
- Select **GitHub Actions**
- Fill in:
  - **Organization**: Your GitHub username/org
  - **Repository**: `<YourOrg>/FabricCustomer360Accelerator`
  - **Entity type**: Branch
  - **Branch**: `main`
  - **Name**: `customer360-main`

#### Step 3: Create Resource Group

```cmd
az group create \
  --name "rg-customer360-dev" \
  --location "centralindia"
```

*(Change region as needed)*

#### Step 4: Create Fabric Workspace

1. Go to **Microsoft Fabric Portal** (https://app.fabric.microsoft.com)
2. Create a new workspace (e.g., "Customer360Workspace")
3. Note the exact **display name**

#### Step 5: Run Quick Deploy Workflow

1. Go to your forked repo → **Actions**
2. Select **"Quick Deploy Customer360"**
3. Click **Run workflow**
4. Fill in the parameters:

| Parameter | Example Value | Description |
|-----------|---------------|-------------|
| `azure_subscription_id` | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | Your Azure subscription ID |
| `azure_tenant_id` | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | Your Azure tenant ID |
| `azure_client_id` | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | Entra app client ID from Step 2 |
| `resource_group` | `rg-customer360-dev` | Resource group name |
| `location` | `centralindia` | Azure region |
| `base_name` | `cust360` | Base name for resources |
| `env` | `dev` | Environment (dev/test/prod) |
| `workspace_name` | `Customer360Workspace` | Fabric workspace display name |
| `lakehouse_name` | `Customer360Lakehouse` | Lakehouse to create |
| `table_name` | `Customer360` | Table name for data |
| `dataagent_name` | `Customer360Agent` | Data Agent name |

5. Click **Run workflow**

**Deployment takes ~15-20 minutes.**

#### Step 6: Configure Azure AI Foundry Agent

After the pipeline completes:

1. Check the workflow logs for the **Data Agent ID** output
2. Go to **Azure AI Foundry Portal**
3. Open your Agent
4. Configure **Fabric tool**:
   - Workspace ID: (from Fabric portal)
   - Data Agent ID: (from workflow logs)
5. Get Agent API key/token
6. Store in Key Vault as secret `AGENT-TOKEN`:

```cmd
az keyvault secret set \
  --vault-name "<KV_NAME>" \
  --name "AGENT-TOKEN" \
  --value "<YOUR_FOUNDRY_AGENT_TOKEN>"
```

#### Step 7: Test the Solution

1. Get frontend URL from Azure Portal:
   - Go to App Service `<base_name>-<env>-frontend`
   - Copy the URL

2. Open in browser and ask:
   - "Top 5 customers by LifetimeValue in Maharashtra"
   - "Which customers are high churn risk?"
   - "Show revenue trend for Karnataka"

---

## 💡 Business Use Cases

### Conversational Analytics
Business users ask natural language questions without SQL/DAX knowledge.

### Customer Risk Intelligence
AI identifies churn risk, revenue trends, and customer health scores.

### Executive Decision Acceleration
Instant answers instead of waiting for BI reports.

### Unified Data Governance
All queries respect Fabric workspace RBAC and security.

---

## 📊 Sample Questions

- "Top 5 customers by LifetimeValue in Maharashtra"
- "Which customers in Karnataka are high churn risk?"
- "Show customers with MonthlyRevenue above 20000"
- "Count customers by State"
- "Average ChurnRiskScore by Segment"

---

## 🔐 Security Features

- **No hardcoded secrets** - All credentials in Key Vault
- **OIDC authentication** - GitHub Actions uses federated identity
- **Managed Identity** - App Services access ACR and Key Vault via MI
- **Private networking** - ACR and Key Vault use private endpoints
- **RBAC everywhere** - Least privilege access control

---

## 📚 Documentation

- [Architecture Details](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Business Scenarios](docs/BUSINESS_SCENARIOS.md)

---

## 🤝 Contributing

This is a Microsoft-inspired solution accelerator. Contributions welcome via pull requests.

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🆘 Support

For issues, please open a GitHub issue in this repository.

---

## 🙏 Acknowledgments

Inspired by:
- [Unified Data Foundation with Fabric Solution Accelerator](https://github.com/microsoft/unified-data-foundation-with-fabric-solution-accelerator)
- [Agentic Applications for Unified Data Foundation](https://github.com/microsoft/agentic-applications-for-unified-data-foundation-solution-accelerator)
