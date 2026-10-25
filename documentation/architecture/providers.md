# Providers

AI Assist talks to AI providers through two small interfaces, so the turn loop never needs to know which provider it is calling. Adding a provider means adding classes, not changing `AIAgentManager`. Class summaries are in the [agent and providers reference](../reference/apex/agent-and-providers.md).

## The pieces

| Piece | Job |
|---|---|
| `AIProvider` | Holds the provider-neutral types (`Request`, `Response`, `ToolDefinition`, `ToolCall`, `Session`), looks up the right builder and handler, and supplies connection presets |
| `IAIProviderRequestBuilder` | One method, `buildRequestBody`: turns the neutral `AIProvider.Request` into that provider's JSON body |
| `IAIProviderResponseHandler` | One method, `handleResponse`: reads the HTTP response, adds the results to the provider's message list, and returns a neutral `AIProvider.Response` (reply text, tool calls, token counts) |

The endpoint path and API version header are not part of the builder. They differ per deployment (for example Azure OpenAI against OpenAI itself), so they live on the model configuration.

## Implementations

| `AIProvider__c` value | Request builder | Response handler | API |
|---|---|---|---|
| `Anthropic` | `AIAnthropicMessageRequestBuilder` | `AIAnthropicMessageResponseHandler` | Messages API |
| `AnthropicAgent` | `AIAnthropicAgentRequestBuilder` | `AIAnthropicAgentResponseHandler` | Agent API (sessions) |
| `OpenAI` | `AIOpenAiRequestBuilder` | `AIOpenAiResponseHandler` | Chat Completions API |

The two simple providers make one callout per pass of the turn loop. `AnthropicAgent` answers over a session: the request builder starts a new session (or continues the one saved on the conversation) and the response handler makes further callouts to fetch events until the session settles. The session id is saved on the conversation (`ExternalReference__c`) by `AIMessageProcessingQueueable` so the next turn can continue it. That provider also needs an `EnvironmentId__c` on its model configuration.

## How a model configuration picks a provider

1. An agent points at one `AIModelConfiguration__c`.
2. `AIAgentManager` reads `AIProvider__c` from it and calls `AIProvider.getRequestBuilder` and `getResponseHandler`. The lookup is a map from the lower-cased provider name to a class, so it is case-insensitive.
3. The request is sent to `callout:` plus `NamedCredential__c` plus `ApiPath__c`.
4. Other fields on the configuration shape the request: `ModelIdentifier__c`, `MaximumOutputTokens__c`, `Temperature__c`, `ApiVersionHeaderName__c` and `ApiVersionHeaderValue__c`.

## Named credentials

The API key is never stored in an AI Assist record. The model configuration only names a Named Credential, and the credential holds the key in an External Credential.

`AIProvider.getPreset` supplies the starting values the Models tab offers for each provider (base URL, API path, and the header that carries the key). For the Anthropic providers the key goes in `x-api-key`; for OpenAI it goes in `Authorization` as a bearer token. An OpenAI-compatible service uses the OpenAI preset with its own base URL.

## Failures

`AIProvider.getFailureReason` maps an HTTP status and response body to a `FailureReason__c` such as `Authentication Failed`, `Model Retired`, `Rate Limited`, `Timeout` or `Provider Error`. The retry rules use `RetryAttempts__c` and `RetryableStatusCodes__c` on `AIAssistSettings__c`; some statuses (400, 401, 403, 404, 410, 413, 422) are never retried.

## Adding a provider

1. Add a value to the `AIProvider__c` picklist and an `AI_PROVIDER_*` constant.
2. Write a request builder and a response handler.
3. Add one line to each map in `AIProvider`, and a case in `getPreset`.
