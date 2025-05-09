# Elastic AI Infused Property Search

An intelligent property search system that combines Elasticsearch's powerful search capabilities with Azure OpenAI's natural language processing to create a conversational property search experience.

## Demo

Watch a demo of the property search system in action:

<iframe width="560" height="315" src="https://videos.elastic.co/embed/1qQtsuYSdeXGpvdhfYosnn" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

This demo showcases:
- Natural language property search
- Location-based search capabilities
- Real-time property recommendations
- Interactive chat interface

## Features

- Interactive chat interface powered by Chainlit
- Azure OpenAI API integration for natural language understanding
- Elasticsearch for powerful property search
- Google Maps API integration for location services
- Real-time streaming responses
- Dynamic query generation
- Location-based search capabilities

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
- Google Maps API key

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.
