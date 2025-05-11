import json
from mcp import ClientSession
from mcp.types import TextContent, ImageContent
import os
import re
from aiohttp import ClientSession, ClientError
import chainlit as cl
from openai import AzureOpenAI, AsyncAzureOpenAI, OpenAI, AsyncOpenAI
import traceback
from dotenv import load_dotenv
load_dotenv("azure.env")

SYSTEM_PROMPT = """You are a helpful home finder assistant. You have access to tools that can help you search for properties.

# Tools
You may call one or more functions to assist with the user query.
You are provided with function signatures within <tools></tools> XML tags.
For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags.

Example tool call:
<tool_call>
{"name": "search_properties", "arguments": {"location": "New York", "max_price": 500000}}
</tool_call>"""

async def check_local_model_availability():
    """Check if local model (LM Studio) is running and accessible"""
    try:
        async with ClientSession() as session:
            async with session.get("http://localhost:1234/v1/models") as response:
                return response.status == 200
    except ClientError:
        return False

def check_azure_credentials():
    """Check if Azure OpenAI credentials are available"""
    required_vars = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "OPENAI_API_VERSION"]
    return all(var in os.environ for var in required_vars)

class ChatClient:
    def __init__(self, use_local_llm=False) -> None:
        self.use_local_llm = use_local_llm
        if use_local_llm:
            # Initialize with LM Studio local server configuration
            self.client = AsyncOpenAI(
                base_url="http://localhost:1234/v1",
                api_key="lm-studio"  # LM Studio uses this as a placeholder
            )
            self.model = "qwen2.5-7b-instruct-1m"  # Local model
        else:
            # Initialize with Azure OpenAI configuration
            self.client = AsyncAzureOpenAI(
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                api_version=os.environ["OPENAI_API_VERSION"]
            )
            self.model = os.environ["AZURE_OPENAI_MODEL"]
        
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.system_prompt = SYSTEM_PROMPT
        self.active_streams = []  # Track active response streams
        
    async def _cleanup_streams(self):
        """Helper method to clean up all active streams"""
        for stream in self.active_streams:
            try:
                if hasattr(stream, 'aclose'):
                    await stream.aclose()
                elif hasattr(stream, 'close'):
                    await stream.close()
                # Add specific handling for HTTP streams
                elif hasattr(stream, '_stream'):
                    try:
                        await stream._stream.aclose()
                    except Exception:
                        pass
            except Exception as e:
                # Log the error but don't raise it
                print(f"Error during stream cleanup: {str(e)}")
                continue
        self.active_streams = []
        
    def _parse_json_response(self, content):
        """Parse JSON response from content field and convert to tool call format"""
        try:
            # Clean up the content string
            content = content.strip()
            if content.startswith('<tool_call>'):
                content = content[11:]
            if content.endswith('</tool_call>'):
                content = content[:-12]
            
            # Parse the JSON
            parsed = json.loads(content)
            if "name" in parsed and "arguments" in parsed:
                return {
                    "id": f"call_{hash(str(parsed))}",  # Generate a unique ID
                    "type": "function",
                    "function": {
                        "name": parsed["name"],
                        "arguments": json.dumps(parsed["arguments"])
                    }
                }
        except Exception as e:
            print(f"Error parsing JSON response: {str(e)}")
        return None

    async def process_response_stream(self, response_stream, tools, temperature=0):
        """
        Process response stream to handle function calls without recursion.
        """
        function_arguments = ""
        function_name = ""
        tool_call_id = ""
        is_collecting_function_args = False
        collected_messages = []
        tool_calls = []
        tool_called = False
        
        # Add to active streams for cleanup if needed
        self.active_streams.append(response_stream)
        
        try:
            async for part in response_stream:
                if part.choices == []:
                    continue
                delta = part.choices[0].delta
                finish_reason = part.choices[0].finish_reason
                
                # Process assistant content
                if delta.content:
                    collected_messages.append(delta.content)
                    yield delta.content
                
                # Handle tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if len(tool_calls) <= tc.index:
                            tool_calls.append({
                                "id": "", "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        tool_calls[tc.index] = {
                            "id": (tool_calls[tc.index]["id"] + (tc.id or "")),
                            "type": "function",
                            "function": {
                                "name": (tool_calls[tc.index]["function"]["name"] + (tc.function.name or "")),
                                "arguments": (tool_calls[tc.index]["function"]["arguments"] + (tc.function.arguments or ""))
                            }
                        }
                
                # Check if we've reached the end of a tool call
                if finish_reason == "tool_calls" and tool_calls:
                    for tool_call in tool_calls:
                        await self._handle_tool_call(
                            tool_call["function"]["name"],
                            tool_call["function"]["arguments"],
                            tool_call["id"]
                        )
                    tool_called = True
                    break
                
                # Check if we've reached the end of assistant's response
                if finish_reason == "stop":
                    # Try to parse the final content as a tool call
                    final_content = ''.join([msg for msg in collected_messages if msg is not None])
                    if final_content.strip():
                        tool_call = self._parse_json_response(final_content)
                        if tool_call:
                            await self._handle_tool_call(
                                tool_call["function"]["name"],
                                tool_call["function"]["arguments"],
                                tool_call["id"]
                            )
                            tool_called = True
                        else:
                            self.messages.append({"role": "assistant", "content": final_content})
                    
                    # Remove from active streams after normal completion
                    if response_stream in self.active_streams:
                        self.active_streams.remove(response_stream)
                        try:
                            await response_stream.aclose()
                        except Exception:
                            pass
                    break
                    
        except GeneratorExit:
            # Clean up this specific stream without recursive cleanup
            if response_stream in self.active_streams:
                self.active_streams.remove(response_stream)
                try:
                    await response_stream.aclose()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error in process_response_stream: {e}")
            traceback.print_exc()
            if response_stream in self.active_streams:
                self.active_streams.remove(response_stream)
                try:
                    await response_stream.aclose()
                except Exception:
                    pass
            self.last_error = str(e)
        
        # Store result in instance variables
        self.tool_called = tool_called
        self.last_function_name = function_name if tool_called else None

    async def _handle_tool_call(self, function_name, function_arguments, tool_call_id):
        """Handle a tool call by calling the appropriate MCP tool"""
        print(f"function_name: {function_name} function_arguments: {function_arguments}")
        function_args = json.loads(function_arguments)
        mcp_tools = cl.user_session.get("mcp_tools", {})
        mcp_name = None
        for connection_name, session_tools in mcp_tools.items():
            if any(tool.get("name") == function_name for tool in session_tools):
                mcp_name = connection_name
                break

        # Add the assistant message with tool call
        self.messages.append({
            "role": "assistant", 
            "tool_calls": [
                {
                    "id": tool_call_id,
                    "function": {
                        "name": function_name,
                        "arguments": function_arguments
                    },
                    "type": "function"
                }
            ]
        })
        
        # Call the tool and add response to messages
        func_response = await call_tool(mcp_name, function_name, function_args)
        print(f"Function Response: {json.loads(func_response)}")
        self.messages.append({
            "tool_call_id": tool_call_id,
            "role": "tool",
            "name": function_name,
            "content": json.loads(func_response),
        })

    async def generate_response(self, human_input, tools, temperature=0):
        self.messages.append({"role": "user", "content": human_input})
        print(f"self.messages: {self.messages}")
        print(f"Available tools: {tools}")  # Debug print
        
        try:
            # Handle multiple sequential function calls in a loop rather than recursively
            while True:
                try:
                    response_stream = await self.client.chat.completions.create(
                        model=self.model,
                        messages=self.messages,
                        tools=tools,
                        stream=True,
                        temperature=temperature
                    )
                    
                    # Stream and process the response
                    async for token in self._stream_and_process(response_stream, tools, temperature):
                        yield token
                    
                    # Check instance variables after streaming is complete
                    if not self.tool_called:
                        break
                    # Otherwise, loop continues for the next response that follows the tool call
                except Exception as e:
                    print(f"Error in generate_response: {str(e)}")
                    if "function calling" in str(e).lower():
                        # If function calling isn't supported, fall back to regular chat
                        response_stream = await self.client.chat.completions.create(
                            model=self.model,
                            messages=self.messages,
                            stream=True,
                            temperature=temperature
                        )
                        async for token in self._stream_and_process(response_stream, [], temperature):
                            yield token
                        break
                    else:
                        raise
        except GeneratorExit:
            # Ensure we clean up when the client disconnects
            await self._cleanup_streams()
            return

    async def _stream_and_process(self, response_stream, tools, temperature):
        """Helper method to yield tokens and return process result"""
        # Initialize instance variables before processing
        self.tool_called = False
        self.last_function_name = None
        self.last_error = None
        
        async for token in self.process_response_stream(response_stream, tools, temperature):
            yield token

def flatten(xss):
    return [x for xs in xss for x in xs]

@cl.on_mcp_connect
async def on_mcp(connection, session: ClientSession):
    result = await session.list_tools()
    tools = [{
        "name": t.name,
        "description": t.description,
        "parameters": t.inputSchema,
        } for t in result.tools]
    
    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_tools[connection.name] = tools
    cl.user_session.set("mcp_tools", mcp_tools)

@cl.step(type="tool") 
async def call_tool(mcp_name, function_name, function_args):
    # Set the step name dynamically based on the function being called
    cl.context.current_step.name = f"Using {function_name}"
    
    try:
        resp_items = []
        print(f"Function Name: {function_name} Function Args: {function_args}")
        
        # Check if MCP session exists
        if not hasattr(cl.context.session, 'mcp_sessions'):
            raise ConnectionError("MCP sessions not initialized. Please connect to the MCP server first.")
            
        mcp_session = cl.context.session.mcp_sessions.get(mcp_name)
        if mcp_session is None:
            raise ConnectionError(f"No active connection to MCP server '{mcp_name}'. Please connect to the server first.")
            
        mcp_session, _ = mcp_session  # Now safe to unpack
        
        func_response = await mcp_session.call_tool(function_name, function_args)
        for item in func_response.content:
            if isinstance(item, TextContent):
                resp_items.append({"type": "text", "text": item.text})
            elif isinstance(item, ImageContent):
                resp_items.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{item.mimeType};base64,{item.data}",
                    },
                })
            else:
                raise ValueError(f"Unsupported content type: {type(item)}")
        
    except ConnectionError as e:
        error_msg = str(e)
        print(f"Connection Error: {error_msg}")
        resp_items.append({"type": "text", "text": f"Error: {error_msg}. Please ensure the MCP server is running at http://localhost:8001/sse and try connecting again."})
    except Exception as e:
        traceback.print_exc()
        resp_items.append({"type": "text", "text": f"Error: {str(e)}"})
    return json.dumps(resp_items)

