# AstraSync Python SDK

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/AstraSyncAI/astrasync-python-sdk)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

Register and verify AI agents on the blockchain with AstraSync - the first decentralized AI agent registry.

## 🚀 Quick Start

```bash
pip install git+https://github.com/AstraSyncAI/astrasync-python-sdk.git
```

```python
from astrasync import AstraSync

# Initialize client
client = AstraSync(email="developer@example.com")

# Register an agent
result = client.register({
    "name": "My AI Assistant",
    "description": "A helpful AI agent for customer support",
    "owner": "ACME Corp",
    "capabilities": ["chat", "analysis", "problem-solving"]
})

print(f"Agent ID: {result['agentId']}")
print(f"Trust Score: {result['trustScore']}")  # API-assigned score
```

## 📋 Features

- **Universal Agent Detection**: Auto-detects agent protocol/format
- **Blockchain Registration**: Immutable record of agent identity (coming soon)
- **Trust Scoring**: API-assigned trust scores for verified agents
- **Simple Integration**: One SDK for all major AI agent frameworks
- **Production**: Get early access and shape the future

## 🤖 Supported Agent Formats

Currently supporting 17+ agent frameworks with auto-detection:
- Google ADK (Agent Development Kit)
- OpenAI Assistants API
- MCP (Model Context Protocol)
- AutoGPT
- Salesforce Agentforce
- LangChain
- CrewAI
- n8n Workflow Agents
- AgentStack (by AgentOps)
- Microsoft AutoGen
- Microsoft Semantic Kernel
- OpenAI Swarm
- Meta Llama Stack
- LlamaIndex Agents
- BabyAGI
- Mistral Agents (Le Chat)
- Amazon Bedrock Agents
- Letta (MemGPT)
- IBM ACP

### Google ADK (Agent Development Kit)
```python
# Schema-based agent
adk_agent = {
    "name": "ADK Assistant",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        }
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "response": {"type": "string"}
        }
    },
    "tools": ["search", "analyze", "summarize"],
    "model": "gemini-1.5-pro"
}

result = client.register(adk_agent)
```

### OpenAI Assistants
```python
openai_agent = {
    "model": "gpt-4",
    "name": "Customer Support Bot",
    "instructions": "You are a helpful customer support assistant.",
    "tools": [{"type": "code_interpreter"}, {"type": "retrieval"}],
    "description": "Handles customer inquiries and technical support"
}

result = client.register(openai_agent)
```

### MCP (Model Context Protocol)
```python
mcp_agent = {
    "protocol": "ai-agent",
    "name": "MCP Assistant",
    "description": "Multi-capability AI agent",
    "skills": [
        {"name": "search", "description": "Search the web"},
        {"name": "calculate", "description": "Perform calculations"}
    ]
}

result = client.register(mcp_agent)
```

### AutoGPT
```python
autogpt_agent = {
    "ai_name": "ResearchBot",
    "ai_role": "Research Assistant",
    "ai_goals": [
        "Research topics thoroughly",
        "Provide accurate information",
        "Cite sources"
    ]
}

result = client.register(autogpt_agent)
```

### Salesforce Agentforce
```python
agentforce_agent = {
    "agent_type": "External",
    "agent_template_type": "EinsteinServiceAgent",
    "label": "Einstein Support Agent",
    "topics": [
        {"label": "Customer Support"},
        {"label": "Technical Issues"}
    ]
}

result = client.register(agentforce_agent)
```

### LangChain
```python
# LangChain agent configuration
langchain_agent = {
    "name": "Research Assistant",
    "agent_type": "conversational",
    "llm": "gpt-4",
    "tools": ["search", "calculator", "code_interpreter"],
    "memory": {"type": "conversation_buffer", "k": 10},
    "prompt": "You are a helpful research assistant...",
    "description": "AI agent for research and analysis"
}

result = client.register(langchain_agent)

# Or use the LangChain-specific adapter
from astrasync.adapters.langchain import register_langchain

result = register_langchain(
    agent=langchain_agent,
    email="developer@example.com",
    owner="Research Team"
)

# Automatic registration with decorator
from astrasync.adapters.langchain import register_with_astrasync

@register_with_astrasync(email="dev@example.com", owner="My Company")
class MyLangChainAgent:
    def __init__(self):
        self.llm = "claude-3"
        self.tools = ["web_search", "calculator"]
        self.memory = {"type": "conversation_summary"}
```

