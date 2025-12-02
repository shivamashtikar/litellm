"""
Example demonstrating vLLM cache isolation using cache_salt parameter.

This example shows how to use the cache_salt parameter to isolate cache usage
between different users or sessions for security and privacy purposes.

With cache_salt:
- Requests with the same salt can reuse cached KV blocks (faster)
- Requests with different salts cannot reuse each other's cached KV blocks (more secure)
- This prevents timing-based attacks where an adversary could infer cached content
  by observing latency differences

Reference: https://docs.vllm.ai/en/latest/features/prefix_caching.html
"""

import litellm
import os

# Set your vLLM API base
os.environ["HOSTED_VLLM_API_BASE"] = "http://localhost:8000"

# Example 1: User-specific cache isolation
# Each user gets their own cache namespace
def completion_with_user_cache(user_id: str, prompt: str):
    """
    Create a completion with cache isolated to a specific user.

    This ensures that User A cannot benefit from or observe the cached
    content of User B, preventing timing-based information leakage.
    """
    response = litellm.completion(
        model="hosted_vllm/llama-3.1-70b-instruct",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        cache_salt=f"user-{user_id}",  # Isolate cache per user
    )
    return response


# Example 2: Session-specific cache isolation
# Each session gets its own cache namespace
def completion_with_session_cache(user_id: str, session_id: str, prompt: str):
    """
    Create a completion with cache isolated to a specific user session.

    This provides even finer-grained isolation, ensuring that different
    sessions from the same user don't share cache.
    """
    response = litellm.completion(
        model="hosted_vllm/llama-3.1-70b-instruct",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        cache_salt=f"user-{user_id}-session-{session_id}",  # Isolate per session
    )
    return response


# Example 3: Trust group cache sharing
# Users within a trust group can share cache
def completion_with_trust_group_cache(trust_group: str, prompt: str):
    """
    Create a completion with cache shared among a trust group.

    All users/requests within the same trust group (e.g., "team-alpha")
    can reuse cached KV blocks, improving performance while maintaining
    isolation from other groups.
    """
    response = litellm.completion(
        model="hosted_vllm/llama-3.1-70b-instruct",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        cache_salt=f"trust-group-{trust_group}",
    )
    return response


# Example 4: No cache isolation (default behavior)
def completion_without_cache_salt(prompt: str):
    """
    Create a completion without cache isolation.

    Without cache_salt, all requests can potentially reuse each other's
    cached KV blocks. This maximizes cache hit rate and performance but
    may have privacy implications in multi-tenant environments.
    """
    response = litellm.completion(
        model="hosted_vllm/llama-3.1-70b-instruct",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        # No cache_salt = no cache isolation
    )
    return response


if __name__ == "__main__":
    # Example usage
    print("Example 1: User-specific cache isolation")
    response1 = completion_with_user_cache("alice", "What is the capital of France?")
    print(f"Response for Alice: {response1.choices[0].message.content}\n")

    print("Example 2: Session-specific cache isolation")
    response2 = completion_with_session_cache("bob", "session-123", "What is 2+2?")
    print(f"Response for Bob's session: {response2.choices[0].message.content}\n")

    print("Example 3: Trust group cache sharing")
    response3 = completion_with_trust_group_cache("team-alpha", "Hello!")
    print(f"Response for team-alpha: {response3.choices[0].message.content}\n")
