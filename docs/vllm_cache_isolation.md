# vLLM Cache Isolation with cache_salt

## Overview

LiteLLM now supports vLLM's cache isolation feature through the `cache_salt` parameter. This feature allows you to control prefix cache reuse for improved privacy and security in shared environments.

## What is Cache Isolation?

vLLM uses prefix caching to improve performance by reusing Key-Value (KV) blocks from previous requests. While this significantly speeds up inference, it can create privacy concerns in multi-tenant environments where one user might infer information about another user's requests by observing latency differences (timing-based attacks).

Cache isolation solves this by allowing you to specify a `cache_salt` value. Only requests with the same salt can reuse cached KV blocks, effectively creating isolated cache namespaces.

## How to Use

### Basic Usage

```python
import litellm

response = litellm.completion(
    model="hosted_vllm/llama-3.1-70b-instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, world!"}
    ],
    cache_salt="my-cache-namespace"  # Isolate cache with this salt
)
```

### Common Use Cases

#### 1. Per-User Cache Isolation

Isolate cache per user to prevent cross-user information leakage:

```python
def get_completion_for_user(user_id: str, message: str):
    return litellm.completion(
        model="hosted_vllm/llama-3.1-70b-instruct",
        messages=[{"role": "user", "content": message}],
        cache_salt=f"user-{user_id}"
    )
```

#### 2. Per-Session Cache Isolation

Isolate cache per user session for even finer-grained control:

```python
def get_completion_for_session(user_id: str, session_id: str, message: str):
    return litellm.completion(
        model="hosted_vllm/llama-3.1-70b-instruct",
        messages=[{"role": "user", "content": message}],
        cache_salt=f"user-{user_id}-session-{session_id}"
    )
```

#### 3. Trust Group Cache Sharing

Allow cache sharing within a trust group while isolating from other groups:

```python
def get_completion_for_team(team_id: str, message: str):
    return litellm.completion(
        model="hosted_vllm/llama-3.1-70b-instruct",
        messages=[{"role": "user", "content": message}],
        cache_salt=f"team-{team_id}"
    )
```

## Performance Considerations

- **With cache_salt**: Cache is isolated to requests with the same salt. This provides better security but may reduce cache hit rate.
- **Without cache_salt**: All requests can potentially share cache, maximizing performance but with potential privacy implications.

## Async Usage

The `cache_salt` parameter also works with async completions:

```python
import asyncio
import litellm

async def main():
    response = await litellm.acompletion(
        model="hosted_vllm/llama-3.1-70b-instruct",
        messages=[{"role": "user", "content": "Hello!"}],
        cache_salt="async-user-123"
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Configuration

The `cache_salt` parameter is:
- **Optional**: If not provided, vLLM uses its default caching behavior
- **String type**: Any string value can be used as a salt
- **vLLM-specific**: Only applies when using vLLM (hosted_vllm/) models

## Security Best Practices

1. **Use unique salts per user/session** in multi-tenant environments
2. **Consider the trade-off** between performance (cache reuse) and privacy (cache isolation)
3. **Combine with other security measures** like authentication and rate limiting
4. **Document your cache isolation strategy** for compliance and audit purposes

## References

- [vLLM Prefix Caching Documentation](https://docs.vllm.ai/en/latest/features/prefix_caching.html)
- [LiteLLM vLLM Provider Documentation](https://docs.litellm.ai/docs/providers/vllm)

## Example

See the complete example in `examples/vllm_cache_salt_example.py`.
