# Admin guide

This guide is for the people who set up and look after AI Assist in your org. It walks through each tab in the **AI Assist** app, who can see it, and the order to set things up in.

## The tabs in the AI Assist app

| Tab | What it is for | Page |
|---|---|---|
| **AI Agent Wizard** | Create and change agents step by step. | [Agents](agents.md) |
| **AI Agents** | The raw agent records. | [Agents](agents.md) |
| **AI Tools** | Data sources the model can read and workflow actions the user can run. | [AI Tools](ai-tools.md) |
| **AI Prompt Templates** | Write, test and publish the instructions agents follow. | [Prompt templates](prompt-templates.md) |
| **AI Agent Models** | Connections to AI providers. | [Models](models.md) |
| **AI Policies** | Daily limits and what users can do. | [Policies](policies.md) |
| **AI PII Registry** | Which fields are masked before data leaves Salesforce. | [PII registry](pii-registry.md) |
| **AI Assist Settings** | Switches, limits and chat window options, at org, profile and user level. | [Settings](settings.md) |
| **AI Conversations**, **AI Feedback**, **AI Platform Logs** | Records of what happened, for review and support. | [Reference](../reference/data-model.md) |

The tabs of the first group are custom pages. Most of them also need the **AI Assist Manage Settings** custom permission to do anything (see [Settings](settings.md)).

## Who sees what

Access comes from three permission sets. Assign them to people; do not change them in place. The full object and field list is in the [permission set reference](../reference/permission-sets.md), and the design is in the [security model](../architecture/security-model.md).

| Permission set | For | What it gives |
|---|---|---|
| **AI Assist User** (`AIAssistUser`) | Everyone who chats | Use the chat. Read access to agents, their own conversations and feedback. No admin tabs. |
| **AI Assist Super User** (`AIAssistSuperUser`) | The people who oversee AI Assist | Everything in User, plus full access to every object, field and setting. The tabs listed above are visible by default. |
| **AI Assist Admin** (`AIAssistAdminUser`) | The people who build and maintain it | Everything in User, plus managing agents, prompts, data sources, actions, models, policies, the PII registry and settings. It cannot read other users' messages or PII mappings, or delete audit data. |

Both Admin and Super User grant the **AI Assist Manage Settings** custom permission. Slash commands can also be limited to Super Users and Admins, or Admins only: see [prompt templates](prompt-templates.md).

!!! warning "To confirm"
    In the permission set source, the Super User set shows all the custom tabs as visible, but the Admin set lists only **AI Prompt Templates**, **AI Policies** and **AI PII Registry** (as available), not **AI Agent Wizard**, **AI Tools**, **AI Agent Models** or **AI Assist Settings**. Admins may need those tabs added another way. Also, `AIPromptTemplatesController` is not listed in any of the three permission sets. Confirm that the Prompt Templates tab works for a non-System-Administrator.

## Recommended order of setup

Each step needs the one before it.

1. **Assign permission sets.** Give your admins **AI Assist Admin** and your users **AI Assist User**.
2. **Review the settings.** Check **AI Assist enabled** and the chat window options on [Settings](settings.md).
3. **Connect a model.** Add a model on [AI Agent Models](models.md) and make sure its connection test passes.
4. **Create a usage policy.** On [AI Policies](policies.md), create one and make it the default. Without an active policy users can read but not send.
5. **Register the objects that hold personal data.** On the [AI PII Registry](pii-registry.md), add them and wait for the sync to finish.
6. **Build tools.** Create [data sources and workflow actions](ai-tools.md) and test them. Skip this for a first, chat-only agent.
7. **Write a prompt template.** On [AI Prompt Templates](prompt-templates.md), write one and make it the default.
8. **Create and activate an agent** with the [Agent Wizard](agents.md). Assign users or choose all AI Assist users.
9. **Try it.** Use **Try it before activating** in the wizard, then open the chat on a record page. Share [Using the chat](../home/using-the-chat.md) with your users.

For installation and scheduling steps that are not on a tab, see [Getting started](../home/getting-started.md).
