# AstraSync Test Suite

This directory contains all tests for the AstraSync Python SDK.

## Structure

- `integration/` - Integration tests for each supported AI agent framework
  - `test_autogen_integration.py` - Microsoft AutoGen adapter tests
  - `test_babyagi_integration.py` - BabyAGI adapter tests
  - `test_bedrock_agents_integration.py` - Amazon Bedrock adapter tests
  - `test_crewai_integration.py` - CrewAI adapter tests
  - `test_langchain_integration.py` - LangChain adapter tests
  - `test_llamaindex_agents_integration.py` - LlamaIndex adapter tests
  - `test_llamastack_integration.py` - Meta Llama Stack adapter tests
  - `test_mistral_agents_integration.py` - Mistral Agents adapter tests
  - `test_n8n_agentstack.py` - n8n and AgentStack adapter tests
  - `test_semantic_kernel_integration.py` - Semantic Kernel adapter tests
  - `test_swarm_integration.py` - OpenAI Swarm adapter tests
  - `test_all_protocols.py` - Cross-protocol tests
  - `test_api_trust_scores.py` - Trust score calculation tests

## Running Tests

To run all tests:
```bash
python -m pytest tests/
```

To run a specific test file:
```bash
python tests/integration/test_langchain_integration.py
```

To run with coverage:
```bash
python -m pytest tests/ --cov=astrasync
```