@cl.on_chat_start
async def start_chat():
    # Check Azure credentials
    has_azure_credentials = check_azure_credentials()
    
    # Check local model availability
    is_local_model_available = await check_local_model_availability()
    
    # Initialize with Local LLM if Azure credentials are missing
    use_local_llm = not has_azure_credentials
    client = ChatClient(use_local_llm=use_local_llm)
    cl.user_session.set("messages", [])
    cl.user_session.set("system_prompt", SYSTEM_PROMPT)
    cl.user_session.set("use_local_llm", use_local_llm)
    cl.user_session.set("has_azure_credentials", has_azure_credentials)
    cl.user_session.set("is_local_model_available", is_local_model_available)
    
    # Create welcome message
    welcome_content = """
# 🏠 Welcome to ElastiChat

## 🤖 Choose Your AI Assistant

Select which AI model you'd like to use for your property search:

"""
    
    # Add tools info if available
    mcp_tools = cl.user_session.get("mcp_tools", {})
    if mcp_tools:
        tools_list = "\n".join([f"- **{name}**: {len(tools)} available tools" 
                             for name, tools in mcp_tools.items()])
        welcome_content += f"\n\n### 🛠️ Available Tools:\n{tools_list}"
    
    # Create actions list
    actions = []
    
    # Add Azure OpenAI button
    actions.append(
        cl.Action(
            name="use_azure",
            label="🤖 AZURE OPENAI" if has_azure_credentials else "🤖 AZURE OPENAI (Not Available)",
            value="azure",
            payload={"llm": "azure"},
            description="Use Azure's powerful GPT models" if has_azure_credentials else "Azure OpenAI credentials not found. Please run setenv.sh with your Azure credentials."
        )
    )
    
    # Add Local LLM button
    actions.append(
        cl.Action(
            name="use_local",
            label="💻 LOCAL LLM" if is_local_model_available else "💻 LOCAL LLM (Not Available)",
            value="local",
            payload={"llm": "local"},
            description="Use local model through LM Studio" if is_local_model_available else "LM Studio is not running. Please start LM Studio with your local model."
        )
    )
    
    # Send welcome message with appropriate buttons
    await cl.Message(
        content=welcome_content,
        author="System",
        actions=actions
    ).send()
    
    # Show a single message if both models are unavailable
    if not has_azure_credentials and not is_local_model_available:
        await cl.Message(
            content="⚠️ No AI models are currently available. To use the app:\n\n1. For Azure OpenAI:\n   - Set up credentials in azure.env\n   - Run setenv.sh\n\n2. For Local LLM:\n   - Start LM Studio\n   - Load your model\n   - Start the local server",
            author="System"
        ).send()
    # Show appropriate message if only one model is available
    elif not has_azure_credentials and is_local_model_available:
        await cl.Message(
            content="✅ Using Local LLM by default. To use Azure OpenAI, please set your credentials in azure.env and run setenv.sh",
            author="System"
        ).send()
    elif has_azure_credentials and not is_local_model_available:
        await cl.Message(
            content="✅ Using Azure OpenAI by default. To use Local LLM, please start LM Studio with your local model.",
            author="System"
        ).send()

