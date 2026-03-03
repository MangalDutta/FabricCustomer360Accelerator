#!/usr/bin/env python3
"""
Fabric Customer360 Setup Automation Script

This script automates the complete Fabric setup:
1. Locates the Fabric workspace by name
2. Creates a Lakehouse (if not exists)
3. Uploads customer360.csv to OneLake
4. Creates a Delta table from CSV
5. Creates a Fabric Data Agent bound to the table
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from azure.identity import DefaultAzureCredential

# Fabric API constants
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
FABRIC_BASE_URL = "https://api.fabric.microsoft.com/v1"


def get_fabric_token() -> str:
    """Get Fabric API token using DefaultAzureCredential"""
    credential = DefaultAzureCredential()
    token = credential.get_token(FABRIC_SCOPE)
    return token.token


def fabric_request(method: str, path: str, token: str, **kwargs) -> requests.Response:
    """Make authenticated request to Fabric REST API"""
    url = f"{FABRIC_BASE_URL}{path}"
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    resp = requests.request(method, url, headers=headers, **kwargs)

    if not resp.ok:
        print(f"❌ Fabric API error: {method} {path}")
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.text}")
        raise RuntimeError(f"Fabric API {method} {path} failed: {resp.status_code}")

    return resp


def find_workspace_id(workspace_name: str, token: str) -> str:
    """Find Fabric workspace by display name"""
    print(f"🔍 Looking for workspace: {workspace_name}")

    resp = fabric_request("GET", "/workspaces", token)
    data = resp.json()

    for workspace in data.get("value", []):
        if workspace.get("displayName") == workspace_name:
            ws_id = workspace["id"]
            print(f"✓ Found workspace: {workspace_name} (ID: {ws_id})")
            return ws_id

    raise RuntimeError(f"Workspace '{workspace_name}' not found. Please create it first.")


def ensure_lakehouse(workspace_id: str, lakehouse_name: str, token: str) -> str:
    """Create lakehouse if it doesn't exist, return lakehouse ID"""
    print(f"🏗️  Checking lakehouse: {lakehouse_name}")

    # List existing lakehouses
    resp = fabric_request("GET", f"/workspaces/{workspace_id}/items?type=Lakehouse", token)
    items = resp.json().get("value", [])

    for item in items:
        if item.get("displayName") == lakehouse_name:
            lh_id = item["id"]
            print(f"✓ Lakehouse already exists: {lakehouse_name} (ID: {lh_id})")
            return lh_id

    # Create new lakehouse
    print(f"📦 Creating lakehouse: {lakehouse_name}")
    payload = {"displayName": lakehouse_name}
    resp = fabric_request("POST", f"/workspaces/{workspace_id}/lakehouses", token, json=payload)
    lakehouse = resp.json()
    lh_id = lakehouse["id"]
    print(f"✓ Created lakehouse: {lakehouse_name} (ID: {lh_id})")
    return lh_id


def upload_csv_to_lakehouse(
    workspace_id: str, 
    lakehouse_id: str, 
    csv_path: Path, 
    token: str
) -> None:
    """Upload CSV file to lakehouse Files area"""
    print(f"📤 Uploading CSV: {csv_path.name}")

    # Note: Actual file upload would use OneLake APIs or Fabric's file upload endpoint
    # This is simplified - in production you'd use the proper OneLake path
    with csv_path.open("rb") as f:
        files = {"file": (csv_path.name, f, "text/csv")}

        # Upload to /Files area (adjust endpoint based on actual Fabric API)
        upload_url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/lakehouses/{lakehouse_id}/files/{csv_path.name}"
        headers = {"Authorization": f"Bearer {token}"}

        resp = requests.put(upload_url, headers=headers, files=files)
        if resp.ok:
            print(f"✓ Uploaded: {csv_path.name}")
        else:
            print(f"⚠️  Upload may have failed (status {resp.status_code})")


