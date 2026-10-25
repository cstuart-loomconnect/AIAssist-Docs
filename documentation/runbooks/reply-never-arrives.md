# A reply never arrives

A user sent a message and no answer came back. Work through the four steps in order. The first step finds the message and tells you which of the others to read.

You need the `AIAssistAdminUser` or `AIAssistSuperUser` permission set. Messages are private to their owner, so look at them as an admin who can read all conversations (both sets can). For how a message travels, see the [message lifecycle](../architecture/message-lifecycle.md).

## 1. Find the message

1. Open the **AI Conversations** tab and find the user's conversation (filter by owner, or by the time they sent it).
2. Open its **AI Conversation Messages** related list and find the user's newest message (`Sender` = `User`).
3. Read **Processing Status**, **Is Awaiting Capacity** and **Failure Reason**.

| Processing Status | What it means | Where to go |
|---|---|---|
| **Failed** | The turn ended with an error. The user sees a message matching the reason, and a **Try again** button. | Step 2 |
| **Queued** with **Is Awaiting Capacity** ticked | Held because the org-wide cap on messages in flight is reached. It starts when a place frees up, and fails as `Service Busy` after 5 minutes. | [Messages are queued or refused](queued-or-refused.md) |
| **Queued**, not awaiting capacity | The job is waiting for its turn or is running. A message stays Queued from the send until the reply is saved. | Steps 3 and 4 |
| **Processing** for more than a few minutes | See the note below. | Steps 3 and 4 |
| **Complete** but the user saw nothing | The reply was saved. The problem is on the display side. | See below |

!!! warning "To confirm"
    The Processing Status picklist has a `Processing` value, but no code in `force-app` sets it: a message goes from Queued straight to Complete or Failed. A message showing Processing was set by hand or by something outside the package. Confirm whether the value is meant to be used.

**Complete but nothing seen.** Check, in this order:

1. Is there an **AI Agent** message after the user's message? If not, look at the Failure Reason and Platform Logs.
2. Is the reply marked **Is Superseded**? A superseded reply was replaced by a regenerated one and is hidden on purpose.
3. Is the conversation **Closed** (for example idle timeout or message limit)? The user has to start a new one.
4. Is **Chat window enabled** off, or **Maintenance mode** on, in the AI Assist UI settings? See [Settings](../admin-guide/settings.md).
5. Ask the user to reload the page. The window polls for the reply, and a window closed mid-reply picks it up when reopened.

## 2. Read the failure

The Failure Reason is one of these values. The user sees a different plain-English message for each.

| Failure Reason | Usual cause | Fix |
|---|---|---|
| **Authentication Failed** | The provider refused the key or the account: HTTP 401 or 403, an invalid key, a permission error or an exhausted quota. Never retried. | Check the API key in the Named Credential and the billing on the provider account. |
| **Model Retired** | The provider no longer has the model: HTTP 410, `model_not_found`, a deprecated or decommissioned model, or a 404 that mentions the model. Never retried. | Edit the model on the **AI Agent Models** tab and set a current model ID. |
| **Rate Limited** | HTTP 429 from the provider. Retried, with a one minute delay from the third attempt. | Wait and try again. If it keeps happening, raise the provider rate limit or lower **Messages in flight**. |
| **Timeout** | The provider took too long (HTTP 408 or 504, or "timed out"). Also set when a job started after its processing lock had expired. | Raise **Callout timeout** (the platform allows at most 120,000 ms) or **Processing lock** in [Settings](../admin-guide/settings.md). |
| **Provider Error** | Any other provider failure, such as a 5xx, or a reply that could not be read. Retried when the status is in **Retryable status codes**. | Check the provider's status page, then the Platform Log entry for the HTTP status. |
| **Configuration Error** | A setup problem: the endpoint is not allowed, the Named Credential is missing, or the model or settings are incomplete. Not retried. | Check the Named Credential name on the model, the API path, and that the model is active. Test it on the **AI Agent Models** tab. |
| **PII Masking Failed** | Masking failed for a field, so the request was **not sent**. The message names the object and field. | See [A PII registry sync failed](pii-sync-failed.md) and check the object in the **AI PII Registry** tab. |
| **Limit Reached** | The model kept calling tools until it hit the maximum number of tool-calling iterations without a final answer. | Raise the agent's **Max Tool Calling Iterations** (up to the cap in Settings), or simplify the agent's tools. |
| **Service Busy** | Held at the cap on messages in flight for more than 5 minutes and never started. | Raise **Messages in flight**, and check the maintenance job and the async queue (step 4). |
| **Other** | An unexpected failure, including a job killed by a governor limit. | Open the **AI Platform Logs** tab and find the entry for that time. |
| **Request Blocked** | The value exists and has a user message, but no code in `force-app` sets it. | See the note below. |

!!! warning "To confirm"
    `Request Blocked` is a picklist value with a label ("This request was blocked because it breaks an AI Assist usage rule") and a case in `AIMessageOutcomeService`, but nothing in the code assigns it. Confirm whether it is reserved for a future rule.

The reason alone is often not enough. For detail:

- **AI Platform Logs** (`AIPlatformLog__c`) hold the class, method, exception and message for each caught error.
- If the user's usage policy has **Should Capture Execution Steps** on, the reply carries an execution trace. If **Debug Mode Enabled** is on, the request and response JSON are stored on the message.

After you fix the cause, the user can press **Try again**. It re-runs their newest message and passes all the usual checks again.

## 3. Check the lock

Only one message per conversation is processed at a time. The lock is the **Processing Locked Until** field on the conversation (`ProcessingLockedUntil__c`): a time in the future means locked, blank or past means free.

| What you see | Meaning | What to do |
|---|---|---|
| Blank, or a past time | Not locked. | Look elsewhere (steps 1, 2 and 4). |
| A future time, and a job is running | Normal. A reply is being prepared. New messages from the user wait behind it. | Wait. |
| A future time, and no job is running | A job and its finalizer both failed without releasing the lock. | Wait until it expires. The next message the user sends then takes it over. The length is **Processing lock** in Settings (30 to 3,600 seconds). |

!!! note "Do not clear the lock by hand"
    A job that starts after its lock has expired stands down and fails its message as `Timeout`, so clearing or editing the field while a job is queued can fail a message that was about to work. Let it expire.

## 4. Check the async queue

Replies are produced by a queueable job, `AIMessageProcessingQueueable`, one per message.

1. In **Setup > Apex Jobs**, filter on **Apex Class** `AIMessageProcessingQueueable`.
2. A job in **Queued** or **Preparing** for a long time means the org's async queue is backed up. Check **Setup > Apex Flex Queue** and what else is running.
3. **Failed** jobs show the error in **Status Detail**. The same error is in the Platform Logs.
4. New messages are refused with "AI Assist is busy, try again shortly" when 200 of these jobs are queued or running. See [Messages are queued or refused](queued-or-refused.md).

If no job exists for a Queued message and its conversation is not locked, press **Try again** as the user, or ask them to send the message again.

Held messages (Is Awaiting Capacity) are failed by the maintenance job if no chat window starts them. If you see old ones, see [The maintenance job is not running](maintenance-job.md).
