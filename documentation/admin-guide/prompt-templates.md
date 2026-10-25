# Prompt templates and slash commands

A prompt template is the set of instructions that tells an agent how to behave: who it is, how it writes and what it must never do. The **AI Prompt Templates** tab is where you write, test and publish them. Slash commands are shortcuts users type in the chat that send a ready-made instruction.

## The template list

Templates are listed on the left with a status of **Live**, **Inactive** or **Default**, and the number of agents that use each one. Click **+ New template** to start one. An agent with no template of its own uses the default template.

## Writing a template

| Field | What it means |
|---|---|
| **Name** | What admins see in lists and pickers. |
| **API name** | A short name with no spaces, such as `MortgageAdviser`. Slash commands use it to ask for this template. Cannot be changed once the template is saved. |
| **Max response length (words)** | Most words in a reply. Empty means no limit. |

The wording is in four sections:

| Section | Purpose |
|---|---|
| **Context** | Who the agent is, who it helps and what the user is looking at. Comes first in every message. |
| **Tone** | How replies should sound. Optional. |
| **Instructions** | The main guidance. Required: a template cannot be saved without it. |
| **Never** | Hard rules, one per line. Put compliance rules here. |

A preview on the right ("What the model receives") shows the filled-in text and an estimate of tokens sent with every message.

### Merge fields

Use the **Insert** bar to add a merge field. Each is filled in for the conversation.

| Merge field | Value |
|---|---|
| `{!Agent.Name}` | The name of the agent answering. |
| `{!User.FirstName}` | The first name of the user chatting. |
| `{!Record.ObjectLabel}` | The kind of record the user has open, such as Opportunity. |
| `{!Record.Name}` | The name of the open record. |
| `{!Today}` | Today's date, in the user's format. |
| `{!Org.Name}` | The name of your organisation. |

A merge field that is not on this list is left as written.

## Publish, activate and archive

Saving a changed template makes a new version. The button reads **Create template** for a new one, or **Publish v** and the next version number for a live one. Before it goes live a dialog shows the agents it reaches, their users and open conversations, and how the saved test messages did. Open conversations switch to the new wording from their next message. Earlier versions are not kept.

| Action | What happens |
|---|---|
| **Archive** | Switches the template off. Each agent using it must be moved to another template, or to the default. The default template cannot be archived: make another one the default first. |
| **Activate** | Brings an archived template back. |
| **Make default** | Makes this template the fallback for agents with no template. It must be active. |

## Try It

The **Try it** tab sends a message to an agent with the saved wording and the edited wording, and shows both replies side by side (**Run both**). Pick an **Agent** and optionally an **On record**.

- **Save this message** keeps it as a saved test message. Mark a result **Better** or **Worse**.
- **Run all** runs every saved message on both wordings, as a quick check before publishing.

Only the wording is tested. No data sources or workflow actions are offered to the model.

## Used By

The **Used by** tab lists the agents using the template with their users, open conversations and status. Agents with no template of their own are shown as "uses the default". To change which template an agent uses, change it in the [Agent Wizard](agents.md).

## Slash commands

Slash commands are records of a custom metadata type, **AI Chat Command**. Create them in Setup under Custom Metadata Types, then Manage Records. There is no tab for them.

| Field | What it means |
|---|---|
| **Command** | What the user types, with the leading slash, for example `/risk-check`. Letters, numbers, hyphens and underscores only. |
| **Description** | One line shown under the command in the chat. |
| **Prompt Text** | The full instruction sent to the model. The user never sees it. |
| **Object API Name** | Only offer the command on this object's record pages. Blank offers it on any record. |
| **Agent Developer Name** | Only offer it with this agent. Blank offers it with every agent. |
| **Prompt Template Developer Name** | Make the command answer with this template. Blank leaves it to the agent's default. |
| **Available To** | **All Users**, **Super Users and Admins** or **Admins Only**, by the user's highest AI Assist permission set. |
| **Display Order** | Lowest first. Blank sorts last. The first three for an object are suggested on a new conversation. |
| **Is Active** | Turn off to hide the command without deleting it. |

Users see what they typed. The hidden instructions are added behind the scenes. See [Using the chat](../home/using-the-chat.md).
