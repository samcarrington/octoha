# Account Discovery Bug Research Findings

## Context Summary

The Octoha integration has a critical bug in the config flow setup process. The `get_account()` method in `OctohaApiClient` requires an account number to be set, but during config flow setup, we only have the API key. This creates a chicken-and-egg problem: we need the account number to fetch account data, but we need to fetch account data to get the account number.

## Current Problem Analysis

### The Bug Location
In `/src/custom_components/octoha/config_flow.py` line 104:
```python
# Fetch account data to discover meters
self._account = await self._client.get_account()
```

The client is initialized without an account number (lines 96-99):
```python
self._client = OctohaApiClient(
    session=session,
    api_key=api_key,
    # No account_number parameter!
)
```

But `get_account()` in `client.py` requires an account number (lines 206-207):
```python
if self._account_number is None:
    raise OctopusError("Account number not set")
```

### Existing Solution Available

The codebase already has the solution! There's an `ACCOUNT_NUMBER_QUERY` defined in `/src/custom_components/octoha/api/graphql.py` lines 77-89:

```graphql
ACCOUNT_NUMBER_QUERY = """
query getAccountNumber($apiKey: String!) {
  viewer {
    accounts(first: 1) {
      edges {
        node {
          number
        }
      }
    }
  }
}
"""
```

However, this query is **not being used anywhere** in the current implementation.

## Reference Implementation from open-octopus

The upstream `open-octopus` project shows the correct pattern. Looking at their client initialization, they **require** the account number to be provided during client construction:

```python
def __init__(
    self,
    api_key: str,
    account: str,  # <-- Required parameter
    mpan: Optional[str] = None,
    # ...
):
```

This means open-octopus expects users to **already know their account number** before using the client. However, the GraphQL API provides a way to discover this via the `viewer` query.

## Recommended Implementation Approach

### Solution 1: Add Account Discovery Method (Recommended)

Add a new method to `OctohaApiClient` to discover account numbers from an API key:

```python
async def discover_account_number(self) -> str:
    """Discover account number from API key using GraphQL viewer query.
    
    Returns:
        Account number string (e.g., "A-FB05ED6C")
        
    Raises:
        AuthenticationError: If API key is invalid
        OctopusError: If no accounts found or API error
    """
    data = await self._graphql(
        ACCOUNT_NUMBER_QUERY,
        # Note: The query variable name should match GraphQL schema
        # It might be "apiKey" or just use the token directly
    )
    
    accounts = data.get("viewer", {}).get("accounts", {}).get("edges", [])
    if not accounts:
        raise OctopusError("No accounts found for this API key")
    
    return accounts[0]["node"]["number"]
```

### Solution 2: Update Config Flow

Modify the config flow to use account discovery:

```python
async def async_step_user(self, user_input=None):
    # ... existing validation ...
    
    try:
        # Create client without account number initially
        self._client = OctohaApiClient(
            session=session,
            api_key=api_key,
        )
        
        # Validate credentials first
        await self._client.validate_credentials()
        
        # Discover account number
        account_number = await self._client.discover_account_number()
        
        # Update client with discovered account number
        self._client._account_number = account_number
        
        # Now fetch full account data
        self._account = await self._client.get_account()
        
        # ... rest of setup flow ...
```

### Solution 3: Alternative - Constructor Pattern

Allow client initialization without account number and lazy-load it:

```python
class OctohaApiClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        account_number: str | None = None,  # Make optional
    ) -> None:
        # ... existing init ...
        self._account_number = account_number
        self._discovered_account = False

    async def _ensure_account_number(self) -> None:
        """Ensure account number is available, discover if needed."""
        if self._account_number is None and not self._discovered_account:
            self._account_number = await self.discover_account_number()
            self._discovered_account = True

    async def get_account(self, force_refresh: bool = False) -> Account:
        await self._ensure_account_number()  # Add this line
        
        # ... rest of existing method ...
```

## GraphQL Query Validation Needed

The existing `ACCOUNT_NUMBER_QUERY` may need verification:

1. **Parameter name**: The query uses `$apiKey: String!` but the GraphQL API might not need this - the authentication is handled via the token in the header.

2. **Query structure**: Need to verify the exact schema. The `viewer` query pattern is common in GraphQL APIs for "current user" data.

3. **Testing**: Should test with real API key to ensure the query works as expected.

## Code Patterns to Follow

### Existing Error Handling Pattern
```python
try:
    # API call
    data = await self._graphql(query, variables)
except AuthenticationError:
    # Handle auth failure
    errors["base"] = "invalid_api_key"
except OctopusError as err:
    # Handle API errors
    errors["base"] = "cannot_connect"
```

### Existing GraphQL Client Pattern
```python
async def _graphql(
    self,
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict:
    """Execute an authenticated GraphQL query."""
    token = await self._token_manager.get_token()
    
    payload = {
        "query": query,
        "variables": variables or {},
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": token,
    }
    # ... rest of implementation
```

## Dependencies Identified

### Required for Implementation
- **GraphQL Query**: `ACCOUNT_NUMBER_QUERY` already exists and just needs to be used
- **Authentication**: Existing `TokenManager` handles GraphQL auth tokens
- **HTTP Client**: Existing `aiohttp` session management via `async_get_clientsession(hass)`

### No Additional Dependencies
- No new external packages needed
- No changes to manifest.json required
- Follows existing HA integration patterns

## Risks and Unknowns

### Technical Risks
1. **GraphQL Schema Changes**: The `viewer.accounts` query structure might change
2. **Multi-Account Users**: Some users might have multiple Octopus accounts - need to handle this case
3. **API Rate Limiting**: Account discovery adds an extra API call during setup

### Implementation Gaps Requiring Spikes
1. **Query Parameter Validation**: Need to test if `ACCOUNT_NUMBER_QUERY` works as-is or needs modification
2. **Multi-Account Handling**: Decision needed on how to handle users with multiple accounts
3. **Error Message UX**: Clear error messages for "no accounts found" vs "multiple accounts found"

## Recommended Success Criteria

### Technical Validation
- Config flow completes successfully with only API key input
- Account discovery works for single-account users within 5 seconds
- Clear error messages for invalid API keys
- Graceful handling of multi-account scenarios
- No breaking changes to existing configured integrations

### User Experience
- User only needs to provide API key during setup
- Setup time remains under 30 seconds
- Clear progress indication during account discovery
- Helpful error messages with next steps

## Additional Resources

### Code References Found
- **GraphQL Query**: `/src/custom_components/octoha/api/graphql.py` lines 77-89
- **Client Implementation**: `/src/custom_components/octoha/api/client.py` 
- **Config Flow**: `/src/custom_components/octoha/config_flow.py` lines 96-108
- **Authentication**: `/src/custom_components/octoha/api/auth.py` - token management patterns

### External References
- **open-octopus source**: Confirmed they require account number at initialization
- **Octopus Energy GraphQL API**: Uses `viewer` pattern for current user data
- **HA Integration Patterns**: Config flow credential validation best practices

## Implementation Priority

**High Priority** - This is a blocking bug that prevents the integration from working during initial setup. Should be implemented immediately as it's required for basic functionality.

The solution is straightforward since the GraphQL query already exists - it just needs to be connected to the config flow logic.