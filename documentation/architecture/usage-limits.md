# Usage limits and throughput

AI Assist limits what each user can spend and how many messages run at once. Per-user limits come from usage policies; org-wide throughput controls live on the settings record. See the [usage and policies reference](../reference/apex/usage-and-policies.md) for the classes.

## Usage policies

An `AIUsagePolicy__c` holds a user's limits and capabilities:

| Field | Meaning |
|---|---|
| `MaxTokensPer24Hours__c` | Tokens the user's conversations may spend per day |
| `MaxConversationsPer24Hours__c` | New conversations per day |
| `MaxConcurrentConversations__c` | Active conversations at once |
| `UsageLimitReachedBehavior__c` | `Block New Messages`, `Block New Conversations Only` or `Notify Only` |
| `IsUserInitiatedChatEnabled__c`, `AllowedChannels__c`, `DebugModeEnabled__c`, `ConversationExportEnabled__c`, `ConversationVisibilityScope__c` | Capabilities, not limits |

A policy reaches users through `AIUsagePolicyAssignment__c` rows (a user or a permission set), or because it is marked `IsDefault__c`. `AIUsagePolicyService` picks the winner: the user's own assignments, then their permission sets (strictest wins), then default policies. The result is one combined policy that is never saved: strictest limits, widest capabilities. A user with no policy has no access to AI Assist at all.

## Daily usage

`AIUsage__c` holds one row per user, with `UsageDate__c`, `TokensUsed__c`, `InputTokens__c`, `OutputTokens__c` and `ConversationsStarted__c`. `AIUsageService` works out "today" in the org's time zone, locks the user's rows (`FOR UPDATE`), starts again any row from an earlier day, and adds new tokens and conversations. Tokens are added when a message is inserted, and a conversation is counted when it is created.

## Limit checks

`AIUsageLimitService.enforceUsageLimits` runs when a message is sent, after validation:

1. Rate: refuse if the user sent more than `MaxMessagesPerUserPerMinute__c` in the last minute.
2. Concurrent conversations, for a new conversation, if the behaviour blocks.
3. Daily conversations, for a new conversation, if the behaviour blocks.
4. Daily tokens: `Block New Messages` refuses every message; `Block New Conversations Only` refuses only a new conversation; `Notify Only` never refuses.
5. The org's async queue: refuse when too many `AIMessageProcessingQueueable` jobs are already queued or running, so AI Assist cannot crowd out other queueables.

The same service reports usage meters and the reached limit to the chat window, so it can warn the user before they press Send.

## The conversation lock and concurrency

Only one message per conversation is processed at a time. `AIConversationLockService` stores an expiry time in `ProcessingLockedUntil__c`; a future time means locked. Each change reads the row with `FOR UPDATE` so two callers cannot change it together. If a job and its finalizer both fail to release the lock, it expires after `ProcessingLockSeconds__c` and the next message takes over. A message sent while the conversation is locked is saved and picked up by the running job's finalizer. The state diagram is in [Message lifecycle](message-lifecycle.md).

## Queueing when awaiting capacity

`MaxMessagesInFlight__c` on `AIAssistSettings__c` caps how many turns run org-wide. When the cap is reached, the message is saved as `Queued` with `IsAwaitingCapacity__c` set and the lock is released. It starts when a place is free:

- A queueable runs as the user who enqueued it and reads the conversation in user mode, so only the sender can start their held message. The chat window's poll does this (`startHeldMessage`).
- A message held longer than 5 minutes is failed as `Service Busy`, by the poll, by the finalizer or by the daily maintenance job, so the user is offered Try again.

## Polling cost and known issue [1]

The chat window polls `getConversationUpdate` while a reply is pending. [Known issue 1](../runbooks/known-issues.md) records that one call measured about 21 SOQL queries in a test, partly because the usage policy lookup runs again on every call. Each call is its own request, so none is near the limit of 100. The concern is the total across many users: about 200 concurrent users is the target and no load test has been run. The options listed in the issue, cheapest first, are to cache the policy lookup, make the poll return only a "changed" marker, back off further, or add a platform event that only wakes the window. Status: open.
