# Known issues

Problems that are known and not yet fixed. This page is the record of them: add new issues here, in the AIAssist-Docs repo, with a `docs:` pull request. The open count on [Codebase health](../codebase-health.md) is read from the table below. Each issue keeps its number, so other notes can refer to it as [1], [2] and so on. New issues are added at the end, and numbers are never reused.

| # | Issue | Status |
|---|---|---|
| [1] | Chat polling costs about 21 SOQL queries per call | Open, not started |
| [2] | Model switching between templates was dropped; its code is still in `AIAgentManager` | Open, not started |
| [3] | The AI Prompt Templates tab has not been seen in a browser | Open |
| [4] | A turn that outlives its lock can be answered twice, or leave the next message unstarted | Open, not started |
| [5] | The tool loop ignores the 120 second callout budget per transaction | Open, not started |
| [6] | An Apex data source that writes anything breaks every later callout in the turn | Open, not started |
| [7] | The SOQL runner can skip its LIMIT when the validator says it will add one | Open, not started |
| [8] | A suggested action can be run again and again from the same reply | Open, not started |
| [9] | Restoring PII replaces stand-ins inside other words | Open, not started |
| [10] | PII mappings stop saving once a conversation's JSON reaches 131,072 characters | Open, not started |
| [11] | Anthropic Agent API sessions are never deleted at the provider | Open, not started |
| [12] | Estimate token tracking undercounts what a turn really costs | Open, not started |
| [13] | The idle timeout is not checked when a message is sent | Open, not started |
| [14] | GDPR erasure has no tool, and four decisions in the runbook are unresolved | Open, not started |
| [15] | Text the user types is sent to the provider unmasked | Open, not started |
| [16] | The usage limits have never been load tested | Open, not started |
| [17] | Settings allow values the platform cannot honour | Open, not started |
| [18] | The chat trusts the object name the browser sends | Open, not started |
| [19] | The utility bar chat loads its context twice on first open | Open, not started |

## [1] Chat polling costs about 21 SOQL queries per call

Found: 2026-10-21, while fixing `AIChatControllerTest.testScenario14` (it passed 100 queries because 8 controller calls shared one test block).

**What happens**

The chat window polls `AIChatController.getConversationUpdate` while a reply is pending. Measured in that test, one call to `getConversationUpdate` takes about 21 queries, and `openConversation` takes about 15 to 21. Each call is its own request, so none is near the 100 query limit. The cost is the total across many users: about 200 concurrent users is the target, and no load test has been run.

**Where the queries go**

Part of the cost is the usage policy lookup, which runs again on every call (`AIChatStateService.getUsagePolicy`, `AIUsagePolicyService.getUsagePolicy`, `AIUsagePolicyService.getUsagePoliciesForUser`).

**Options, cheapest first**

| Option | What it means |
|---|---|
| a | Cache the usage policy lookup for the length of the request, or per user. |
| b | Make the poll lighter: return only a "changed since" marker, and load the messages only when something changed, so a poll that finds nothing new needs a couple of queries. |
| c | Slow the backoff further when a reply is slow. |
| d | Add a platform event that only wakes the window (carries the conversation Id, no content), so it polls once when a reply is ready. The window still needs a fallback poll, because a held message can only be started by its sender's poll. |

**Decided against:** a platform event that carries the reply, a PushTopic or Change Data Capture (about 200 times the delivery to every subscribed client, and it cannot safely carry the content).

**Before shipping:** run a 200 user load test.

**Status:** open, not started.

## [2] Model switching between templates was dropped; its code is still in `AIAgentManager`

Found: 2026-10-21, while building the AI Prompt Templates tab.

**What happens**

Templates are now shared between agents (`AIAgent__c.AIPromptTemplate__c`), so the model has no per-agent list of templates to switch between. `AIPromptTemplateService.getPromptTemplateChoice` always returns an empty `routingTemplates` list, so the `select_prompt_template` tool is never offered. A slash command can still ask for any active template by its API name.

**What is left**

The routing code in `AIAgentManager` (the `routingPromptTemplates` argument, the `select_prompt_template` tool, `AgentResult.selectedPromptTemplateId` and `Version`), the `PROMPT_TEMPLATE_*` constants, and the matching tests in `AIAgentManagerTest` and `AIMessageProcessingQueueableTest`. It is dead code until removed or given a new source of templates.

**Status:** open, not started.

## [3] The AI Prompt Templates tab has not been seen in a browser

Found: 2026-10-21.

The components deploy and the Apex is tested (preview, save, publish impact, archive, default, test messages, Try it). No LWC tests were written, and the layout, the Insert bar cursor handling, the record picker and the blank-valued "Default (fallback)" option in the archive dialog have not been checked in a browser.

**Status:** open.

