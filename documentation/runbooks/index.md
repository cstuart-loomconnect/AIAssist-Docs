# Runbooks

Step-by-step fixes for the things that go wrong. Find the symptom in the table, then follow the page. Most steps need the `AIAssistAdminUser` or `AIAssistSuperUser` permission set and access to Setup.

| Symptom | Runbook |
|---|---|
| A user sent a message and no reply came back | [A reply never arrives](reply-never-arrives.md) |
| The chat shows an error such as "AI Assist could not sign in", "model is no longer available" or "took too long" | [A reply never arrives](reply-never-arrives.md), step 2 (Failure Reason table) |
| A message is stuck on Queued, or "AI Assist is busy, try again shortly" | [Messages are queued or refused](queued-or-refused.md) |
| A user is turned away before sending: no access, terms, limits, new chats paused | [Messages are queued or refused](queued-or-refused.md) |
| Old conversations are not being deleted or closed, or nothing runs overnight | [The maintenance job is not running](maintenance-job.md) |
| An object on the AI PII Registry tab shows Failed, or fields are not being masked | [A PII registry sync failed](pii-sync-failed.md) |
| Someone asks for their data to be erased | [GDPR deletion request](gdpr-deletion.md) |
| You hit something odd that looks like a known limitation | [Known issues](known-issues.md) |

## Before you start

- Messages and conversations are private to their owner. Use a Super User, or an Admin with the **View All** access the Admin set grants on conversations, to see them.
- Errors that are caught are written to **AI Platform Logs**. Check there first when the screen gives no detail: it names the class, method and exception.
- For how a message travels, read the [message lifecycle](../architecture/message-lifecycle.md). For what limits apply, read [Usage limits and throughput](../architecture/usage-limits.md).

!!! note "Pages marked To confirm"
    Where a runbook says **To confirm**, the code does not settle the question. Answer it for your org and write the answer down.
