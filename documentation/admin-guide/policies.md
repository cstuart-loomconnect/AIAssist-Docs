# AI Policies

The **AI Policies** tab manages usage policies. A usage policy caps how much each user can use AI Assist and decides what they can do. You assign policies to permission sets for teams, or to a single user for an exception. You need the **AI Assist Manage Settings** custom permission to use the tab.

!!! warning "A user with no policy cannot send"
    A user needs at least one active usage policy that applies to them, either assigned or through a default policy. With none, they can read their conversations but cannot send. Always keep an active default policy.

## The policy list

Policies are listed on the left; the default one carries a **Default** pill. Each has two tabs, **Settings** and **Assignments**. Click **+ New policy** to create one. A new policy is not saved until you click **Save**.

## Settings

| Section | Setting | What it does |
|---|---|---|
| (top) | **Name**, **Description**, **Active**, **Default** | Active off stops the policy applying without deleting it. Default applies it to everyone with no assignment of their own. |
| **Daily limits** | **Tokens per 24 hours** | Input and output tokens across all of a user's conversations. |
| | **Conversations per 24 hours** | New conversations a user can start. |
| | **Open conversations at once** | Across all records. |
| **When a limit is hit** | See below. | |
| **What users can do** | **Start a chat themselves** | Off means only automated or suggested prompts. |
| | **Export conversations** | Lets the user export a conversation transcript. |
| | **See conversations** | **My Conversations Only**, **My Subordinates Conversations** or **All Conversations**. |
| | **Channels** | **Record Page Chat**, **Utility Bar**, **Mobile**. Tick none to allow every channel. |
| **Debugging** | **Debug mode** | Shows the execution trace under replies. |
| | **Capture execution steps** | Saves each tool call for QA review. Uses storage. |

Limits must be whole numbers above zero. Leave a limit blank for no limit.

The three limits live only on policies. For exceptions, assign the user a different policy rather than looking for a per-user setting.

## When a limit is reached

Pick one behaviour per policy:

| Behaviour | What happens |
|---|---|
| **Block new messages** | The user is stopped straight away and cannot send until their allowance resets. They can still read their conversations. |
| **Block new conversations only** | The user can finish what they are doing but cannot start anything new. |
| **Notify only** | The user sees a warning but can carry on. |

A conversation limit (daily or open) only ever blocks new conversations. A token limit blocks every message only under **Block new messages**. The chat shows a usage banner and a "Your AI usage today" panel, see [Using the chat](../home/using-the-chat.md). Usage resets each day.

## Assignments

On the **Assignments** tab, click **+ Add assignment** and choose **User** or **Permission set**. The list shows each assignment's type, who it is for, **Users covered** and whether it is active. A user assignment is shown as overriding their permission sets.

How a user's policy is chosen:

1. **User assignment.** If the user has their own, only those count.
2. **Permission set assignment.** Otherwise policies assigned to any permission set they hold.
3. **Default policy.** Otherwise the default.

The first level that has anything wins. If several policies tie at that level, the stricter one (lowest daily token limit) applies. When more than one policy applies, limits take the lowest number and the most blocking behaviour, while abilities such as channels, export and debug mode are allowed if any policy allows them, and the widest conversation visibility is used.

## Check a user

Type a name in **Check a user** to see which policy they get, why, and every other policy that could have applied with its source, daily tokens and conversations. There is an **Assign ... to this user** shortcut. Use this first when someone says they cannot send.

## Deleting a policy

Click **Delete policy**. If users are assigned, you must choose what happens to them: **Move them to the default policy** or **Move them to another policy**, then **Move users and delete**. Their usage so far today still counts, and the new limits apply from their next message.

- The default policy cannot be deleted. Make another policy the default first.
- If no other policy exists, create one first.

Related: [usage limits architecture](../architecture/usage-limits.md) and the runbook [queued or refused](../runbooks/queued-or-refused.md).
