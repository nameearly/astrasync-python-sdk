#!/usr/bin/env python3
"""
Salesforce Agentforce + AstraSync Integration Example

This example shows how to automatically register Agentforce agents
with AstraSync for blockchain-based compliance tracking.
"""

import json
from astrasync import AstraSync
from astrasync.adapters.agentforce import (
    register_agentforce, 
    register_agentforce_deployment,
    AgentforceAdapter
)

# Example 1: Register a JSON-based Agentforce agent
print("=" * 60)
print("Example 1: Registering JSON-based Agentforce agent")
print("=" * 60)

agentforce_json = {
    "name": "Customer Service Excellence Agent",
    "description": "AI Agent for premium customer support with compliance tracking",
    "agent_type": "External",
    "agent_template_type": "EinsteinServiceAgent",
    "company_name": "AcmeCorp",
    "domain": "Customer Service",
    "sample_utterances": [
        "Check my order status",
        "I need help with my account",
        "File a complaint",
        "Request a refund"
    ],
    "variables": [
        {
            "name": "customer_id",
            "developer_name": "customer_id",
            "label": "Customer ID",
            "data_type": "Text",
            "visibility": "Internal",
            "var_type": "conversation"
        }
    ],
    "system_messages": [
        {
            "message": "You are a helpful customer service agent.",
            "msg_type": "system"
        },
        {
            "message": "Always maintain customer privacy and comply with GDPR.",
            "msg_type": "system"
        }
    ],
    "topics": ["order_management", "account_support", "complaints", "refunds"]
}

result = register_agentforce(agentforce_json, email="admin@acmecorp.com")
print(f"✅ Registered with AstraSync Production!")
print(f"   AstraSync ID: {result['agentId']}")
print(f"   Trust Score: {result['trustScore']} (production calculation)")
print(f"   Note: This is a temporary ID. Create an AstraSync account at")
print(f"         https://astrasync.ai to convert to permanent blockchain registration")
print(f"   Verification URL: https://astrasync.ai/verify/{result['agentId']}")

# Example 2: Register after Salesforce deployment
print("\n" + "=" * 60)
print("Example 2: Register after Salesforce deployment")
print("=" * 60)

# This would come from agentforce.create(agent)
deployment_result = {
    "id": "0Ai5f000000CaRbCAK",
    "deployResult": {
        "status": "Succeeded"
    },
    "agent": agentforce_json
}

result = register_agentforce_deployment(deployment_result, email="admin@acmecorp.com")
print(f"✅ Deployment registered in AstraSync Production!")
print(f"   Salesforce ID: {deployment_result['id']}")
print(f"   AstraSync ID: {result['agentId']}")
print(f"   Status: {result['deployment_status']}")
print(f"   Note: Blockchain registration pending account creation")

# Example 3: Using the decorator pattern (if using SDK programmatically)
print("\n" + "=" * 60)
print("Example 3: Auto-registration with decorator")
print("=" * 60)
print("   (Decorator example requires Agentforce SDK with proper initialization)")
print("   See documentation for SDK integration patterns")

# Example 4: Financial Services Use Case
print("\n" + "=" * 60)
print("Example 4: Financial Services Compliance")
print("=" * 60)

banking_agent = {
    "name": "Loan Processing Agent",
    "description": "Automated loan application processing with full audit trail",
    "agent_type": "Internal",
    "agent_template_type": "EinsteinServiceAgent",
    "company_name": "MegaBank Financial",
    "domain": "Banking",
    "sample_utterances": [
        "Check loan application status",
        "Submit loan documents",
        "Calculate loan eligibility",
        "Schedule loan officer meeting"
    ],
    "variables": [
        {
            "name": "application_id",
            "developer_name": "application_id",
            "label": "Application ID",
            "data_type": "Text",
            "visibility": "Internal",
            "var_type": "conversation"
        },
        {
            "name": "compliance_level",
            "developer_name": "compliance_level",
            "label": "Compliance Level",
            "data_type": "Text",
            "visibility": "Internal",
            "var_type": "conversation"
        }
    ],
    "system_messages": [
        {
            "message": "You must comply with all banking regulations including KYC and AML.",
            "msg_type": "system"
        },
        {
            "message": "Every decision must be traceable and auditable.",
            "msg_type": "system"
        }
    ],
    "topics": ["loan_processing", "kyc_verification", "risk_assessment", "compliance"]
}

result = register_agentforce(banking_agent, email="compliance@megabank.com")
print(f"✅ Banking agent registered in Production!")
print(f"   AstraSync ID: {result['agentId']}")
print(f"   Trust Score: {result['trustScore']}")
print(f"   Preview Dashboard: https://astrasync.ai/production/{result['agentId']}")
print(f"\n💡 When you create an AstraSync account, this agent will be")
print(f"   permanently registered on blockchain with full audit trail!")

print("\n" + "=" * 60)
print("Integration complete! Your Agentforce agents now have")
print("production IDs that will convert to blockchain identity.")
print("=" * 60)
