# Using the chat

AI Assist adds a chat window to Salesforce record pages and the utility bar. You ask questions about the record you have open, and the assistant answers using the data your admin has connected. This page is for everyone who uses the chat.

## Open the chat and send a message

1. Open a record page that has the AI Assist chat, or the AI Assist utility bar item.
2. Type in the message box ("Ask about this record, or type / for commands") and click **Send**.
3. A "Working on it" indicator shows while the reply is written. Click **Stop** if you do not want to wait.

The assistant knows which record you have open. Personal details on the record, such as names, emails and phone numbers, are swapped for placeholders before anything is sent to the AI model, and swapped back in the answer you see. The bar at the top of the chat shows **PII protected** when this is on.

!!! note
    AI can make mistakes. Check before acting.

If you see a message such as "AI Assist isn't set up for you", "No AI agent is set up here" or "AI Assist is down for maintenance", the chat is not available to you yet. Contact your Salesforce admin.

## Terms

The first time you use the chat, you may see "A few things to know about AI Assist". Read it, tick the box to agree to the AI usage policy, and click **Agree and continue**. You are asked again when your admin raises the terms version.

## The menu

The buttons at the top are **New**, **End**, **History** and **Usage**, with a **More options** menu. If more than one agent is available on the page, you can **Switch AI agent**.

| Action | What it does |
|---|---|
| **New conversation** | Starts a fresh conversation. It is greyed out ("disabled by admin") when your admin has paused new conversations. |
| **End conversation** | Closes the conversation. You cannot send more in it, but it stays in your history and you can still export it. |
| **Export conversation** | Saves the transcript as a text file, if your admin allows it. |
| **Share conversation** | Lets a colleague read it (see below), where the agent allows sharing. |

## History

Click **History** to browse past conversations. Search, or filter by **This record** and **All records**. A **Shared with me** tab appears when colleagues have shared conversations with you. Conversations are grouped by date and show a status such as Active, Closed, Timed out or Limit reached. Open one to read it, or choose **Continue conversation** if it can be resumed. Conversations are deleted after the retention period your admin sets.

## On a reply

Under each reply you can:

- Rate it **Helpful** or **Not helpful**. For not helpful you pick a reason (**Not accurate**, **Missing info**, **Wrong record**, **Too long** or **Other**) and can add a comment.
- **Copy** the text.
- **Regenerate** it. This is only on the newest reply of an open conversation.
- **Save to record**: **Save to Notes** adds the text as a note on the record, and **Create Task** makes a task for you on the record. You can edit the text first. This needs a record the conversation is about.
- Open **Sources** where the reply lists them.

If a reply fails, you see "Couldn't reach the AI service. Nothing was lost" with **Try again**.

## Share a conversation

Choose **Share conversation**, search for a person by name and click **Share**. People you share with can read the conversation. They cannot reply or change it, and they need access to the record it is about. Remove access from the same dialog. The person must have an active AI Assist user setup, or they will not be found.

## Slash commands

Type `/` (or click the slash button) to see a list of commands, then use the arrow keys and Enter to pick one. Commands are shortcuts your admin has set up, such as `/risk-check`. You see only what you typed; the full instructions are added behind the scenes. Which commands you see depends on the record and your role. On a new conversation, the first few are suggested for the record. See [prompt templates and slash commands](../admin-guide/prompt-templates.md) for how admins create them.

## Suggested actions

Sometimes a reply includes a **Suggested action**, such as updating a record. The assistant can only suggest it. Nothing happens until you act.

- Choose **Edit first** to change the values, **Confirm** to run it, or **Dismiss** to decline.
- Actions that change data ask you to confirm first.
- A **Screen Flow** action opens in a window over the chat. Complete the screens and press **Finish**. Finishing is the confirmation.

Actions run with your own permissions. Depending on settings they show as cards or inline buttons.

## Usage limits

Your admin can limit how much you use AI Assist each day. The chat shows a counter of today's allowance in the message footer, and **Usage** ("Your AI usage today") shows each limit with how much is left.

| When you reach a limit | What you see |
|---|---|
| **Notify only** | A warning. You can keep chatting. |
| New conversations blocked | "New conversations are paused." You can carry on in your current conversation. |
| All messages blocked | "You cannot send messages until your allowance resets." You can still read your conversations. |

If you cannot send at all and no limit has been reached, ask your admin to check that you have a usage policy. See [policies](../admin-guide/policies.md).
