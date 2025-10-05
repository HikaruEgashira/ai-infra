"""
Custom callbacks to fix invalid request parameters
"""
from litellm.integrations.custom_logger import CustomLogger
import litellm


class RequestValidator(CustomLogger):
    """
    Validates and fixes request parameters before sending to LLM
    """

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        """Fix parameters at the earliest possible hook"""
        if call_type == "completion" or call_type == "acompletion":
            self._fix_params(data)
        return data

    async def async_log_pre_api_call(self, model, messages, kwargs):
        """Fix invalid parameters in async context"""
        print(f"[RequestValidator BEFORE FIX] kwargs keys: {list(kwargs.keys())}")
        if "tools" in kwargs:
            print(f"[RequestValidator BEFORE FIX] tools count: {len(kwargs.get('tools', []))}")
            print(f"[RequestValidator BEFORE FIX] first tool keys: {list(kwargs['tools'][0].keys()) if kwargs['tools'] else 'none'}")
        self._fix_params(kwargs)
        if "tools" in kwargs:
            print(f"[RequestValidator AFTER FIX] tools count: {len(kwargs.get('tools', []))}")
            print(f"[RequestValidator AFTER FIX] first tool: {kwargs['tools'][0] if kwargs['tools'] else 'none'}")
        return kwargs

    def log_pre_api_call(self, model, messages, kwargs):
        """Fix invalid parameters in sync context"""
        self._fix_params(kwargs)
        return kwargs

    def _fix_params(self, kwargs):
        """Fix or remove invalid parameters"""

        # Fix max_completion_tokens
        if "max_completion_tokens" in kwargs:
            val = kwargs.get("max_completion_tokens")
            if val is not None and (not isinstance(val, int) or val <= 0):
                print(f"[RequestValidator] Removing invalid max_completion_tokens: {val}")
                del kwargs["max_completion_tokens"]

        # Fix max_output_tokens (similar to max_completion_tokens)
        if "max_output_tokens" in kwargs:
            val = kwargs.get("max_output_tokens")
            if val is not None and (not isinstance(val, int) or val < 16):
                print(f"[RequestValidator] Removing invalid max_output_tokens: {val}")
                del kwargs["max_output_tokens"]

        # Fix max_tokens
        if "max_tokens" in kwargs:
            val = kwargs.get("max_tokens")
            if val is not None and (not isinstance(val, int) or val <= 0):
                print(f"[RequestValidator] Removing invalid max_tokens: {val}")
                del kwargs["max_tokens"]

        # Fix stream_options - remove unsupported parameters
        if "stream_options" in kwargs:
            stream_opts = kwargs.get("stream_options")
            if isinstance(stream_opts, dict) and "include_usage" in stream_opts:
                print(f"[RequestValidator] Removing unsupported stream_options.include_usage")
                del stream_opts["include_usage"]
                # If stream_options is now empty, remove it entirely
                if not stream_opts:
                    del kwargs["stream_options"]

        # Fix tools parameter
        if "tools" in kwargs and kwargs["tools"]:
            print(f"[RequestValidator DEBUG] Original tools count: {len(kwargs['tools'])}")
            valid_tools = []
            for i, tool in enumerate(kwargs["tools"]):
                if not isinstance(tool, dict):
                    print(f"[RequestValidator] Skipping non-dict tool at index {i}: {tool}")
                    continue

                # Check for function-based tool (new OpenAI format: {type: 'function', function: {...}})
                if "function" in tool and isinstance(tool.get("function"), dict):
                    func = tool["function"]
                    if not func.get("name"):
                        print(f"[RequestValidator] Skipping tool {i} with missing function.name")
                        continue

                    # Convert to format that includes type and flattened function fields
                    old_format_tool = {
                        "type": "function",
                        "name": func.get("name"),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {"type": "object", "properties": {}})
                    }
                    valid_tools.append(old_format_tool)
                    print(f"[RequestValidator] Converted tool {i} from nested to flat format")
                # Already in old format
                elif "name" in tool:
                    if not tool.get("name"):
                        print(f"[RequestValidator] Skipping tool {i} with empty name")
                        continue
                    valid_tools.append(tool)
                else:
                    print(f"[RequestValidator] Skipping tool {i} without name or function: {list(tool.keys())}")

            if valid_tools:
                kwargs["tools"] = valid_tools
                print(f"[RequestValidator] Kept {len(valid_tools)} valid tools in old format")
                print(f"[RequestValidator DEBUG] First tool keys: {list(valid_tools[0].keys()) if valid_tools else 'none'}")
            else:
                print(f"[RequestValidator] Removing tools parameter (no valid tools)")
                del kwargs["tools"]


# Create singleton instance
request_validator = RequestValidator()
