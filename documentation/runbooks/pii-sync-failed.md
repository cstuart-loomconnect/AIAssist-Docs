# A PII registry sync failed

An object on the **AI PII Registry** tab shows **Failed** instead of **Synced**. The sync reads the object's fields, classifies which hold personal data, and saves one `AIPIIFieldMetadata__c` row per field. Until a sync succeeds, the registry cannot protect that object properly.

!!! warning "Treat a failed sync as a privacy risk"
    On the tab, an object that has not synced successfully shows: "Until a sync succeeds, unclassified fields are treated as not PII. If an agent reads [the object], those values could reach the provider unmasked." Fix a failed sync promptly, or stop agents reading that object until it is fixed. See [PII protection](../architecture/pii-protection.md).

## How a sync runs

| Part | What it does |
|---|---|
| `AIPiiRegistrySyncDispatcher` | Called by the daily maintenance job when AI Assist is on. Finds active registries that are never synced, **Failed**, or past their **Cache Reset Date**, and not already **Queued**. Marks them Queued and hands them all to one worker job. |
| `AIPiiRegistrySyncWorker` | A queueable. For each registry it reads the object's fields from `FieldDefinition` (no callout), classifies each one, and upserts the field rows. It marks the registry **Synced**, or **Failed**. A failure on one registry does not stop the others. |
| The **Sync now** button | Queues a sync of one object straight away, optionally with a higher field limit. |

The dispatcher takes at most 20 registries per run, and fewer if **Registries per sync run** (`MaxPIIRegistryObjects__c`) is lower. A field you overrode by hand keeps your choice when the sync runs again.

The registry's **Sync Status** is one of **Not Synced**, **Queued**, **Synced** or **Failed**. The picklist is also defined with an **In Progress** value that the code checks for but never sets.

## 1. Find out why it failed

Open the registry on the **AI PII Registry** tab, or the **AI PII Registry** record.

| What the tab says | Cause |
|---|---|
| "Field describe returned more than N fields; only the first N were classified (MaxFieldsToQuery)." | The object has more fields than **Max Fields To Query** (default 200, allowed 1 to 500). The rest were never checked for PII, so the registry is marked Failed on purpose. |
| "The platform log says why." | Something else went wrong: a field row could not be saved, or an unexpected exception. |

For the second case, open **AI Platform Logs** and filter on **Class Name** `AIPiiRegistrySyncWorker`. The entry gives the object and the error.

## 2. Fix it

**Too many fields.** On the registry, use the button the tab offers: **Raise to N and sync**. It doubles the limit (up to 500) and queues a sync. Or set **Max Fields To Query** yourself and press **Sync now**.

!!! warning "To confirm"
    The registry cannot read more than 500 fields: the tab says "This is the most the registry can read (500). The rest of the fields can't be checked here." An object with more than 500 fields cannot be fully classified. The repository does not say what to do for such an object (for example standard objects with very many custom fields). Decide, and record it here.

**Other failure.** Fix the cause named in the log, then press **Sync now** (or **Sync again**). Common causes are a field-level issue on a custom object, or a limit hit because many registries were synced in one run: lower **Registries per sync run** in [Settings](../admin-guide/settings.md).

## 3. Retry behaviour

- A registry that is **Failed** is picked up again by the dispatcher on every maintenance run, so it is retried daily without anyone pressing a button, as long as it is **Active** and the maintenance job is running. See [The maintenance job is not running](maintenance-job.md).
- A retry with the same limit fails the same way for the too-many-fields case, so raise the limit rather than waiting.
- **Sync now** is refused with "This object is already queued or syncing. Wait for it to finish." when the status is Queued.

!!! warning "To confirm"
    A registry left at **Queued** (for example if the queued job was lost) is skipped by the dispatcher, which ignores Queued and In Progress registries, and **Sync now** refuses it. No code was found that resets a stuck Queued status. The status field is editable only by `AIAssistSuperUser`. Confirm the recovery step: a Super User resetting **Sync Status** to **Failed** should make the dispatcher pick it up on the next run.

## 4. Check it worked

1. The registry shows **Synced** and a recent **Last Synced** time.
2. Open the **Fields** tab on the registry: PII fields are marked, and the count matches what you expect.
3. Use the **Test masking** tab to see what would be masked for a sample value.

See [AI PII Registry](../admin-guide/pii-registry.md) for the tab, and [PII registry classes](../reference/apex/pii-protection.md) for the code.