### CrewAI
```python
# CrewAI agent configuration
crewai_agent = {
    "name": "Research Specialist",
    "role": "Senior Researcher",
    "goal": "Conduct thorough research and analysis",
    "backstory": "You are an experienced researcher with deep expertise in your field.",
    "tools": ["search_tool", "analysis_tool"],
    "memory": True,
    "llm": "gpt-4",
    "description": "Expert researcher for comprehensive analysis"
}

result = client.register(crewai_agent)

# CrewAI crew configuration
crew_config = {
    "name": "Research Team",
    "agents": [
        {"role": "Researcher", "goal": "Find information"},
        {"role": "Analyst", "goal": "Analyze findings"},
        {"role": "Writer", "goal": "Create reports"}
    ],
    "tasks": [
        {"description": "Research topic", "expected_output": "Research data"},
        {"description": "Analyze data", "expected_output": "Analysis report"},
        {"description": "Write report", "expected_output": "Final document"}
    ],
    "process": "sequential"
}

result = client.register(crew_config)

# Or use the CrewAI-specific adapter
from astrasync.adapters.crewai import register_crewai

result = register_crewai(
    agent=crewai_agent,
    email="developer@example.com",
    owner="Research Department"
)
```

### n8n
```python
# n8n AI Agent node configuration
n8n_agent = {
    "type": "n8n-nodes-langchain.agent",
    "name": "Customer Support AI",
    "parameters": {
        "systemPrompt": "You are a helpful customer support assistant.",
        "model": "gpt-4",
        "tools": ["search", "calculator", "knowledge_base"],
        "memory": {"type": "windowBuffer", "k": 10}
    }
}

result = client.register(n8n_agent)

# n8n workflow with AI agents
n8n_workflow = {
    "workflow": {
        "name": "AI Automation Workflow",
        "nodes": [
            {"type": "webhook", "name": "Trigger"},
            {"type": "n8n-nodes-langchain.agent", "name": "AI Agent"},
            {"type": "http", "name": "API Call"}
        ]
    }
}

result = client.register(n8n_workflow)
```

### AgentStack
```python
# AgentStack agent configuration
agentstack_agent = {
    "agent_name": "Research-Assistant",
    "system_prompt": "You are an expert research assistant...",
    "model": "gpt-4",
    "max_loops": 5,
    "autosave": True,
    "context_length": 100000,
    "dynamic_temperature_enabled": True,
    "tools": ["web_search", "document_analyzer"]
}

result = client.register(agentstack_agent)

# AgentStack swarm configuration
swarm_config = {
    "swarm_architecture": {
        "name": "Analysis-Swarm",
        "swarm_type": "ConcurrentWorkflow",
        "max_loops": 3
    },
    "agents": [
        {"agent_name": "Data-Collector", "system_prompt": "Gather data..."},
        {"agent_name": "Analyst", "system_prompt": "Analyze findings..."}
    ]
}

result = client.register(swarm_config)
```

### Microsoft AutoGen
```python
# AutoGen multi-agent configuration
autogen_config = {
    "name": "Research Team",
    "agents": [
        {"name": "Coder", "system_message": "Write clean code", "llm_config": {"model": "gpt-4"}},
        {"name": "Reviewer", "system_message": "Review code quality", "llm_config": {"model": "gpt-4"}}
    ],
    "code_execution": True,
    "max_round": 10
}

result = client.register(autogen_config)
```

### Microsoft Semantic Kernel
```python
# Semantic Kernel agent with plugins
sk_agent = {
    "name": "Enterprise Assistant",
    "kernel": {"model": "gpt-4"},
    "plugins": {
        "WebSearchPlugin": {"functions": ["search", "scrape"]},
        "MathPlugin": {"functions": ["calculate", "solve"]}
    },
    "memory": {"type": "semantic"},
    "planner": {"type": "sequential"}
}

result = client.register(sk_agent)
```

### OpenAI Swarm
```python
# Swarm agent with handoffs
swarm_agent = {
    "name": "Customer Service",
    "instructions": "Help customers professionally",
    "model": "gpt-4",
    "functions": ["check_order", "process_refund"],
    "handoffs": ["technical_support", "billing"]
}

result = client.register(swarm_agent)
```

