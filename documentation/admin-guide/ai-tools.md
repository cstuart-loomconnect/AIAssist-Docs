# AI Tools

The **AI Tools** tab is where you build the things an [agent](agents.md) can use beyond plain conversation. It has two sub-tabs, **Data Sources** and **Workflow Actions**. You need the **AI Assist Manage Settings** custom permission to use it.

## Two kinds of tool

| | Data source | Workflow action |
|---|---|---|
| **Purpose** | Lets the model **read** Salesforce data. | Lets the user **do** something. |
| **Who decides** | The model decides when to call it and fills in the inputs. | The model can only **suggest** it. Only the user can run it. |
| **Built from** | A SOQL query or an Apex class. | An Apex class, an autolaunched flow or a screen flow. |
| **Safety** | Queries run in user mode, so users only ever get data they could already see. Results are masked by the [PII registry](pii-registry.md) before the model sees them. | **Write** actions always ask the user to confirm first. A screen flow opens in a window and the user pressing Finish is the confirmation. |

The wording the model reads to decide when to use a tool is the **Description for the agent** you write on the Details step. Write it as an instruction to the model.

## Data sources

The list shows each data source with its Type, Object, Binding, Max rows, number of agents, Last tested and Status. Filter by **All**, **SOQL**, **Apex** or **Inactive**. Click **+ New data source** to open the wizard.

### The wizard

| Step | What you decide |
|---|---|
| **Type** | **SOQL query** or **Apex class**. And whether it is **Bound to the open record** (`:recordId` is filled from the page and a record must be open) or **Unbound** (offered anywhere, the agent supplies every input). |
| **Query** or **Apex class** | For SOQL, build the query with the **Visual builder** or **Write SOQL**, and set **Max rows**. For Apex, pick a class from the list. |
| **Inputs** | For each bind, tell the agent what it means. Choose who fills it: **The page** or **The agent**. |
| **Test** | Pick a record if the source is bound, optionally **Run as** another user, and click **Run test**. |
| **Details** | **Name**, **API name**, **Description for the agent**, **What comes back**, the object it returns (optional) and **Active**. |

### SOQL templates

The query is checked as you type. Problems show as errors or warnings with a suggested fix.

- Only a single `SELECT` is allowed, for example `SELECT Id, Name FROM Account`.
- Objects and fields must exist and be readable by you. A wrong field name gets a "did you mean" suggestion.
- Sub-queries can be only one level deep, and the object name cannot be a bind.
- **Max rows** is a `LIMIT` of 1 to 200. A query with no `LIMIT` gets one added (warning). A `LIMIT` over 200 is an error.
- `:recordId` is an error in an unbound source and a warning if a bound source never uses it.
- A hard-coded record ID is a warning. Use a bind instead.
- Other binds become inputs. Binds are values, never pasted into the query text.

The visual builder only shows simple queries: one object, plain fields, AND filters, one order by and a limit.

### Apex classes

The list shows only classes that implement `IAIDataSourceExecutor`. If none exist, a developer must write one first; use SOQL until then. A class that also implements `IAIDataSourceInputDescriber` describes its own inputs, and the Inputs step is filled in for you. See the [developer guide](../developer-guide/extending.md).

Inputs the agent sends that are not declared are dropped before the query or class runs.

### Testing

The test runs the source as you, or as another user to check what they would get. **Run as** checks field access from that user's permission sets. It is not a full impersonation, and record sharing is not simulated.

| Result | Meaning |
|---|---|
| **Passed** | Ran and returned rows (or ran and returned none). |
| **Partial** | Ran, but fields were removed because the user has no read access. This is safe behaviour: fix permissions, not the query. |
| **Failed** | The source could not run. The reason is shown. |

The test also shows what the agent would receive after PII masking.

## Workflow actions

The list shows Runs, Changes data, Target, In agents, Last tested and Status. Filter by **All**, **Write**, **Read only** or **Needs attention** (for example a flow with no active version, or one that changed since it was tested).

### The wizard

| Step | What you decide |
|---|---|
| **Type** | What runs it (**Apex**, **Autolaunched flow** or **Screen flow**) and whether it is **Read only** or **Write**. |
| **Flow or class** | Pick an active flow (only active ones are listed) or an Apex class implementing `IAIWorkflowActionExecutor`. |
| **Inputs** | For each input: filled by **The page** (the open record's Id), **The agent**, the current user, or a fixed value. Agents can only pass text, numbers, dates and booleans. |
| **Confirmation** | The confirmation message and which inputs to show. Write actions are locked to require confirmation. |
| **Test** | Pick a record, keep **Roll back** on, and **Run test**. |
| **Details** | **Name**, **API name**, **Description for the agent**, **What comes back**, **Active**. |

!!! warning "Testing writes data"
    **Roll back** undoes the records a test changed, but not callouts, emails or platform events. Only a sandbox lets you turn roll back off. A screen flow cannot be tested here: save it, give it to an agent, and open it from the chat.

## Saving a change to a tool agents use

- **Data source:** if active agents use it, you must test it before saving. If the test fails, the change is **not saved** and the current version keeps running. A dialog lists the affected agents and offers **Save and test**.
- **Workflow action:** a dialog tells you how many active agents use it and that the change is live as soon as it is saved.

An inactive tool can be saved and tested, but agents cannot use it. A tool must also be linked to the agent, and the link must be active (the wizard does this): see [Agents](agents.md).