## [4] A turn that outlives its lock can be answered twice, or leave the next message unstarted

Found: 2026-10-25, bug review of `development`.

**What happens**

The conversation lock is only a time (`ProcessingLockedUntil__c`) with no owner. `AIMessageProcessingQueueable` checks it once, when the job starts, and `AIMessageProcessingFinalizer` always calls `releaseOrHandOffLock` when the job ends. Two things follow:

- **Answered twice.** If a running turn takes longer than `ProcessingLockSeconds__c` (it can be set as low as 30 seconds, and a busy async queue adds delay), the lock expires mid-turn. A new message then takes the lock and starts its own job. When the first job ends, its finalizer sees that newest message is not the one it processed and hands the lock to it again, so a second job answers the same message. Two replies, double the tokens, and the first finalizer can also clear a lock the second job is relying on.
- **Never started.** If a job starts after its lock expired, it fails its own message as a timeout and returns without handing on. A message the user sent while that job was waiting stays `Queued` with no job behind it and no "reply on its way" shown, until the user presses Try again.

**Options**

| Option | What it means |
|---|---|
| a | Give the lock an owner: store the triggering message Id with the lock, and only let the finalizer that owns it release or hand it on. |
| b | Re-check ownership just before the outcome is recorded, and stand down without saving if another message owns the lock. |
| c | On the stale-lock path, still hand on to a newer waiting message instead of returning. |
| d | Validate `ProcessingLockSeconds__c` against the longest possible turn (see [5]) on the settings page. |

**Status:** open, not started.

## [5] The tool loop ignores the 120 second callout budget per transaction

Found: 2026-10-25, bug review of `development`.

**What happens**

Salesforce allows 120 seconds of callout time in total per transaction. `AIAgentManager.executeAiMessage` sets every callout to the full `CalloutTimeoutMilliseconds__c`, and the settings page allows up to 50 tool-calling iterations. A turn with three or four slow model calls runs out of budget, and the platform's "exceeded maximum time allotted for callout" error does not contain "timed out", so it is classed as a provider error and retried. The retry runs the whole turn again from the start: every data source is re-run and every token is spent again.

**Options**

| Option | What it means |
|---|---|
| a | Track the callout time used and set each callout's timeout to what is left of the 120 seconds (less a margin); stop the loop with a clear limit failure when too little is left. |
| b | Classify the budget error as `Timeout` and not retryable. |
| c | Cap `MaxToolCallingIterationsCap__c` to a realistic number, or warn on the settings page when iterations × timeout is over 120 seconds. |

**Status:** open, not started.

## [6] An Apex data source that writes anything breaks every later callout in the turn

Found: 2026-10-25, bug review of `development`.

**What happens**

Data sources run inside the tool loop, between callouts. `AIDataSourceDispatcher` runs a subscriber's `IAIDataSourceExecutor` with no guard, so if that class does any DML (a log record, a "last viewed" stamp), the next callout throws "You have uncommitted work pending". That is classed as a provider error and retried, and the retry fails the same way, spending tokens each time. Nothing tells the admin the data source is the cause.

**Options**

| Option | What it means |
|---|---|
| a | Take `Limits.getDmlStatements()` before and after the executor; if it changed, roll back to a savepoint and fail the tool call with a configuration error naming the data source. |
| b | Document on `IAIDataSourceExecutor` that executors must be read-only, and check this in the AI Tools "Test" button. |

**Status:** open, not started.

## [7] The SOQL runner can skip its LIMIT when the validator says it will add one

Found: 2026-10-25, bug review of `development`.

**What happens**

`AISoqlTemplateValidator` looks for a LIMIT at the top level only (quoted text and sub-queries blanked out), and only warns when there is none, because "the runner adds one". `AISoqlTemplateRunner` uses a plain `\bLIMIT\b` search over the whole text. A template whose only LIMIT is inside a sub-query (`(SELECT Id FROM Contacts LIMIT 5)`) or inside quoted text (`Subject LIKE '%limit%'`) passes validation with a warning, then runs with no outer LIMIT. Every matching row is loaded before being cut to Max Rows in memory, which can hit the 50,000 row or heap limit and kill the turn.

**Options**

| Option | What it means |
|---|---|
| a | Make the runner use the validator's top-level text (quotes and brackets blanked) to decide whether to add a LIMIT. |
| b | Always wrap: if the top-level LIMIT is missing or above Max Rows, replace or append it. |

**Status:** open, not started.

## [8] A suggested action can be run again and again from the same reply

Found: 2026-10-25, bug review of `development`.

**What happens**

`AIChatController.runSuggestedAction` checks the user owns the reply and that it has a suggested action, then runs it. Nothing records that the action already ran, so a double click, a second tab or a direct call runs a write action (create a task, send an email, update a record) as many times as it is called. The controller also always passes `isConfirmed = true`, so `RequiresConfirmation__c` is only enforced by the chat window, not by the server.