### Meta Llama Stack
```python
# Llama Stack agent with tools
llamastack_agent = {
    "name": "Code Assistant",
    "agent_config": {
        "model": "llama-3.1-70b",
        "system_prompt": "You are an expert programmer"
    },
    "tools": ["code_interpreter", "web_search"],
    "safety": {"shields": ["prompt_guard", "llama_guard"]}
}

result = client.register(llamastack_agent)
```

### LlamaIndex Agents
```python
# LlamaIndex multi-agent service
llamaindex_agent = {
    "name": "Query Processor",
    "agent_service": {
        "service_name": "query_service",
        "host": "localhost",
        "port": 8080
    },
    "orchestrator": {
        "agents": ["research", "analysis", "synthesis"]
    },
    "message_queue": {"type": "rabbitmq"}
}

result = client.register(llamaindex_agent)
```

### BabyAGI
```python
# BabyAGI autonomous agent
babyagi_agent = {
    "name": "Research AGI",
    "objective": "Research and summarize AI developments",
    "initial_task": "Search for latest AI papers",
    "vectorstore": {"type": "pinecone"},
    "max_iterations": 10
}

result = client.register(babyagi_agent)
```

### Mistral Agents
```python
# Mistral AI agent with Le Chat
mistral_agent = {
    "name": "Assistant",
    "model": "mistral-large",
    "system_prompt": "You are a helpful assistant",
    "functions": ["search", "calculate", "analyze"],
    "json_mode": True,
    "safe_mode": True
}

result = client.register(mistral_agent)
```

### Amazon Bedrock Agents
```python
# Bedrock managed agent
bedrock_agent = {
    "agent_name": "Enterprise Bot",
    "foundation_model": "anthropic.claude-v2",
    "instruction": "Help users with enterprise tasks",
    "action_groups": [
        {
            "name": "OrderManagement",
            "api_schema": {"source": "s3://schemas/orders.json"},
            "action_group_executor": {"lambda": "arn:aws:lambda:..."}
        }
    ],
    "knowledge_bases": [
        {"id": "KB-001", "description": "Product documentation"}
    ],
    "guardrails": {"guardrail_id": "GR-001"}
}

result = client.register(bedrock_agent)
```

### More Frameworks
- **Letta (MemGPT)**: Memory-augmented agents
- **IBM ACP**: Agent Communication Protocol
- **SuperAGI**: Enterprise autonomous agent framework (coming soon)
- **Vertex AI**: Google Cloud AI agents (coming soon)
- **Dify**: Visual AI workflow builder (coming soon)

## 📊 Registration Response

All registrations return a consistent response format:

```python
{
    "agentId": "TEMP-1706439245-X7K9M2",      # Unique identifier
    "status": "registered",                    # Registration status
    "trustScore": "TEMP-95%",                 # API-assigned trust score
    "blockchain": {
        "status": "pending",
        "message": "Blockchain registration queued"
    },
    "message": "Agent registered successfully"
}
```

**Note**: During production, all agents receive a temporary ID (`TEMP-XXX`) and placeholder trust score (`TEMP-95%`). Production IDs and dynamic trust scores will be assigned after account creation.

## 🔍 Agent Detection

The SDK automatically detects your agent's format:

```python
from astrasync import detect_agent_type

agent_data = {
    "model": "gpt-4",
    "instructions": "...",
    "tools": [...]
}

agent_type = detect_agent_type(agent_data)
print(f"Detected type: {agent_type}")  # Output: "openai"
```

## 🛡️ Trust Scores

Trust scores are assigned by the AstraSync API based on:
- Agent verification status
- Developer verification
- Capability declarations
- Compliance with standards

**Important**: As of v0.2.1, the SDK uses trust scores exclusively from the API. Local calculation has been removed to ensure consistency across all registration methods.

## 🔧 Advanced Usage

### Custom Owner Information
```python
result = client.register(agent_data, owner="My Company Inc.")
```

### Verify Existing Registration
```python
verification = client.verify("TEMP-1706439245-X7K9M2")
print(f"Agent exists: {verification['exists']}")
```

