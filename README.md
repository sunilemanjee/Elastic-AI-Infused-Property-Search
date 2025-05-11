# Elastic AI Infused Property Search

An intelligent property search system that combines Elasticsearch's powerful search capabilities with Azure OpenAI's natural language processing to create a conversational property search experience.

## Demo




Watch a demo of the property search system in action:

https://github.com/user-attachments/assets/df498631-fb16-4ba5-b1fd-c14670213d73

https://github.com/user-attachments/assets/562cbc97-d785-4d01-8561-1c4c10a3b4c9



This demo showcases:
- Natural language property search
- Location-based search capabilities
- Real-time property recommendations
- Interactive chat interface

## Features

- Interactive chat interface powered by Chainlit
- Azure OpenAI API integration for natural language understanding
- Elasticsearch for powerful property search
- Real-time streaming responses
- Dynamic query generation
- Location-based search capabilities

## Data Ingestion

Before running the demo, you need to ingest sample property data into your Elasticsearch instance. The data ingestion scripts and detailed instructions can be found in the [Elastic Python MCP Server repository](https://github.com/sunilemanjee/Elastic-Python-MCP-Server/tree/main/data-ingestion).

Follow these steps:
1. Clone the MCP Server repository
2. Navigate to the data-ingestion directory
3. Follow the instructions in the README to ingest the sample property data
4. Verify the data has been successfully ingested before proceeding with the demo

## Architecture

The system consists of four main components:

1. **Chainlit UI Layer**
   - Interactive chat interface
   - Real-time message streaming
   - Property result display
   - Image visualization

2. **Azure OpenAI Integration**
   - Natural language processing
   - Entity detection
   - Context management
   - Response generation

3. **Elasticsearch Backend**
   - Property data storage
   - Search templates
   - Geo-spatial search
   - Result ranking

4. **MCP Server**
   - Tool orchestration
   - API integration
   - Response processing
   - Query generation

## Prerequisites

- Python 3.8 or higher
- Azure OpenAI API access
- Elasticsearch Serverless instance
- Poperty data (see Data Ingestion section above)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/elastic-ai-property-search.git
cd elastic-ai-property-search
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:

   **Option 1: Using setenv.sh (Recommended)**
   ```bash
   # Copy the template file
   cp setenv.sh.template setenv.sh
   
   # Edit setenv.sh with your credentials
   # IMPORTANT: Never commit setenv.sh to version control!
   nano setenv.sh  # or use your preferred editor
   
   # Source the environment variables
   source setenv.sh
   ```

   **Option 2: Manual Setup**
   Create an `azure.env` file with the following content:
   ```env
   AZURE_OPENAI_MODEL=your-model-name
   AZURE_OPENAI_ENDPOINT=your-endpoint
   AZURE_OPENAI_API_KEY=your-api-key
   OPENAI_API_VERSION=2023-05-15
   ```

## Usage

1. Start the application:
```bash
chainlit run app.py
```

2. Open your browser and navigate to `http://localhost:8000`

3. Start searching for properties using natural language queries like:
   - "Find me a 3-bedroom house near downtown with a pool"
   - "Show me apartments under $2000 with parking"
   - "I need a pet-friendly condo within 5 miles of the beach"

## Project Structure

```
.
├── src/               # Source code
│   ├── app.py        # Main application file
│   └── __init__.py   # Package initialization
├── tests/            # Test directory
├── docs/             # Documentation
│   └── ai_property_search_article.md
├── public/           # Public assets
├── .chainlit/        # Chainlit configuration
├── requirements.txt  # Project dependencies
├── setenv.sh.template # Template for environment variables
└── .gitignore       # Git ignore file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