@cl.action_callback("use_azure")
async def on_use_azure(action):
    has_azure_credentials = cl.user_session.get("has_azure_credentials", False)
    
    if not has_azure_credentials:
        await cl.Message(
            content="⚠️ Azure OpenAI credentials not found. Please set your credentials in azure.env and run setenv.sh to use Azure OpenAI.",
            author="System"
        ).send()
        return
    
    cl.user_session.set("use_local_llm", False)
    await cl.Message(
        content="✅ Switched to Azure OpenAI",
        author="System"
    ).send()

@cl.action_callback("use_local")
async def on_use_local(action):
    is_local_model_available = cl.user_session.get("is_local_model_available", False)
    
    if not is_local_model_available:
        await cl.Message(
            content="⚠️ Local LLM is not available. Please start LM Studio with your local model to use this option.",
            author="System"
        ).send()
        return
    
    cl.user_session.set("use_local_llm", True)
    await cl.Message(
        content="✅ Switched to Local LLM",
        author="System"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    mcp_tools = cl.user_session.get("mcp_tools", {})
    tools = flatten([tools for _, tools in mcp_tools.items()])
    tools = [{"type": "function", "function": tool} for tool in tools]
    
    # Get the current LLM choice
    use_local_llm = cl.user_session.get("use_local_llm", False)
    
    # Create a fresh client instance for each message
    client = ChatClient(use_local_llm=use_local_llm)
    # Restore conversation history
    client.messages = cl.user_session.get("messages", [])
    
    msg = cl.Message(content="")
    async for text in client.generate_response(human_input=message.content, tools=tools):
        await msg.stream_token(text)
    
    # Update the stored messages after processing
    cl.user_session.set("messages", client.messages) 