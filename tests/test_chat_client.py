import pytest
import asyncio
from unittest.mock import Mock, patch
from app import ChatClient, ChatConfig, RateLimiter, InputValidator

@pytest.fixture
def mock_config():
    return ChatConfig(
        deployment_name="test-model",
        azure_endpoint="https://test.endpoint",
        api_key="test-key",
        api_version="2023-05-15",
        system_prompt="Test prompt",
        rate_limit=60,
        timeout=30
    )

@pytest.fixture
def chat_client(mock_config):
    return ChatClient(mock_config)

@pytest.mark.asyncio
async def test_rate_limiter():
    limiter = RateLimiter(calls_per_minute=2)
    start_time = asyncio.get_event_loop().time()
    
    # First call should pass immediately
    await limiter.acquire()
    
    # Second call should pass immediately
    await limiter.acquire()
    
    # Third call should wait
    await limiter.acquire()
    
    end_time = asyncio.get_event_loop().time()
    assert end_time - start_time >= 60  # Should have waited at least 60 seconds

def test_input_validator():
    validator = InputValidator()
    
    # Test valid input
    assert validator.validate_message("Hello, world!") is True
    
    # Test invalid input
    assert validator.validate_message("") is False
    assert validator.validate_message("   ") is False
    
    # Test tool args sanitization
    test_args = {"key": "value", "unsafe": "<script>alert('xss')</script>"}
    sanitized = validator.sanitize_tool_args(test_args)
    assert sanitized["key"] == "value"
    assert "<script>" not in sanitized["unsafe"]

@pytest.mark.asyncio
async def test_chat_client_initialization(mock_config):
    client = ChatClient(mock_config)
    assert client.config == mock_config
    assert len(client.messages) == 0
    assert client.system_prompt == mock_config.system_prompt
    assert isinstance(client.rate_limiter, RateLimiter)
    assert isinstance(client.validator, InputValidator)

@pytest.mark.asyncio
async def test_generate_response_invalid_input(chat_client):
    with pytest.raises(ValueError):
        async for _ in chat_client.generate_response("", []):
            pass

@pytest.mark.asyncio
async def test_generate_response_timeout(chat_client):
    with patch.object(chat_client.client.chat.completions, 'create') as mock_create:
        mock_create.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(asyncio.TimeoutError):
            async for _ in chat_client.generate_response("Hello", []):
                pass

@pytest.mark.asyncio
async def test_cleanup_streams(chat_client):
    # Create a mock stream
    mock_stream = Mock()
    mock_stream.aclose = Mock()
    
    # Add stream to active streams
    chat_client.active_streams.append(mock_stream)
    
    # Call cleanup
    await chat_client._cleanup_streams()
    
    # Verify stream was closed
    mock_stream.aclose.assert_called_once()
    assert len(chat_client.active_streams) == 0 