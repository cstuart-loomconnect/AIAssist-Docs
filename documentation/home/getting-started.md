# Getting started

This page takes an org from nothing to a working chat window. Follow the steps in order: each one needs the one before it.

You need the [Salesforce CLI](https://developer.salesforce.com/tools/salesforcecli) and an API key for an AI provider (Anthropic or OpenAI).

## 1. Install

AI Assist is installed from source. Use a sandbox or a scratch org.

=== "From source (sandbox or scratch org)"

    Clone the repository, log in to the org and deploy everything in `force-app`:

    ```bash
    sf org login web --alias ai-assist
    sf project deploy start --source-dir force-app --target-org ai-assist
    ```

=== "New scratch org"

    You need a Dev Hub. The scratch org definition is `config/project-scratch-def.json`.

    ```bash
    sf org create scratch --definition-file config/project-scratch-def.json --alias ai-assist --set-default --duration-days 7
    sf project deploy start --source-dir force-app
    ```

!!! note "No package version yet"
    `sfdx-project.json` names a package called `AIAssist` (version `0.1.0.NEXT`) but has no package version recorded in `packageAliases`, so there is nothing to install from a package link yet.

## 2. Assign permission sets

There are three permission sets. Assign them from **Setup > Permission Sets**, or with `sf org assign permset --name AIAssistAdminUser`.

| Permission set | Give it to | What it unlocks |
|---|---|---|
| `AIAssistUser` | Everyone who chats | Chat with agents, give feedback, accept the usage terms. Only their own conversations. |
| `AIAssistAdminUser` | The people who set AI Assist up | Everything in User, plus agents, prompts, tools, models, policies, the PII registry and the settings tabs. They cannot read other people's messages or PII mappings. |
| `AIAssistSuperUser` | Oversight, and anyone running the Apex tests | Read, create, edit and delete on every AI Assist object, and the settings. |

Admins also need `AIAssistUser` to chat. See [Permission sets](../reference/permission-sets.md) for every object and field.

## 3. Connect an AI provider

AI Assist never stores an API key. It calls the provider through a **Named Credential** (with an External Credential behind it) and sends each request to `callout:<named credential><API path>`.

1. In **Setup > Named Credentials**, create a credential for your provider.
2. Set its URL to the provider's address: `https://api.anthropic.com` for Anthropic, `https://api.openai.com` for OpenAI.
3. Make the credential add the key header the provider expects:

    | Provider | Header | Value |
    |---|---|---|
    | Anthropic and AnthropicAgent | `x-api-key` | the API key |
    | OpenAI | `Authorization` | `Bearer ` followed by the API key |

4. Give the users who will chat access to the credential through the External Credential's principal (a permission set). Callouts run as the user who sent the message.

!!! warning "To confirm"
    How the principal's permission set should be granted to chat users (the three AI Assist permission sets do not list an External Credential principal) is not recorded in the repository. Check this in your org: a missing principal shows up as a Configuration Error on the message.

## 4. Create a model

A model is one connection: a provider, a model ID and the named credential.

1. Open the **AI Agent Models** tab in the AI Assist app.
2. Click **+ New model**, pick the provider, fill in the fields and pick the named credential from step 3.
3. Click **Test connection**, then **Save**. A model whose test fails is saved but kept inactive.

Details are in [AI Agent Models](../admin-guide/models.md).

## 5. Create a usage policy

A user can only chat when an active usage policy applies to them. Without one they see "AI Assist has not been set up for your user".

1. Open the **AI Policies** tab.
2. Create a policy and mark it **Default** so it covers everyone who has no policy of their own.
3. Set the limits you want (tokens per 24 hours, conversations per 24 hours, open conversations) and what happens when one is reached.

See [AI Policies](../admin-guide/policies.md).

## 6. Create an agent

1. Open the **AI Agent Wizard** tab.
2. Pick the model from step 4, choose which objects the agent works on (blank means a general agent), and decide who can use it (**All AI Assist Users** or **Assigned Users Only**).
3. Make the agent **Active**. An agent cannot be active without a model.

See [Agents and the Agent Wizard](../admin-guide/agents.md).

## 7. Schedule the maintenance job

The package has one scheduled job, `AIMaintenanceScheduler`. Nothing schedules it for you. Without it, retention, idle-conversation closing, stuck-message cleanup and PII registry syncs never run.

Run this once in **Developer Console > Debug > Open Execute Anonymous Apex**:

```apex
AIMaintenanceScheduler.scheduleDaily();
```

It runs every day at 02:00 in the time zone of the user who scheduled it. It does nothing if a job named `AI Assist Maintenance` already exists. See [The maintenance job is not running](../runbooks/maintenance-job.md).

## 8. Set the usage terms

Users must accept the usage terms before their first chat.

1. Open the **AI Assist Settings** tab.
2. Under **Terms and policy**, set **Current terms version** (for example `1.0`) and the **AI usage policy URL** shown on the terms screen.

If the version is blank, users are not asked to accept anything. Raising the version later makes everyone accept again. See [Settings](../admin-guide/settings.md).

## 9. Add the chat window to a page

The component is called **AI Assist Chat** (`aiAssistChat`). It can go in two places:

- **Utility bar:** in **App Manager**, edit the app, open **Utility Items** and add **AI Assist Chat**.
- **Record page:** in the Lightning App Builder, drag **AI Assist Chat** into a region at least 320px wide. The properties are the agent (blank picks the first active agent for the object), the height and the accent colour.

A user's policy can limit the channels they chat from (**Allowed Channels**; blank means all). Leave the **Channel** property at its default so it matches.

## 10. Check it works

1. Sign in as a user who has `AIAssistUser` and an agent assigned (or an agent set to **All AI Assist Users**).
2. Open the page with the chat window and accept the terms.
3. Send a short message. A reply should appear within a few seconds.

If it does not, start with [A reply never arrives](../runbooks/reply-never-arrives.md) or [Messages are queued or refused](../runbooks/queued-or-refused.md).

!!! tip "Load sample data"
    In a sandbox or scratch org, `scripts/load-sample-data.sh [org alias]` loads sample settings, agents, tools, rules, conversations and custom metadata so every object has something in it. It runs the five scripts in `scripts/apex/sample-data` in order. The running user needs all three permission sets. It refuses to run outside a sandbox or scratch org, and is safe to run again. Model configurations are only made active where the org already has a matching Named Credential.
