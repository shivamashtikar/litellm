# vLLM Cache Isolation in LiteLLM Proxy

## Overview

When running LiteLLM as a proxy server, you can enable automatic per-user cache isolation for vLLM requests. This feature automatically sets the `cache_salt` parameter based on each user's `user_api_key_user_id`, ensuring that different users cannot share or infer each other's cached content.

## Why Use Cache Isolation in Multi-Tenant Deployments?

In multi-tenant proxy deployments, multiple users share the same vLLM backend. Without cache isolation:
- **Timing Attacks**: Users could potentially infer cached content from other users by observing response latency differences
- **Privacy Concerns**: Different customers/teams sharing cache could lead to information leakage
- **Compliance Issues**: Some industries require strict data isolation between tenants

With automatic cache isolation:
- ✅ Each user gets their own isolated cache namespace
- ✅ Prevents timing-based information leakage
- ✅ Maintains performance within each user's requests
- ✅ Zero configuration required from API consumers

## Configuration

### Enable Automatic Cache Salt

Add to your `config.yaml`:

```yaml
general_settings:
  vllm_auto_cache_salt: true  # Enable automatic per-user cache isolation
  database_url: postgresql://... # Required for user_api_key_user_id
```

### Complete Example Configuration

See [`litellm/proxy/example_config_yaml/vllm_cache_isolation.yaml`](../litellm/proxy/example_config_yaml/vllm_cache_isolation.yaml) for a complete working example.

```yaml
model_list:
  - model_name: vllm-llama-70b
    litellm_params:
      model: hosted_vllm/llama-3.1-70b-instruct
      api_base: http://your-vllm-server:8000

general_settings:
  master_key: sk-1234
  vllm_auto_cache_salt: true  # Enable automatic cache isolation
  database_url: postgresql://user:password@localhost:5432/litellm
```

## How It Works

### Request Flow

1. **User Authentication**: User makes request with their API key
   ```bash
   curl http://localhost:4000/v1/chat/completions \
     -H "Authorization: Bearer sk-user-alice-key" \
     -d '{"model": "vllm-llama-70b", "messages": [...]}'
   ```

2. **User ID Extraction**: Proxy authenticates and extracts `user_api_key_user_id` from the API key

3. **Automatic Cache Salt Injection**: If `vllm_auto_cache_salt: true`, proxy automatically adds:
   ```json
   {
     "model": "vllm-llama-70b",
     "messages": [...],
     "cache_salt": "alice@example.com"  // Automatically added by proxy
   }
   ```

4. **vLLM Request**: Request is forwarded to vLLM with cache_salt, ensuring Alice's cache is isolated

### When Is cache_salt Added?

The proxy automatically adds `cache_salt` when **ALL** of these conditions are met:

1. ✅ `vllm_auto_cache_salt: true` in config
2. ✅ User is authenticated and has a `user_id`
3. ✅ Model is a vLLM model (model name contains "vllm" or uses `hosted_vllm/`)
4. ✅ Request doesn't already have a `cache_salt` parameter

### Manual Override

Users can still manually specify `cache_salt` if needed, which will override the automatic value:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-user-alice-key" \
  -d '{
    "model": "vllm-llama-70b",
    "messages": [...],
    "cache_salt": "custom-salt"  # Manual override
  }'
```

## Setup Guide

### Step 1: Configure Database

Cache isolation requires user management, which needs a database:

```yaml
general_settings:
  database_url: postgresql://user:password@localhost:5432/litellm
```

### Step 2: Enable Cache Isolation

```yaml
general_settings:
  vllm_auto_cache_salt: true
```

### Step 3: Start the Proxy

```bash
litellm --config config.yaml
```

### Step 4: Create Users and API Keys

```bash
# Create an API key for user "alice@example.com"
curl -X POST http://localhost:4000/key/generate \
  -H "Authorization: Bearer <master-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice@example.com",
    "models": ["vllm-llama-70b"]
  }'

# Response includes the generated API key
{
  "key": "sk-...",
  "user_id": "alice@example.com"
}
```

### Step 5: Make Requests

```bash
# Alice's request - automatically gets cache_salt="alice@example.com"
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer <alice-key>" \
  -d '{
    "model": "vllm-llama-70b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Bob's request - automatically gets cache_salt="bob@example.com"
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer <bob-key>" \
  -d '{
    "model": "vllm-llama-70b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

