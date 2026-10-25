# Known issues

Problems that are known and not yet fixed. This page is the record of them: add new issues here, in the AIAssist-Docs repo, with a `docs:` pull request. The open count on [Codebase health](../codebase-health.md) is read from the table below. Each issue keeps its number, so other notes can refer to it as [1], [2] and so on. New issues are added at the end, and numbers are never reused.

| # | Issue | Status |
|---|---|---|
| [1] | Chat polling costs about 21 SOQL queries per call | Open, not started |
| [2] | Model switching between templates was dropped; its code is still in `AIAgentManager` | Open, not started |
| [3] | The AI Prompt Templates tab has not been seen in a browser | Open |

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
