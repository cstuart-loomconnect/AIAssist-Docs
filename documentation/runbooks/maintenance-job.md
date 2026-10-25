# The maintenance job is not running

AI Assist has one scheduled job, `AIMaintenanceScheduler`, which runs the daily housekeeping. Nothing schedules it for you: it exists only after someone runs `AIMaintenanceScheduler.scheduleDaily()`. This page shows how to check it, restart it and know what stops without it.

## What stops working without it

| Task | What goes wrong if it never runs |
|---|---|
| Fail held messages | Messages held at the cap on messages in flight, whose sender never reopened the chat window, stay Queued instead of failing as `Service Busy` after 5 minutes. |
| Retention (`AIConversationRetentionBatch`) | Conversations past their **Retention Expiry Date** are never deleted, except on legal hold. This matters for GDPR: see [GDPR deletion request](gdpr-deletion.md). |
| Idle conversations (`AIConversationIdleBatch`) | Conversations are not closed after their agent's **Idle Timeout Minutes**. |
| PII registry sync (`AIPiiRegistrySyncDispatcher`) | Registries are not synced when they are new, failed or past their cache reset date. See [A PII registry sync failed](pii-sync-failed.md). |

Chatting itself keeps working. This is a slow failure: nothing breaks on the day, and data piles up.

## What one run does

The job runs at 02:00 every day, in the time zone of the user who scheduled it (`0 0 2 * * ?`).

1. Fail messages held at the cap for more than 5 minutes (20 at a time at most).
2. Start the retention batch. This runs even when AI Assist is switched off, so switching it off never stops data expiring.
3. If AI Assist is on, start the idle conversation batch.
4. If AI Assist is on, hand the due PII registries to one worker job.

Each batch is started on its own with a batch size of 200. A batch that cannot start is logged and the others still run.

## 1. Check it is scheduled

In **Setup > Scheduled Jobs**, look for a job named **AI Assist Maintenance**. Check **Next Scheduled Run** is in the future.

Or run this in the Developer Console (**Debug > Open Execute Anonymous Apex**, then **Open Log**):

```apex
for (CronTrigger job : [SELECT State, NextFireTime, PreviousFireTime, CronJobDetail.Name FROM CronTrigger WHERE CronJobDetail.Name = 'AI Assist Maintenance']) {
    System.debug(job.State + ' next: ' + job.NextFireTime + ' last: ' + job.PreviousFireTime);
}
```

| You find | Meaning |
|---|---|
| No job | It was never scheduled, or it was deleted. Go to "Schedule it" below. |
| `WAITING` with a next run | Scheduled correctly. Go to step 2 to see whether it ran. |
| A previous run long ago and no next run | The job ended or was removed. Reschedule it. |

## 2. Check it ran

1. In **Setup > Apex Jobs**, look for `AIConversationRetentionBatch` and `AIConversationIdleBatch` around 02:00. The idle batch is missing when AI Assist is switched off, which is expected.
2. Open **AI Platform Logs** and filter on **Class Name** `AIMaintenanceScheduler`. An entry here means a batch could not start (the exception message says why).
3. Check a batch's own failures under its class name (`AIConversationRetentionBatch`, `AIConversationIdleBatch`).

If the job ran but did not do what you expected, check that the batch's conditions are met: retention only deletes conversations with a **Retention Expiry Date** on or before today that are not on **Is On Legal Hold**.

## 3. Schedule it (or reschedule it)

`scheduleDaily()` does nothing, and returns null, when a job with that name already exists. So to change the time or replace a broken job, delete the old job first.

1. If a job exists, go to **Setup > Scheduled Jobs** and click **Del** beside **AI Assist Maintenance**.
2. Run this in **Execute Anonymous Apex**:

    ```apex
    AIMaintenanceScheduler.scheduleDaily();
    ```

3. Check the new job in **Setup > Scheduled Jobs**.

To test one run without waiting until 02:00, run `new AIMaintenanceScheduler().execute(null);` in Execute Anonymous. It starts the same batches immediately.

!!! warning "To confirm"
    The job runs as the user who scheduled it. Schedule it as a stable integration or admin user, not a person who may leave. What happens to the job if that user is deactivated has not been verified here.

!!! note "The time is fixed in code"
    The 02:00 time is set in `AIMaintenanceScheduler` (`DAILY_AT_2AM`). To run at another time, change the code, or schedule `new AIMaintenanceScheduler()` yourself from **Setup > Apex Classes > Schedule Apex** with your own time. Give it a job name other than `AI Assist Maintenance`, and do not also call `scheduleDaily()`, or the housekeeping will run twice a day.

See [Logging and scheduled jobs](../architecture/logging-and-jobs.md) for how this fits with logging.
