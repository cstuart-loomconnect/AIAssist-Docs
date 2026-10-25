# GDPR deletion request

A person asks for their data in AI Assist to be erased. This page lists where a user's data lives, how deletion cascades, what the retention batch already does, and a procedure. Steps that need a decision are marked **To confirm**: they are not settled in the code and need a ruling from your data protection lead.

!!! warning "Not legal advice"
    This page describes what the package does. Whether a record must be erased, kept on legal hold or kept for another lawful reason is a decision for your organisation. Agree the decision before you delete anything: deleted data can be hard to get back.

## Where a user's data is held

| Object | What it holds about the user | Link to the user | Deleted with the conversation? |
|---|---|---|---|
| `AIConversation__c` | The conversation itself: the related record, channel, and an external session id for some providers (`ExternalReference__c`). | Owner | This is the parent. |
| `AIConversationMessage__c` | Everything the user typed and the replies. Also the debug request and response JSON and the execution trace, when those were captured. | Master-detail to the conversation | **Yes.** |
| `AIPIIMapping__c` | A JSON map of every real value to its fake value for the conversation. This contains the **original** personal data. | Master-detail to the conversation | **Yes.** |
| `AIPIIMaskingRecord__c` | What was masked on each message: object, field, rule and a count. No values. | Master-detail to the message | **Yes**, through the message. |
| `AIFeedback__c` | A thumbs rating, a reason and a free-text **Comment**. | Lookups to the conversation and the message, set to blank on delete | **No.** The feedback survives with its links blanked. |
| `AIUsage__c` | One row per user per day: token and conversation counts. No content. | Lookup to the user | No. |
| `AITermsAcknowledgment__c` | The version accepted, the date and the typed full name used as a signature. | Lookup to the user | No. |
| `AIPlatformLog__c` | Error details: class, method, exception message, stack trace, the related record Id. | Lookup to the user | No. |
| `AIAgentAssignment__c`, `AIUsagePolicyAssignment__c` | Who may use which agent or policy. Configuration, not content. | Lookup to the user | No. |

Also outside these objects:

- **Conversation shares.** A user can share a conversation read-only with others. The share rows go when the conversation is deleted.
- **Text saved to records.** A user can save a reply to the record the conversation is about, as a note, a Chatter post or a task (`AIChatSaveToRecordService`). That copy lives on the record, not in AI Assist, and is **not** deleted with the conversation.
- **The AI provider.** Messages are sent to the provider with personal data masked, but the provider may keep what it received. For the AnthropicAgent provider, the session is kept on the provider's side and `ExternalReference__c` holds its id.
- **Workflow action results.** An action may have changed a record or sent an email. Those changes are not undone by deleting the conversation.
- **Salesforce recycle bin and backups.** Deleted records sit in the recycle bin until it is emptied.

!!! note "Users cannot be deleted"
    Salesforce does not delete User records, only deactivates them. The user lookups above are set to blank when a user is deleted, which does not happen in practice, so `AIUsage__c`, terms and log rows stay linked to a deactivated user until you delete them yourself.

## What deletion does by itself

`AIConversationRetentionBatch` runs from the daily [maintenance job](maintenance-job.md). It deletes feedback first (because it would otherwise be left behind), then conversations whose **Retention Expiry Date** is today or earlier and whose **Is On Legal Hold** is not ticked. Deleting a conversation removes its messages, masking records and PII mappings.

The expiry date comes from the agent: **Conversation Retention Days** counted from the **Retention Trigger** (conversation created date, closed date, or last message date). A blank retention, or one under 1 day, means no expiry date, so the conversation is kept indefinitely. Changing the agent's retention starts a recalculation batch for all its conversations.

The retention batch is not a right-to-erasure tool: it does not look at who a conversation belongs to. It also never touches `AIUsage__c`, terms or platform logs.

## Procedure

You need a user with `AIAssistSuperUser`. It is the only permission set with delete on conversations, messages, feedback, PII mappings, usage, terms and logs. `AIAssistAdminUser` cannot delete these.

### 1. Confirm the request

Confirm who is asking and which Salesforce user they are. Note their User Id. Decide, with your data protection lead, whether it covers all their AI Assist data or particular conversations.

!!! warning "To confirm"
    Who verifies the requester, and how the request is logged, is outside the package. Record the request, the decision and the date elsewhere: AI Assist does not keep an audit record of manual deletions.

### 2. List what exists

Run these in the Developer Console **Query Editor**, replacing the Id:

```sql
SELECT Id, Name, Status__c, CreatedDate, IsOnLegalHold__c, RetentionExpiryDate__c, ExternalReference__c, RelatedObjectAPIName__c, RelatedRecordId__c FROM AIConversation__c WHERE OwnerId = '005XXXXXXXXXXXX'
SELECT Id, Comment__c FROM AIFeedback__c WHERE CreatedById = '005XXXXXXXXXXXX'
SELECT Id FROM AIUsage__c WHERE User__c = '005XXXXXXXXXXXX'
SELECT Id FROM AITermsAcknowledgment__c WHERE User__c = '005XXXXXXXXXXXX'
SELECT Id, ClassName__c, ExceptionMessage__c FROM AIPlatformLog__c WHERE User__c = '005XXXXXXXXXXXX'
```

Use a Super User, because conversations are private to their owner.

### 3. Resolve legal holds

A conversation with **Is On Legal Hold** ticked is skipped by the retention batch. Nothing in the package sets or clears this field: it is edited by hand.

!!! warning "To confirm"
    Does a legal hold override an erasure request, and who may untick it? The code does not stop a Super User deleting a conversation that is on hold: only the retention batch honours the flag. Decide the rule and follow it by hand.

### 4. Delete the feedback, then the conversations

Order matters: feedback first, then the conversations (which also removes their messages, PII mappings and masking records). Run as a Super User in **Execute Anonymous Apex**:

```apex
Id userId = '005XXXXXXXXXXXX';
List<AIConversation__c> conversations = [SELECT Id FROM AIConversation__c WHERE OwnerId = :userId AND IsOnLegalHold__c = FALSE];
delete [SELECT Id FROM AIFeedback__c WHERE AIConversation__c IN :conversations];
delete conversations;
```

The snippet only covers conversations not on hold and feedback attached to them. Feedback the user gave on **someone else's** shared conversation, and feedback whose conversation link was already blanked, is found by the `CreatedById` query in step 2 and deleted separately.

### 5. Delete the rest

Delete the usage, terms and log rows from the step 2 queries once your decision says to.

!!! warning "To confirm"
    Usage rows feed the daily limits. The terms acknowledgment is the evidence that the user accepted the terms. Deleting the terms row means a user who is still active is asked to accept again. Platform logs may contain what the user typed, because exception text can. Decide for each whether to delete or keep (for example, anonymise).

### 6. Clear what the package does not

- Delete notes, Chatter posts and tasks the user saved from a reply, on the records they were saved to.
- Ask the AI provider to delete anything it holds, using its own process. For AnthropicAgent, use the session ids from `ExternalReference__c` (take a copy before step 4).
- Empty the recycle bin for the deleted records if the request requires hard deletion.

!!! warning "To confirm"
    The package has no way to find saved notes, posts and tasks for a user. Decide how you will locate them (for example by creator and date).

### 7. Check

Re-run the step 2 queries. All should return no rows (except anything you chose to keep). Keep your own record of the request and the result.

## Related

- [PII protection](../architecture/pii-protection.md): what is masked before text reaches the provider.
- [Security model](../architecture/security-model.md)
- [Data model](../reference/data-model.md)