Alice and Bob will have completely isolated caches, preventing any potential information leakage.

## Use Cases

### 1. Multi-Tenant SaaS Platform

```yaml
general_settings:
  vllm_auto_cache_salt: true  # Isolate cache per customer
```

Each customer's API key has a unique `user_id`, ensuring complete cache isolation.

### 2. Team-Based Organizations

```bash
# Create team-specific API keys
curl -X POST http://localhost:4000/key/generate \
  -d '{"user_id": "team-alpha", "models": ["vllm-llama-70b"]}'

curl -X POST http://localhost:4000/key/generate \
  -d '{"user_id": "team-beta", "models": ["vllm-llama-70b"]}'
```

Team Alpha and Team Beta get isolated caches automatically.

### 3. Development vs Production Isolation

```bash
# Dev environment key
curl -X POST http://localhost:4000/key/generate \
  -d '{"user_id": "dev-environment", ...}'

# Prod environment key
curl -X POST http://localhost:4000/key/generate \
  -d '{"user_id": "prod-environment", ...}'
```

## Performance Considerations

### With vllm_auto_cache_salt: true

- ✅ Requests from the same user can reuse cache (fast)
- ✅ Prevents cross-user cache sharing (secure)
- ⚠️ Lower overall cache hit rate compared to shared cache
- ✅ Still significantly faster than no caching

### Without vllm_auto_cache_salt: false (default)

- ✅ Maximum cache hit rate (all users share cache)
- ✅ Fastest performance
- ⚠️ Potential timing-based information leakage
- ⚠️ Not suitable for multi-tenant deployments with privacy requirements

## Security Best Practices

1. **Always Enable in Multi-Tenant Environments**
   ```yaml
   vllm_auto_cache_salt: true  # Required for isolation
   ```

2. **Use Meaningful User IDs**
   - ✅ `user_id: "customer-acme-corp"`
   - ✅ `user_id: "team-engineering"`
   - ❌ `user_id: "user-1"` (less auditable)

3. **Monitor Cache Hit Rates**
   - Track cache performance per user
   - Adjust user groupings if needed

4. **Combine with Other Security Measures**
   - Rate limiting per user
   - Budget limits per user
   - Content filtering/guardrails

## Debugging

Enable debug logging to see cache_salt assignment:

```yaml
litellm_settings:
  set_verbose: true
```

Look for log messages like:
```
Auto-set cache_salt for vLLM model: vllm-llama-70b to user_id: alice@example.com
```

## Frequently Asked Questions

### Q: Does this work with vLLM passthrough endpoints?

**A:** Yes! The feature works with both:
- Standard `/v1/chat/completions` endpoint
- vLLM passthrough endpoint `/vllm/...`

### Q: What if a user doesn't have a user_id?

**A:** The proxy will not add `cache_salt` if:
- User is not authenticated
- User's API key doesn't have a `user_id`

Ensure all API keys have a `user_id` for cache isolation to work.

### Q: Can I disable cache isolation for specific models?

**A:** Currently, `vllm_auto_cache_salt` applies to all vLLM models. To disable for specific requests, clients can explicitly set `cache_salt: null` (though this is not recommended for security).

### Q: Does this affect non-vLLM models?

**A:** No, `cache_salt` is only added for vLLM models. Other providers are unaffected.

## Related Documentation

- [vLLM Cache Isolation (Direct API)](./vllm_cache_isolation.md)
- [vLLM Provider Documentation](https://docs.litellm.ai/docs/providers/vllm)
- [LiteLLM Proxy Documentation](https://docs.litellm.ai/docs/proxy/quick_start)
- [vLLM Prefix Caching](https://docs.vllm.ai/en/latest/features/prefix_caching.html)

## Complete Example

See the complete working example:
- Config: [`litellm/proxy/example_config_yaml/vllm_cache_isolation.yaml`](../litellm/proxy/example_config_yaml/vllm_cache_isolation.yaml)
- Documentation: This file
