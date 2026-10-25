# AI PII Registry

The **AI PII Registry** tab controls which fields are masked before data reaches the AI provider. Each object in the registry has its fields classified as personal data (PII) or not, and PII values are swapped for stand-in values before anything is sent. This page is the admin view; for how masking works inside, see [PII protection](../architecture/pii-protection.md).

!!! note "Who can use this tab"
    The AI Assist Admin and AI Assist Super User permission sets include the tab's Apex. The tab is visible by default only for Super User. See [permission sets](../reference/permission-sets.md).

## Registered objects

Objects are listed on the left, each with its field count, PII field count and sync status. The header shows how many objects the registry holds against the limit, for example "5 of 10 objects (MaxPIIRegistryObjects)". That limit is a setting on the [Settings tab](settings.md), under **Registries per sync run**. Click **+ Add object** to add one.

In the **Add an object to the registry** dialog:

1. Type at least two letters of the object name and pick it. Objects already in the registry are not offered.
2. Set **Max fields to query**. The dialog shows how many fields the object has and warns if the limit is too low.
3. Click **Add and sync**. Fields are classified in the background.

The **Active** toggle on an object turns masking for it on or off. Switched off, its fields go to the provider unmasked.

## Sync status

| Status | Meaning |
|---|---|
| **Not synced yet** | Never synced. Use **Sync now**. |
| **Queued** or **Syncing** | Fields are being classified. They appear when the sync finishes. |
| **Synced** | Fields are classified. |
| **Failed** | The sync did not complete. The tab shows the time and says the platform log explains why. Use **Sync again** or **View log**. |

!!! warning
    Until a sync succeeds, unclassified fields are treated as not PII. If an agent reads that object, the values could reach the provider unmasked.

### Max Fields To Query

**Max fields to query** is how many fields of the object the sync reads, up to 500. If the object has more fields, the first ones are classified and the sync is marked **Failed**, because the rest were never checked. The tab then offers **Raise to n and sync**. If the object is larger than the most the registry can read, the remaining fields cannot be checked here.

Failed objects are picked up again on the next sync run.

## Fields

Open an object's **Fields** tab. Filter with **PII only**, **All** or **Overridden**, or search by name.

| Column | Meaning |
|---|---|
| **Field** and **Type** | The field and its Salesforce data type. |
| **PII** | Whether the field is masked. |
| **PII type** | The kind of personal data, for example a name or email. |
| **Compliance group** | The compliance group of the type, where one is known. |
| **Masking** | The masking rule for the type. |
| **Source** | **Auto** (classified by the rules) or **Overridden**. |

Fields are classified automatically from rules held in custom metadata (`AIPiiFieldType__mdt`). To override one, switch **PII** on or off, or change the **PII type**. Overrides survive the next sync. **Reset** hands a field back to the automatic rules.

!!! warning "To confirm"
    **Masking** shows "Redacted" unless masking rules exist in custom metadata. The package source in this repo contains no `AIPiiFieldType__mdt`, `AIPiiDataMaskingRule__mdt` or `AIPiiComplianceGroup__mdt` records. Confirm which records are deployed in your org, and note the masking engine only builds stand-ins from a list of substitute values: any other strategy falls back to a generic `REDACTED-` value. See the [PII reference](../reference/objects/AIPiiFieldType__mdt.md).

## Test masking

The **Test masking** tab runs masking on a real record without saving or sending anything.

1. Search for a record of the object.
2. Click **Run masking**.
3. Compare **Real value (you only)** with **Sent to the AI provider**, and see the **Rule** used.

If the record has no values in the PII fields, there is nothing to mask. When a reply comes back it is unmasked before the user sees it, using the pairs saved for that conversation.

## Unprotected objects

A banner at the top of the tab lists objects that agents read but that are not in the registry: "n objects are read by agents but not in the registry. Their fields go to the provider unmasked." It comes from checking the target object of every active data source against the registry. Each row shows the data sources that read it and has **Add to registry**. The banner stays until fixed.

For incidents see the runbook [PII sync failed](../runbooks/pii-sync-failed.md).
