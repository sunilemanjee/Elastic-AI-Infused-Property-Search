# Elastic AI-Infused Property Search

A powerful property search application that combines Elasticsearch with AI capabilities, allowing users to search for properties using natural language queries.

## Features

- **Dual LLM Support**: Choose between:
  - Azure OpenAI: For production-grade AI capabilities
  - Local LLM (via LM Studio): For privacy-focused or offline usage
- **Intelligent Query Processing**: Leverages LLM functions to understand query intent and detect entities, then dynamically generates precise Elasticsearch queries using search templates
- **Elasticsearch Integration**: Efficient property search and filtering
- **Real-time Results**: Get instant property matches based on your criteria
- **Interactive UI**: User-friendly interface with clear model selection and search capabilities
- **ELSER Model Management**: 
  - "Wake Elser" button for serverless deployments
  - Automatically wakes up the default ELSER model if it has scaled down due to inactivity
  - Only required when using the default ELSER model in serverless deployments
  - Not needed for non-default ELSER model deployments

## Prerequisites

- Python 3.11 or higher
- Elasticsearch instance
- One of the following:
  - Azure OpenAI account and credentials, or
  - LM Studio with a compatible model (e.g., Qwen2.5-7B-Instruct)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Elastic-AI-Infused-Property-Search.git
cd Elastic-AI-Infused-Property-Search
```

2. Create and activate a virtual environment:
```bash
python3.11 -m venv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:

For Azure OpenAI:
```bash
# Edit setenv.sh with your Azure OpenAI credentials
source setenv.sh
```

For Local LLM:
- Install and start LM Studio
- Load your preferred model (e.g., Qwen2.5-7B-Instruct)
- Start the local server in LM Studio

## Usage

1. Start the application:
```bash
chainlit run src/app.py
```

2. Open your browser and navigate to `http://localhost:8000`

3. Choose your preferred LLM:
   - Azure OpenAI: For production-grade AI capabilities
   - Local LLM: For privacy-focused or offline usage

4. Start searching for properties using natural language queries like:
   - "Find apartments in New York under $500,000"
   - "Show me 3-bedroom houses in San Francisco with a pool"
   - "What are the most expensive properties in Los Angeles?"

## Configuration

### Azure OpenAI Setup
1. Create an Azure OpenAI resource
2. Get your API key and endpoint
3. Update `setenv.sh` with your credentials:
```
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_key
OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_MODEL=your_model
```

### Local LLM Setup
1. Download and install [LM Studio](https://lmstudio.ai/)
2. Download a compatible model (e.g., Qwen2.5-7B-Instruct)
3. Load the model in LM Studio
4. Start the local server (default: http://localhost:1234)

### ELSER Model Configuration
1. For serverless deployments using the default ELSER model:
   - The model will scale down to zero after 10+ minutes of inactivity
   - Use the "Wake Elser" button to reactivate the model when needed
   - This helps save costs in serverless environments
2. For non-default ELSER model deployments:
   - The "Wake Elser" button is not required
   - The model remains active and ready for use

### Local LLM Requirements
- If using the local LLM option, your model must support function calling/tools
- The model should be able to:
  - Parse and understand tool definitions in JSON format
  - Generate structured responses that can be parsed as tool calls
  - Handle multiple tools in a single conversation
- Recommended models that support tools:
  - Qwen 2.5 7B Instruct (default)
  - Llama 2 70B Chat
  - Mistral 7B Instruct
  - Any other model that supports function calling/tools
- The model should be running locally via LM Studio or a similar inference server
- Set the `LOCAL_LLM_MODEL` environment variable to your model's name in `setenv.sh`

## Architecture

The application uses a modular architecture:
- **Frontend**: Chainlit-based UI with model selection and chat interface
- **LLM Layer**: Supports both Azure OpenAI and local models via LM Studio
- **Intelligent Query Layer**: 
  - LLM functions for query intent understanding and entity detection
  - Dynamic query generation using Elasticsearch search templates
  - Precise parameter extraction and mapping to schema
- **Search Engine**: Elasticsearch for efficient property search
- **MCP Integration**: Model Control Protocol for tool calling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