**Options**

| Option | What it means |
|---|---|
| a | Refuse a second run when the reply's trace already has a `Success` workflow action step (or add a field such as `SuggestedActionRunAt__c` and lock the reply row while checking it). |
| b | Pass the user's actual confirmation from the window to the server, and refuse a `RequiresConfirmation__c` action without it. |

**Status:** open, not started.

## [9] Restoring PII replaces stand-ins inside other words

Found: 2026-10-25, bug review of `development`.

**What happens**

`AIChatDebugService.restorePii` swaps each stand-in for its real value with `String.replace`, longest first. That matches anywhere in the text, not just whole words. A stand-in such as "Lee" turns "Leeds" into "*real name*ds", "Ann" changes "Annual", and so on. It can also chain: if one restored real value happens to equal another stand-in, the next pass replaces it again. The user sees a reply with a real customer's details in the wrong place, and the same restore is used for the exported transcript.

**Options**

| Option | What it means |
|---|---|
| a | Replace on word boundaries only (a regex with `\b` around the quoted stand-in). |
| b | Replace in one pass, so a restored value is never matched again. |
| c | Stop picking substitutes that are common words or prefixes of common words, or use stand-ins with a marker the model will copy (for example `Morgan Reyes⁽¹⁾`). |

**Status:** open, not started.

## [10] PII mappings stop saving once a conversation's JSON reaches 131,072 characters

Found: 2026-10-25, bug review of `development`.

**What happens**

`AIPiiMappingService` keeps every real-to-fake pair for a conversation in one `MappingJson__c` long text field (131,072 characters). A long conversation that reads many records fills it. From then on the upsert fails and is only logged. The turn still succeeds, so the reply is saved with stand-ins that can never be restored, and the next turn gives the same real value a different stand-in, so the model sees two "people" where there is one.

**Options**

| Option | What it means |
|---|---|
| a | Chunk the mapping across child rows (the chunking design noted for knowledge sources). |
| b | Treat a failed mapping save as a masking failure, so the turn fails rather than saving a reply that can never be restored. |

**Status:** open, not started.

## [11] Anthropic Agent API sessions are never deleted at the provider

Found: 2026-10-25, bug review of `development`.

**What happens**

