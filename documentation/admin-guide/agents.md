# Agents and the Agent Wizard

An agent is an AI assistant set up for record pages. It uses a [model](models.md), can read [data sources](ai-tools.md), can suggest workflow actions, and is offered only to the users you choose. The **AI Agent Wizard** tab is the guided way to create and change agents.

## The agent list

The wizard opens on a list of every agent. Use the **All**, **Active** and **Draft** filters or the search box (name, page or model). Columns are Name, Status, Pages, Model, Users and Last changed. A hint under an agent says "Can't activate: ..." or "Needs fixing: ..." when a blocker is present, or "n things need a look" for warnings.

Click **+ New agent** to start. You can begin with a **Blank agent** or **Copy an existing agent**, which clones its settings, data sources and actions.

!!! note "Existing items only"
    The wizard only links things that already exist. It never creates models, data sources or workflow actions. Build those first on [AI Agent Models](models.md) and [AI Tools](ai-tools.md).

## Access mode and assignments

| Access mode | Who can use the agent |
|---|---|
| **Assigned users only** (the default) | Only the users and permission sets you add as assignments. Anyone else is refused. |
| **All AI Assist users** | Anyone with the AI Assist User permission set. |

On the Access step, click **+ Add** to assign a user or a permission set. Use **Check a user** to type a name and see whether they will have access. The step also shows how many users will see the agent on each page, and tells you if another agent on the same object means those users get an agent picker in the chat window.

## The wizard steps

| Step | What you decide |
|---|---|
| 1. **Basics** | **Agent name**, **API name** (letters, numbers and underscores, starting with a letter; filled from the name), **Description** (for admins only), **Record pages it appears on**, **Prompt template**, **Persona and rules**, **Greeting**. |
| 2. **Model** | Which active model the agent uses. **Test again** checks the connection. You can **Skip for now** and save as a draft. |
| 3. **Data sources** | What the agent can read. Add from existing data sources. |
| 4. **Workflow actions** | What the agent can suggest. Write actions always ask the user first. |
| 5. **Conversations** | When a conversation loads (**On chat window open**, **On page load**, **Manual only**), resume, one active conversation per record, who can see conversations (Private or Global), idle close time, retention days and what retention counts from. |
| 6. **Limits** | Max messages, max tokens and max tool-calling rounds per conversation, and how tokens are counted (**Estimate** or **Track actual usage**). |
| 7. **Access** | Access mode and assignments, and the **Active** toggle. |
| 8. **Review** | Checks, a summary with **Edit** links, and **Try it before activating**. |

Notes on the steps:

- **Limits** apply per conversation. [Usage policies](policies.md) apply on top, and the stricter one wins.
- **Global** conversation visibility can show one user's chat, including record data, to another user with this agent. Use it only where users share the same access.
- **Try it** uses the model, prompt template and persona only. Data sources and workflow actions are not used.

## Saving and activating

The last buttons are **Save as draft** (or **Save changes** on a live agent) and **Activate agent**. A new agent is not saved until you finish. Each check is either a **Blocker**, which stops activation, or a **Warning**, which does not stop saving.

Blockers: no name, no API name (or a bad or taken one), no object chosen, no model, or limits that are not positive numbers. Activation is refused while any blocker remains, but you can always save a draft.

Editing a live agent: changes apply when you click **Save changes**. Conversations already open keep their old settings until they close.

## Traps

!!! warning "Common reasons an agent does nothing"
    - **Data source and workflow action links must be active.** The wizard sets this for you. If you link items by hand on the Agent Data Source or Agent Workflow Action records, they default to inactive and the agent will not see them.
    - **The data source or action itself must be active.** An inactive one is linked but not offered. The Review step warns "Item is switched off".
    - **A user needs an active usage policy to send.** With no active policy (and no default policy active) a user can read but not send. The warning is "No usage policy is active". See [policies](policies.md).
    - **Assigned users only with no assignments** means nobody can use the agent ("Nobody is assigned").
    - **Workflow actions switched off** in the [UI settings](settings.md) means the agent cannot run them.
    - **The model must be active.** A switched-off model means the agent cannot answer.
    - **Object mismatch.** A data source or action tied to an object the agent does not appear on is not offered there.
    - **Flow with no active version** will fail when run.
    - **No prompt template** (none chosen and no default) leaves the agent without a prompt.
    - Only 64 data sources and 64 workflow actions per agent reach the model.
