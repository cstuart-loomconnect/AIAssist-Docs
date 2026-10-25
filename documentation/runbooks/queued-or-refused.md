# Messages are queued or refused

A user says their message "just sits there" or that the chat window turned them away. There are two different things to tell apart: a message that is **queued awaiting capacity**, and a message that is **refused** before it is saved.

| What the user sees | What happened | Section |
|---|---|---|
| The message is sent and a "waiting" state shows, then a reply or "AI Assist is busy, try again shortly" | The org is at its cap on messages in flight. The message is saved as Queued and held. | [Queued awaiting capacity](#queued-awaiting-capacity) |
| A red message and nothing is saved | A check refused the send. No message record exists. | [Refusals](#refusals) |

## Queued awaiting capacity

**Maximum Messages In Flight** in the [AI Assist settings](../admin-guide/settings.md) is an org-wide cap on messages being answered at once (blank means no cap). Over the cap, a new message is saved as **Queued** with **Is Awaiting Capacity** ticked, and its conversation lock is released.

- A held message can only be started by its own sender: from the finalizer of that user's earlier turn, or when their chat window asks for an update. If the window is closed, nothing starts it.
- After 5 minutes it is failed as `Service Busy` (the user sees "AI Assist is busy, try again shortly" and a **Try again** button).
- The daily maintenance job also fails held messages older than 5 minutes, up to 20 at a time. See [The maintenance job is not running](maintenance-job.md).

To count what is in flight, go to **Setup > Apex Jobs** and count `AIMessageProcessingQueueable` jobs in **Queued**, **Preparing** or **Processing**. If the count sits at the cap for long, either replies are slow (look at the provider and [A reply never arrives](reply-never-arrives.md)) or the cap is too low for the number of users. Raise **Maximum Messages In Flight**, or clear it.

A separate guard refuses new messages outright, with the same text, when 200 message jobs are already queued or running (the async queue is shared with the rest of the org).

## Refusals

These checks run when the user presses Send, in this order. A refusal is shown as plain text and nothing is saved, so there is no message to inspect. Ask the user which text they saw.

### Access and setup

| Message the user sees | Cause | Fix |
|---|---|---|
| AI Assist is switched off for your organisation. | **AI Assist enabled** is off in settings. | Switch it on in [Settings](../admin-guide/settings.md). |
| AI Assist is undergoing maintenance and will be back shortly. | **Maintenance mode** is on in the UI settings. | Switch it off. |
| AI Assist has not been set up for your user. | No active usage policy applies to the user. | Make a policy **Is Default**, or assign one to the user. See [AI Policies](../admin-guide/policies.md). |
| This AI agent is not currently active. | The agent's **Is Active** is off. | Activate the agent. |
| You haven't been given access to this AI agent. | The agent is **Assigned Users Only** and the user is not assigned. | Add an assignment in the Agent Wizard. |
| No AI agent is available for this record. | No active agent matches the object or the user. | Check the agent's objects and assignments. |
| You need to accept the AI Assist usage terms... / The usage terms have been updated... | The user has not accepted the **Current terms version**. | The user accepts the terms in the window. Raising the version in Settings asks everyone again. |
| AI Assist is not available from here for your user. | The channel (**Utility Bar** or **Record Page Chat**) is not in the policy's **Allowed Channels**. | Add the channel to the policy, or leave Allowed Channels blank for all. |
| You don't have access to the record this conversation is about. | The user cannot read the record. | Share the record, or this is working as intended. |
| Enter a message before sending. / Your message is too long. | Empty text, or over **Maximum message length** (never more than 8,000 characters). | Raise the setting, up to the system maximum. |

### Limits and pauses

| Message the user sees | Cause | Fix |
|---|---|---|
| You're sending messages too quickly. | More than **Maximum Messages Per User Per Minute** sent in the last 60 seconds. | Wait a minute, or raise the setting. |
| New conversations are paused. You can still read your existing ones. | The user's policy has **Is User Initiated Chat Enabled** off, and they are starting a new conversation. | Switch it on in the policy. |
| You have too many open conversations. Close one before starting another. | **Max Concurrent Conversations** reached. | The user closes one, or raise the limit. |
| You've reached your daily limit of new AI Assist conversations. | **Max Conversations Per 24 Hours** reached. | Wait for tomorrow, or raise the limit. |
| You've reached your daily AI Assist usage limit. | **Max Tokens Per 24 Hours** reached. | Wait for tomorrow, or raise the limit. |
| AI Assist is busy, try again shortly. | 200 message jobs are queued or running. | See above. |

How **Usage Limit Reached Behavior** on the policy changes what is refused:

| Behavior | Effect when a limit is reached |
|---|---|
| **Block New Messages** | The token limit blocks every message. Conversation limits block new conversations. |
| **Block New Conversations Only** | Only a new conversation is refused. Messages in an open conversation still go through. |
| **Notify Only** | The daily limits do not refuse anything. The per-minute rate limit and the queue guard still apply. |

"Day" means the org's own day, in the org's time zone, not the user's. The chat window shows a usage banner before the user presses Send, using the same checks.

To see what a given user is allowed, open the **AI Policies** tab and use its user check.

!!! note "A conversation that fills up"
    A conversation that reaches its agent's **Max Messages Per Conversation** or **Max Tokens Per Conversation** is closed automatically, and the next message starts a new conversation (which then goes through the checks above).

See [Usage limits and throughput](../architecture/usage-limits.md) for how the limits fit together.