def create_table_from_csv(
    workspace_id: str,
    lakehouse_id: str,
    table_name: str,
    csv_file_name: str,
    token: str
) -> None:
    """Create Delta table from CSV file in lakehouse"""
    print(f"📊 Creating table: {table_name}")

    payload = {
        "source": {
            "type": "csv",
            "path": f"/Files/{csv_file_name}"
        },
        "target": {
            "type": "table",
            "name": table_name
        },
        "mode": "overwrite"
    }

    resp = fabric_request(
        "POST",
        f"/workspaces/{workspace_id}/lakehouses/{lakehouse_id}:load",
        token,
        json=payload
    )

    print(f"✓ Created table: {table_name}")


def ensure_data_agent(
    workspace_id: str,
    dataagent_name: str,
    lakehouse_id: str,
    table_name: str,
    token: str
) -> str:
    """Create Fabric Data Agent bound to lakehouse table"""
    print(f"🤖 Creating Data Agent: {dataagent_name}")

    definition = {
        "dataSources": [
            {
                "type": "lakehouse_tables",
                "workspaceId": workspace_id,
                "itemId": lakehouse_id,
                "displayName": "Customer360 Lakehouse",
                "elements": [
                    {
                        "display_name": table_name,
                        "type": "lakehouse_tables.table",
                        "is_selected": True
                    }
                ],
                "dataSourceInstructions": "Use this lakehouse for customer 360 analytics. "
                                           "Answer questions about customer lifetime value, churn risk, and revenue trends."
            }
        ],
        "userDescription": "AI agent for Customer 360 conversational analytics over lakehouse data."
    }

    payload = {
        "displayName": dataagent_name,
        "description": "Customer 360 Data Agent for conversational analytics",
        "definition": definition
    }

    resp = fabric_request(
        "POST",
        f"/workspaces/{workspace_id}/DataAgents",
        token,
        json=payload
    )

    data_agent = resp.json()
    da_id = data_agent["id"]
    print(f"✓ Created Data Agent: {dataagent_name} (ID: {da_id})")
    return da_id


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Automate Fabric Customer360 setup: workspace, lakehouse, table, data agent"
    )
    parser.add_argument("--workspace_name", required=True, help="Fabric workspace display name")
    parser.add_argument("--lakehouse_name", required=True, help="Lakehouse name")
    parser.add_argument("--csv_path", required=True, help="Path to customer360.csv")
    parser.add_argument("--table_name", required=True, help="Table name for data")
    parser.add_argument("--dataagent_name", required=True, help="Data Agent name")

    args = parser.parse_args(argv)

    print("=" * 60)
    print("🚀 Fabric Customer360 Setup Starting")
    print("=" * 60)

    try:
        # Get auth token
        print("🔐 Authenticating with Fabric...")
        token = get_fabric_token()
        print("✓ Authentication successful")

        # Find workspace
        workspace_id = find_workspace_id(args.workspace_name, token)

        # Create lakehouse
        lakehouse_id = ensure_lakehouse(workspace_id, args.lakehouse_name, token)

        # Upload CSV
        csv_path = Path(args.csv_path).resolve()
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        upload_csv_to_lakehouse(workspace_id, lakehouse_id, csv_path, token)

        # Create table
        create_table_from_csv(
            workspace_id,
            lakehouse_id,
            args.table_name,
            csv_path.name,
            token
        )

        # Create Data Agent
        dataagent_id = ensure_data_agent(
            workspace_id,
            args.dataagent_name,
            lakehouse_id,
            args.table_name,
            token
        )

        # Output summary
        print()
        print("=" * 60)
        print("✅ Fabric Customer360 Setup Complete!")
        print("=" * 60)

        result = {
            "workspace_id": workspace_id,
            "lakehouse_id": lakehouse_id,
            "dataagent_id": dataagent_id,
            "table_name": args.table_name
        }

        print(json.dumps(result, indent=2))
        print()
        print("📝 Next steps:")
        print("   1. Configure Azure AI Foundry Agent")
        print("   2. Set Fabric tool connection to Data Agent ID above")
        print("   3. Store Agent token in Key Vault")
        print("=" * 60)

    except Exception as ex:
        print(f"\n❌ Error: {ex}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
