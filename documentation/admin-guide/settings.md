# Settings

The **AI Assist Settings** tab is where you switch AI Assist on or off, set message and provider limits, and control how the chat window looks and behaves. It edits two sets of settings, each on its own tab.

!!! note "Who can use this tab"
    You need the **AI Assist Manage Settings** custom permission (`AIAssistManageSettings`). The AI Assist Admin and AI Assist Super User permission sets both grant it. Without it, every action on the tab is refused with an access message. See [permission sets](../reference/permission-sets.md).

## The two settings tabs

| Tab | What it controls | Levels |
|---|---|---|
| **AI Assist Settings** | The engine: limits, provider calls, tool calling, terms, PII sync. | Org-wide for everything. Five limits can also be set for a profile or user. |
| **AI Assist UI Settings** | The chat window: what it shows and whether it is on. | Org-wide, Profiles and Users. |

## Org-wide, Profiles and Users

Each tab has three sub-tabs: **Org-wide**, **Profiles** and **Users**.

- **Org-wide** applies to everyone. There is always one, and it cannot be deleted.
- **Profiles** lists the profiles that have their own row ("Profiles with a row"). Use **Find a profile to add** to start one.
- **Users** lists the users that have their own row. Use **Find a user to add** to start one.

The most specific row wins: a user row beats a profile row, which beats the org-wide row. A new row starts as a copy of the org-wide values and is not saved until you click **Save**. **Delete row** puts that profile or user back on the org-wide values.

## AI Assist Settings

Changes are kept as a draft until you click **Save**. Numbers outside the allowed range are refused with a message.

| Group | Setting | What it does |
|---|---|---|
| Availability | AI Assist enabled | The master switch. Off stops all of AI Assist. |
| Message limits | Maximum message length | Longest message a user can send, 1 to 99,999 characters. Blank uses the system maximum. |
| | Messages per user per minute | Stops one user flooding the queue, 1 to 999. Blank means no limit. |
| | Messages in flight | Messages being answered at once across the org, 1 to 9,999. Extra messages wait as Queued. Blank means no cap. |
| | Processing lock | Seconds a conversation stays locked while a reply is built, 30 to 3,600. After this the next message takes over a stuck lock. |
| AI provider calls | Callout timeout | Milliseconds to wait for the provider. Salesforce allows at most 120,000. |
| | Retry attempts | Extra tries after a retryable failure, 0 to 5. |
| | Retryable status codes | Comma-separated codes (100 to 599). Some codes are never retried whatever is listed. |
| | Success status codes | Any other code is treated as a failure. Required. |
| Tool calling | Default iterations | Rounds of tool calls an agent may use if it does not set its own, 1 to 50. |
| | Iteration cap | No agent can go above this, 1 to 50. Must be at least the default. |
| | Tool calls per iteration | How many tools the model may ask for in one step, 1 to 20. |
| Terms and policy | Current terms version | Raise it (for example 1.0 to 1.1) to make everyone accept the terms again. Blank means users are not asked to accept terms. |
| | AI usage policy URL | Link shown on the terms screen. |
| PII | Registries per sync run | A lower number spreads the [PII registry](pii-registry.md) sync over more runs, 1 to 20. |

### The five limits you can override

Only these five settings can be set on a **Profiles** or **Users** row. The rest stay org-wide.

1. Maximum message length
2. Messages per user per minute
3. Default iterations
4. Iteration cap
5. Tool calls per iteration

On a profile or user row the three tool-calling numbers must be filled in. A blank message length or messages-per-minute on such a row is not filled from the org-wide value: it means "system maximum" and "no limit" for that profile or user.

!!! note
    Daily token and conversation limits are not here. They belong to [usage policies](policies.md).

## AI Assist UI Settings

| Group | Setting | What it does |
|---|---|---|
| Availability | Chat window enabled | Shows or hides the chat window. |
| | Maintenance mode | The chat shows a maintenance message and accepts no new messages. |
| Chat window | Feedback buttons | Thumbs up and down on each reply. |
| | Typing indicator | Animated dots while a reply is written. |
| | Show execution trace | Replaces the dots with a step card listing what the agent is doing. |
| | Show timestamp on messages | Adds a time to each message. |
| | Workflow actions | Lets agents suggest workflow actions in chat. |
| | Show actions inline | Runs actions from buttons in the message instead of a separate card. Needs **Workflow actions** on. |
| | Suggested actions display | **Cards** or **Inline Buttons**. |
| | Messages shown per page | 1 to 200. Older messages load as the user scrolls up. Blank uses the built-in page size. |

For how these look to end users, see [Using the chat](../home/using-the-chat.md).

## Setting up an exception

1. Open **AI Assist Settings** and choose the tab you want.
2. Open the **Profiles** or **Users** sub-tab.
3. Search for the profile or user and select it.
4. Change the values and click **Save**.
5. To undo it, select the row and click **Delete row**.