For the Anthropic Agent provider, the conversation history is kept at the provider and referenced by `AIConversation__c.ExternalReference__c`. `AIConversationRetentionBatch` and the [GDPR deletion runbook](gdpr-deletion.md) delete the Salesforce records only. The session at the provider, which holds every message (masked data source results, but the user's own typed text as written), outlives both retention and an erasure request.

**Options**

| Option | What it means |
|---|---|
| a | Before deleting a conversation with an external reference, call the provider's delete endpoint (from a queueable, as the batch cannot call out after DML), and log any that fail. |
| b | Until then, add it to the GDPR runbook as a manual step and to the data map. |

**Status:** open, not started.

## [12] Estimate token tracking undercounts what a turn really costs

Found: 2026-10-25, bug review of `development`.

**What happens**

With `TokenTrackingMethod__c = Estimate`, the tokens counted against the conversation and the user's daily `AIUsage__c` are the length of the user's message plus the length of the reply, divided by four. Every callout really sends the system prompt, tool definitions, up to 100,000 characters of history and every tool result, and a turn can make several callouts. On a long conversation the real spend can be ten times the counted figure or more, so `MaxTokensPer24Hours__c` and `MaxTokensPerConversation__c` do not protect cost in this mode.

**Options**

| Option | What it means |
|---|---|
| a | Count the provider's reported input and output tokens for the reply in every mode, and use the estimate only for the pre-send check. |
| b | If Estimate must stay, estimate the whole request (system prompt, history, tool results), not just the two message bodies. |

**Status:** open, not started.

## [13] The idle timeout is not checked when a message is sent

Found: 2026-10-25, bug review of `development`.

**What happens**

`IdleTimeoutMinutes__c` is only enforced by the chat window and by `AIConversationIdleBatch`, which runs once a day at 2am. `AIConversationMessageService.sendMessage` continues any Active conversation it is given, and for an agent with one conversation per record it finds the Active one without looking at the last message time. So a user who comes back hours after a 30 minute timeout carries on the old conversation, while the concurrency limit (`countActiveConversations`) already treats it as closed. The two disagree, and the old history is still sent to the model.

**Options**

| Option | What it means |
|---|---|
| a | In `sendMessage`, close a candidate conversation that is past its agent's idle timeout (reason Idle Timeout) and start a new one, the same way the message and token caps are handled. |

**Status:** open, not started.

## [14] GDPR erasure has no tool, and four decisions in the runbook are unresolved

Found: 2026-10-26, phase 1 readiness review.

**What happens**

An erasure request is handled by hand: a Super User runs the Apex in the [GDPR deletion runbook](gdpr-deletion.md) through Execute Anonymous. Nothing records that it was done, the order of deletion depends on the person following the page, and four steps are marked **To confirm**:

1. Who verifies the requester and where the request is logged.
2. Whether a legal hold overrides an erasure request, and who may untick it.
3. Whether usage rows, terms acknowledgments and platform logs are deleted, kept or anonymised.
4. How saved notes, posts and tasks made from the chat are found for a user.

Provider-side sessions ([11]) are also not covered.

**Options**

| Option | What it means |
|---|---|
| a | Get a ruling from the data protection lead on the four decisions and write them into the runbook. Needed for phase 1 either way. |
| b | Add an `AIErasureService` that takes a user Id, deletes in the right order, honours the legal hold rule, and writes an audit `AIPlatformLog__c` entry with counts (never values). |

**Status:** open, not started.

## [15] Text the user types is sent to the provider unmasked

Found: 2026-10-26, phase 1 readiness review.

**What happens**

Only data source results go through `AIPiiPseudonymizationService`. The user's own message, and the earlier messages in the history, are sent to the provider exactly as typed. A user who pastes a customer's name, address, date of birth or account number into the chat sends it to the provider in clear, and for the Anthropic Agent provider it is kept in the provider's session ([11]).

**Options**

| Option | What it means |
|---|---|
| a | Record it as a known limitation: tell the data protection lead, and state it in the terms the user accepts. |
| b | Mask values in typed text that match the open record's PII fields (the real values are known for that record). |
| c | Add pattern checks for obvious identifiers (email, phone, National Insurance number, sort code and account number) and either mask them or warn before sending. |

**Status:** open, not started.

## [16] The usage limits have never been load tested

Found: 2026-10-26, phase 1 readiness review.

**What happens**

The rate, daily, concurrency, in-flight and pending-job limits are built and unit tested, but nothing has shown they hold at the target of about 200 concurrent users. Polling alone costs about 21 SOQL queries per call ([1]), and `countQueuedMessageJobs` queries `AsyncApexJob` on every send. Whether the org's async queue, concurrent request limit and the providers' rate limits keep up is unknown.

**What to do**

Run a load test in a full sandbox: 200 simulated users, each sending messages and polling as the chat window does, over at least 30 minutes. Record the turn times, failures by reason, async queue depth and org limit use, and keep the results with this issue.

**Status:** open, not started.

## [17] Settings allow values the platform cannot honour

Found: 2026-10-26, phase 1 readiness review.

**What happens**

- `MaxMessagesInFlight__c` accepts up to 9,999, but `MAX_PENDING_PROCESSING_JOBS` refuses new work at 200 queued jobs. Any cap above 200 never holds a message: users get "Service busy" instead of being queued.
- `ProcessingLockSeconds__c` accepts 30 to 3,600 seconds with no check against how long a turn can take (iterations × callout timeout, plus queue delay). A lock shorter than a turn leads to [4].
- `MaxToolCallingIterationsCap__c` accepts up to 50, which combined with the callout timeout cannot fit in one transaction ([5]).

**Options**

| Option | What it means |
|---|---|
| a | Lower the ranges on the settings page: in-flight at most 200, iterations to a realistic cap. |
| b | Add cross-field checks: refuse a lock time shorter than the longest possible turn, and warn when iterations × timeout is over 120 seconds. |

**Status:** open, not started.

## [18] The chat trusts the object name the browser sends

Found: 2026-10-26, while tracing how the utility bar finds the page's record.

**What happens**

`AIChatContextService.buildRecordContext` uses the `objectApiName` passed from the browser in preference to the object it describes from the record Id (`String.isNotBlank(objectApiName) ? objectApiName : describedObject`). The agent list and the PII protected flag are then worked out from that name. A changed request could open an Account record with agents meant only for another object, or show the record as not PII protected.

**Fix**

Always use the object described from the record Id, and ignore the browser's value when a record Id is given.

**Status:** open, not started.

## [19] The utility bar chat loads its context twice on first open

Found: 2026-10-26, while tracing how the utility bar finds the page's record.

**What happens**

In the utility bar, `aiAssistChat.connectedCallback` calls `loadContext()` straight away, before the `CurrentPageReference` wire has given it the record. That call goes to `getChatContext` with no record, and the wire then starts a second call with the record. The `loadSequence` counter throws the first answer away, so nothing wrong is shown, but every first open pays for an extra server round trip and may briefly show the no-record state.

**Fix**

In the utility bar, skip the load in `connectedCallback` and let the page reference wire start it.

**Status:** open, not started.
