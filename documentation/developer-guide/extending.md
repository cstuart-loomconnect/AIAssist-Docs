# Extending AI Assist

AI Assist has three extension points: an AI provider, a data source and a workflow action. Each is an Apex interface. This page lists the interfaces with their real signatures and says where each one is looked up.

| You want to | Implement | Registered by |
|---|---|---|
| Talk to a new AI provider | `IAIProviderRequestBuilder` and `IAIProviderResponseHandler` | Two maps in `AIProvider` |
| Give the model records from custom Apex | `IAIDataSourceExecutor` (and optionally `IAIDataSourceInputDescriber`) | The class name on an `AIDataSource__c` record |
| Let the model suggest an action that runs custom Apex | `IAIWorkflowActionExecutor` (and optionally `IAIWorkflowActionInputDescriber`) | The class name on an `AIWorkflowAction__c` record |

!!! note "Permanent API"
    `IAIDataSourceExecutor`, `IAIDataSourceInputDescriber`, `IAIWorkflowActionExecutor`, `IAIWorkflowActionInputDescriber`, and the request and response classes they use are `global`. Their header comments say that once released a method cannot be changed or removed, only added to. The two provider interfaces are `public`.

## Add a provider

A provider is a pair of classes. The request builder turns the provider-neutral request into the provider's JSON. The response handler reads the provider's reply into a provider-neutral response. `AIAgentManager` never sees a provider's raw JSON, so it does not change.

```apex
public interface IAIProviderRequestBuilder {

    // Converts the canonical request into this provider's exact JSON-ready body.
    Map<String, Object> buildRequestBody(AIProvider.Request request);
}

public interface IAIProviderResponseHandler {

    AIProvider.Response handleResponse(List<Map<String, Object>> providerMessages, HttpResponse response, List<AIProvider.ToolCall> previousToolCalls, List<Object> previousToolResults, AIProvider.Request request);
}
```

`handleResponse` is called in two ways. With `response` set, it parses the reply, appends the assistant's turn to `providerMessages` and returns an `AIProvider.Response` (text, tool calls, token counts). With `previousToolCalls` and `previousToolResults` set and `response` null, it only appends the tool results to `providerMessages`, and returns null.

Steps:

1. Add the value to the `AIProvider__c` picklist on `AIModelConfiguration__c` (today `Anthropic`, `AnthropicAgent`, `OpenAI`).
2. Add an `AI_PROVIDER_*` constant to `AIAssistApplicationConstants`.
3. Write the two classes. Use `AIAnthropicMessageRequestBuilder` and `AIAnthropicMessageResponseHandler` (or the `AIOpenAi*` pair) as the model.
4. In `AIProvider`, add one line to `REQUEST_BUILDER_BY_PROVIDER` and one to `RESPONSE_HANDLER_BY_PROVIDER`. Keys are the lower-cased constant. `AIProvider.isSupported` is true only when both maps know the provider.
5. Add a branch to `AIProvider.getPreset` (base URL, API path, auth header, version header) so the AI Agent Models tab can fill in the form.
6. Add the constant to the `PROVIDERS` list in `AIModelsEditorService` so the tab offers a card.
7. Test it with `AIAssistTestProviderMock` (see [Testing](testing.md)).

**Where it is dispatched.** `AIAgentManager.executeAiMessage` calls `AIProvider.getRequestBuilder(...)` and `AIProvider.getResponseHandler(...)` with the model's `AIProvider__c`, serialises the body, and sends it to `callout:<named credential><API path>`. The endpoint path and version header are not part of the interfaces: they live on `AIModelConfiguration__c`.

`AIProvider.getFailureReason(statusCode, body)` maps a refused status to a `FailureReason__c` value for every provider. Extend it if your provider reuses status codes in its own way.

## Add a data source

A data source gives the model a tool that returns records. A SOQL data source needs no code (it is a template on the AI Tools tab). Write Apex when SOQL is not enough.

```apex
global interface IAIDataSourceExecutor {

    AIDataSourceResponse execute(AIDataSourceRequest request);
}

// Optional: lets the AI Tools tab fill in the Inputs step.
global interface IAIDataSourceInputDescriber {

    String describeInputs();
}
```

`AIDataSourceRequest` carries `recordId` (null for an unbound source), `inputParameters`, `conversationId`, `agentId`, `userId`, `dataSourceName` and `maxRows`. Return an `AIDataSourceResponse` holding a `List<SObject>` named `records`.

```apex
public with sharing class AccountOpenCases implements IAIDataSourceExecutor {

    public AIDataSourceResponse execute(AIDataSourceRequest request) {

        List<Case> cases = [SELECT Id, Subject, Status FROM Case WHERE AccountId = :request.recordId WITH USER_MODE LIMIT 20];

        return new AIDataSourceResponse(cases);
    }
}
```

`describeInputs` returns an input schema as JSON text, the same format saved to `AIDataSource__c.InputSchema__c`, for example `{"type":"object","properties":{"recordId":{"type":"string","x-source":"page"}}}`. See `AIDataSourceTestStub`.

**Where it is registered and dispatched.**

- Create an `AIDataSource__c` record with `SourceType__c` = `Apex` and `ApexClassName__c` = your class name (the AI Tools tab does this, and lists classes found through `ApexTypeImplementor` for `IAIDataSourceExecutor`). Assign it to an agent.
- At run time, `AIDataSourceDispatcher.runDataSource` loads the record, checks it is active and assigned to the agent, then uses `Type.forName('', className)` and checks `IAIDataSourceExecutor.class.isAssignableFrom(...)` before anything in your class runs. It builds the request and calls `execute`. The records then go through `AIDataSourceResultProcessor`, which masks personal data before they reach the model.
- Your class owns its security context. What it returns goes to an AI model, so query in user mode.

## Add a workflow action

A workflow action is something the model may suggest and the user may run, such as updating a record or sending an email.

```apex
global interface IAIWorkflowActionExecutor {

    AIWorkflowActionResponse execute(AIWorkflowActionRequest request);
}

// Optional: lets the AI Tools tab fill in the Inputs step.
global interface IAIWorkflowActionInputDescriber {

    String describeInputs();
}
```

`AIWorkflowActionRequest` carries `recordId`, `inputParameters`, `conversationId`, `agentId`, `userId`, `actionName` and `isConfirmed`. Return `new AIWorkflowActionResponse('Done.')`: the `message` is shown to the user as text.

`describeInputs` returns a JSON Schema object like `AIWorkflowAction__c.InputSchema__c`. A top-level `x-callouts` text or list says what the class does that cannot be rolled back, such as sending email.

**Where it is registered and dispatched.**

- Create an `AIWorkflowAction__c` with `ActionType__c` = `Apex` and `ApexClassName__c` = your class name, then assign it to an agent. The other action types are `Flow` and `Screen Flow`.
- `AIWorkflowActionDispatcher.runWorkflowAction` checks the application, the settings, the agent and the assignment, refuses an unconfirmed action when `RequiresConfirmation__c` is set, and keeps only the inputs the schema declares. It then does the same `Type.forName` and `isAssignableFrom` check, and calls `execute` in the user's own transaction.
- Your class is responsible for keeping its queries and DML within what the user may access.

!!! warning "To confirm"
    The interfaces are `global`, but every implementation in this repository (`AIDataSourceTestStub`, `AIWorkflowActionTestStub`) is a `public` class in the same package. Whether a class in another package must declare its methods `global` to implement them has not been tested here.

See also the generated [Data sources](../reference/apex/data-sources.md), [Workflow actions](../reference/apex/workflow-actions.md) and [Agent and providers](../reference/apex/agent-and-providers.md) reference pages.
