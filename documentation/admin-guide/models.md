# AI Agent Models

The **AI Agent Models** tab holds the connections to AI providers. Each model is one connection: a provider, a model ID and the named credential that calls it. [Agents](agents.md) pick one in the wizard.

!!! note "Who can use this tab"
    You need the **AI Assist Manage Settings** custom permission, the same one as the [Settings tab](settings.md).

## The model list

Models are listed on the left, active ones first. Each row shows the provider and how many active agents use it ("not used" when none). Click **+ New model** to add one. A model that is not saved yet is marked **Draft**.

There is no delete button. To retire a model, switch it off.

## Adding a model

1. Click **+ New model**.
2. Pick a **Provider** card (see below).
3. Fill in the fields (see the table).
4. Click **Test connection**, then **Save**.

### Providers

| Card | Meaning |
|---|---|
| **Anthropic** | Messages API. Claude models. |
| **AnthropicAgent** | Managed agents. Needs an **Environment ID**. |
| **OpenAI** | Chat Completions API. |

Picking a card fills in the API path and the version header for that provider.

### Fields

| Field | What it means |
|---|---|
| **Active** | Whether agents can use this model. See "Test on activation". |
| **Name** | What you and the agent wizard call the model. Required. |
| **Model** | The provider's own model ID, for example `claude-sonnet-5-5`. Required. |
| **Named credential** | Picked from the named credentials in Setup. The API key lives in the credential, never on this record. Required. |
| **API path** | Where on the provider the message is sent. Must start with a single `/` and hold no host name, spaces, `..` or `//`. |
| **Environment ID** | Only for AnthropicAgent: the Anthropic environment the agent session runs in. Required for that provider. |
| **Version header** and **Version value** | The provider's API version header, filled in from the provider card. |
| **Max output tokens** | Longest reply the model may write. A whole number of 1 or more. |
| **Temperature** | 0 up to the provider maximum (2, or 1 for Anthropic). Lower is more predictable. |

## Test on activation

**Test connection** sends one short message ("Reply with OK") through the named credential and uses a few tokens. A pass shows "Connected." with the reply time and token counts. A failure shows the reason and hints, for example an authentication error or a model that is not available.

The test also runs on **Save** in two cases:

- You switch a model on.
- A model that is already on has its connection fields changed (provider, model, named credential, API path, version header, environment ID).

What happens when it fails:

| Situation | Result |
|---|---|
| New or switched-off model | Saved, but kept **Inactive**. You see "Model saved, but it is still switched off because the connection test failed." |
| Live model with a changed connection | Nothing is saved. The live model keeps its saved connection. |

Changes to name, max output tokens or temperature alone do not trigger a test on a live model.

## Switching a model off

Use the **Active** toggle. If active agents use the model, a dialog lists each agent with its number of users and a **Move to** list of other active models. Pick a model for every agent, then click the button that moves the agents and switches the model off.

- Agents that are inactive are left alone.
- Open conversations switch to the new model from their next message.
- If there is no other active model, switch another one on first.

Saving a model as off while active agents use it is refused. Always use the toggle.

!!! warning
    A model that is off cannot answer. An active agent pointing at it would stop answering, which is why the move is forced.

See [providers](../architecture/providers.md) for how the connection is used at run time.