### Normalize Agent Data
```python
from astrasync import normalize_agent_data

# Convert any format to standard structure
normalized = normalize_agent_data(raw_agent_data)
```

## 📦 Installation Options

### From GitHub (Recommended)
```bash
pip install git+https://github.com/AstraSyncAI/astrasync-python-sdk.git
```

### From PyPI (Coming Soon)
```bash
pip install astrasyncai
```

### Development Installation
```bash
git clone https://github.com/AstraSyncAI/astrasync-python-sdk.git
cd astrasync-python-sdk
pip install -e .
```

## 🌟 Why AstraSync?

- **First-Mover**: First blockchain registry for AI agents
- **Compliance Ready**: Built for upcoming AI regulations
- **Universal Support**: One SDK for all major agent frameworks
- **Developer Friendly**: Simple API, comprehensive docs
- **Future Proof**: Preparing for the autonomous agent economy

## 🚧 Production Status

This SDK is in active development. Current limitations:

- ✅ Agent registration working
- ✅ Auto-detection of 12+ agent formats (including LangChain, CrewAI, n8n, and AgentStack)
- ✅ API-assigned trust scores
- 🔄 Blockchain integration (in progress)
- 🔄 Dynamic trust scoring (coming with accounts)
- 🔄 Production agent IDs (after account creation)

## 📚 Documentation

- [API Reference](https://docs.astrasync.ai)
- [Integration Guides](https://docs.astrasync.ai/guides)
- [Agent Formats](https://docs.astrasync.ai/formats)
- [Trust Score Methodology](https://docs.astrasync.ai/trust)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 Changelog

### v0.2.5 (Latest)
- **NEW**: Added 8 major AI agent frameworks:
  - Microsoft AutoGen (multi-agent conversations with code execution)
  - Microsoft Semantic Kernel (enterprise AI orchestration with plugins)
  - OpenAI Swarm (lightweight agent orchestration with handoffs)
  - Meta Llama Stack (Llama agents with safety shields)
  - LlamaIndex Agents (distributed multi-agent microservices)
  - BabyAGI (autonomous task management and prioritization)
  - Mistral Agents (Le Chat with JSON mode and function calling)
  - Amazon Bedrock Agents (AWS managed agents with RAG)
- **FIXED**: Dictionary detection issue affecting all adapters
- **IMPROVED**: Trust scoring with framework-specific bonuses
- **ADDED**: Comprehensive test coverage for all new frameworks
### v0.2.4
- **NEW**: Added n8n workflow automation support
- **NEW**: Added AgentStack (by AgentOps) support
- **NEW**: Support for n8n AI agent nodes and workflows
- **NEW**: Support for AgentStack agents, swarms, and YAML configs
- **ADDED**: Examples for both n8n and AgentStack integrations

### v0.2.3
- **NEW**: Added CrewAI support with auto-detection
- **NEW**: Support for CrewAI agents, crews, and multi-agent teams
- **NEW**: CrewAI-specific adapter with decorator support
- **ADDED**: Comprehensive CrewAI examples

### v0.2.2
- **NEW**: Added LangChain support with auto-detection
- **NEW**: LangChain-specific adapter with decorator support
- **IMPROVED**: Enhanced agent detection logic
- **ADDED**: Comprehensive LangChain examples

### v0.2.1
- **BREAKING**: Trust scores now come exclusively from API
- Removed local trust score calculation
- Simplified migration path for account linking
- All agents receive API-assigned trust scores

### v0.2.0
- Added Google ADK support
- Added Agentforce support
- Improved agent detection
- Enhanced error handling

### v0.1.0
- Initial release
- Support for MCP, Letta, ACP, OpenAI, AutoGPT
- Basic registration and verification

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Website**: [astrasync.ai](https://astrasync.ai)
- **Documentation**: [docs.astrasync.ai](https://docs.astrasync.ai)
- **API Status**: [status.astrasync.ai](https://status.astrasync.ai)
- **GitHub**: [github.com/AstraSyncAI](https://github.com/AstraSyncAI)

## 💬 Support

- **Discord**: [Join our community](https://discord.gg/astrasync)
- **Email**: developers@astrasync.ai
- **Issues**: [GitHub Issues](https://github.com/AstraSyncAI/astrasync-python-sdk/issues)

---

**AstraSync** - Building trust infrastructure for the AI agent economy.