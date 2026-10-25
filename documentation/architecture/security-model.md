# Security model

AI Assist stores conversations that may hold personal data, so access is layered: object sharing, permission sets, agent access rules and conversation visibility. The permission sets themselves are listed in the [permission sets reference](../reference/permission-sets.md).

## Sharing models

| Object | Org-wide default (internal / external) |
|---|---|
| `AIConversation__c`, `AIFeedback__c`, `AITermsAcknowledgment__c`, `AIPlatformLog__c` | Private / Private |
| `AIAgent__c`, `AIDataSource__c`, `AIWorkflowAction__c`, `AIModelConfiguration__c`, `AIPromptTemplate__c`, `AIUsagePolicy__c`, `AIUsage__c`, `AIPIIRegistry__c` | Public Read/Write / Private |
| `AIConversationMessage__c`, `AIPIIMapping__c`, `AIPIIMaskingRecord__c`, `AIPIIFieldMetadata__c`, `AIAgentAssignment__c`, `AIAgentDataSource__c`, `AIAgentWorkflowAction__c`, `AIUsagePolicyAssignment__c`, `AIPromptTestMessage__c` | Controlled by Parent |

Conversations are private to their owner. Messages follow their conversation. Configuration objects are open for read and write by default, but a user can only act on them if a permission set gives object access.

## Without sharing, with explicit modes

Most classes are declared `without sharing`, and each statement says how it runs:

- **User mode** (`WITH USER_MODE`, `AccessLevel.USER_MODE`) wherever the user is expected to have access, such as finding their own conversation. This keeps sharing and field-level security in force.
- **System mode** (`WITH SYSTEM_MODE`, `AccessLevel.SYSTEM_MODE`) only for data the user may not touch directly: the conversation lock, the usage row, message processing status and token counts, and configuration read during a turn.

The reason is that a user must not be able to write system-managed fields (for example by editing their own message's status), yet the package must. `AIMessagingDataService` is the single place the messaging layer writes data the user cannot, and it marks the write as trusted so `AIConversationMessageTriggerHandler` accepts it. Callers are authorised first.

## Agent access

`AIAgent__c.AccessMode__c` is `All AI Assist Users` or `Assigned Users Only`. For assigned agents, an active `AIAgentAssignment__c` must name the user, or a permission set (or group) they hold. `AIMessageValidator.isUserAllowedOnAgent` checks this on every send, and `AIWorkflowActionDispatcher` reuses it so an action cannot run for a user the agent no longer admits.

## Permission sets

| Permission set | Intended for |
|---|---|
| AI Assist User (`AIAssistUser`) | Chat and give feedback. Creates and reads only their own conversations, messages and feedback. No configuration, logs or PII data |
| AI Assist Admin (`AIAssistAdminUser`) | Builds and maintains agents, prompts, tools, models, rules, PII registry and policies. Cannot read other users' messages or PII mappings |
| AI Assist Super User (`AIAssistSuperUser`) | Full access for oversight and for running tests |

Two custom permissions refine access: `AIAssistManageSettings` (changing settings and policy assignments) and `AIAssistViewSharedConversations`.

## Conversation visibility

A conversation is private to its owner unless the agent's `ConversationVisibility__c` is `Global`. `AIConversationVisibilityService` then allows another user to read it only if all of these hold: the sharing model already lets them see it, they are allowed through a direct share from the owner or through their policy's `ConversationVisibilityScope__c` (`My Conversations Only`, `My Subordinates Conversations` or `All Conversations`), and they can read the record the conversation is about. Any failure returns the same "not found" message, so nothing is revealed. Owners share read-only with individual users through `AIConversationShareService`, which adds a `DirectShare` row.

## Personal data

PII is masked before it is sent to a provider, and mappings and masking records are visible only to admin roles that need them. See [PII protection](pii-protection.md).
