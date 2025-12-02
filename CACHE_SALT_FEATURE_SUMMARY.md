# vLLM Cache Isolation Feature - Implementation Summary

## Overview

This document summarizes the implementation of vLLM's cache isolation feature in LiteLLM using the `cache_salt` parameter.

## What Was Implemented

### 1. Core Functionality

Added support for the `cache_salt` parameter to enable vLLM's prefix cache isolation feature. This allows users to control which requests can share cached Key-Value blocks, improving security and privacy in multi-tenant environments.

### 2. Code Changes

#### a. Parameter Support in vLLM Configuration
- **File**: `litellm/llms/hosted_vllm/chat/transformation.py`
- **Changes**: Added `cache_salt` to the list of supported OpenAI parameters in `HostedVLLMChatConfig.get_supported_openai_params()`
- This ensures that `cache_salt` is recognized as a valid parameter and passed through to vLLM

#### b. Main API Function Signatures
- **File**: `litellm/main.py`
- **Changes**:
  - Added `cache_salt: Optional[str] = None` parameter to both `completion()` and `acompletion()` functions
  - Added documentation for the parameter in function docstrings
  - The parameter is automatically handled by the existing parameter mapping logic

#### c. Tests
- **File**: `tests/test_litellm/llms/hosted_vllm/chat/test_hosted_vllm_chat_transformation.py`
- **Changes**: Added two test functions:
  1. `test_hosted_vllm_supports_cache_salt()`: Verifies that `cache_salt` is in the supported params and is correctly mapped
  2. `test_hosted_vllm_cache_salt_in_request()`: Verifies that `cache_salt` is included in the transformed request sent to vLLM

### 3. Documentation

#### a. Example Code
- **File**: `examples/vllm_cache_salt_example.py`
- **Contents**: Comprehensive examples demonstrating:
  - User-specific cache isolation
  - Session-specific cache isolation
  - Trust group cache sharing
  - Default behavior without cache_salt

#### b. Feature Documentation
- **File**: `docs/vllm_cache_isolation.md`
- **Contents**: Complete documentation including:
  - Overview of cache isolation
  - Usage examples for different scenarios
  - Performance considerations
  - Security best practices
  - References to vLLM documentation

## How It Works

### Request Flow

1. User calls `litellm.completion()` or `litellm.acompletion()` with `cache_salt` parameter
2. LiteLLM validates the request and extracts parameters
3. The `cache_salt` parameter is mapped through `HostedVLLMChatConfig.map_openai_params()`
4. The parameter is included in the transformed request sent to vLLM
5. vLLM uses the salt to isolate cache reuse

### Example Usage

```python
import litellm

# User-specific cache isolation
response = litellm.completion(
    model="hosted_vllm/llama-3.1-70b-instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, world!"}
    ],
    cache_salt="user-123"  # Only requests with salt "user-123" share cache
)
```

## Configuration

The feature is **opt-in** via the `cache_salt` parameter:
- **When provided**: Cache is isolated to requests with the same salt value
- **When omitted**: Default vLLM caching behavior (all requests can share cache)

No additional configuration files or environment variables are required. Users simply pass the `cache_salt` parameter when needed.

## Testing

All tests pass successfully:
- `test_hosted_vllm_supports_cache_salt`: ✅ PASSED
- `test_hosted_vllm_cache_salt_in_request`: ✅ PASSED
- All existing vLLM tests continue to pass: ✅ PASSED

## Benefits

### Security
- Prevents timing-based attacks where adversaries could infer cached content by observing latency differences
- Enables isolated cache namespaces for different users/sessions/teams

### Flexibility
- Users can choose their own cache isolation strategy (per-user, per-session, per-team, etc.)
- Completely optional - doesn't affect users who don't need cache isolation

### Performance
- Requests within the same cache namespace (same salt) still benefit from prefix caching
- No performance penalty for users who don't use the feature

## Use Cases

1. **Multi-tenant SaaS applications**: Isolate cache between different customers
2. **Privacy-sensitive applications**: Prevent information leakage via cache timing
3. **Team collaboration**: Share cache within teams while isolating from other teams
4. **Session-based applications**: Isolate cache per user session

## References

- vLLM Prefix Caching Documentation: https://docs.vllm.ai/en/latest/features/prefix_caching.html
- LiteLLM vLLM Provider Documentation: https://docs.litellm.ai/docs/providers/vllm

## Files Modified

1. `litellm/llms/hosted_vllm/chat/transformation.py`
2. `litellm/main.py`
3. `tests/test_litellm/llms/hosted_vllm/chat/test_hosted_vllm_chat_transformation.py`

## Files Created

1. `examples/vllm_cache_salt_example.py`
2. `docs/vllm_cache_isolation.md`
3. `CACHE_SALT_FEATURE_SUMMARY.md` (this file)
