# Code patterns

AI Assist code follows one house pattern for Apex classes and another for Lightning web components. This page is the reference for both.

The aim is that a junior developer can open any file and follow it without help. The pattern prefers many small named steps over short, clever code.

## Apex classes

The reference example is `AIAnthropicMessageResponseHandler`. Test classes follow a separate pattern: see [Testing](testing.md).

### Header

Every class starts with a comment block: the class name, a one-line description, the workflow as numbered `Step 1:`, `Step 2:` lines, and a version table. The version table always has exactly one row (`1.0  Chandler Stuart  Initial development`) and is never added to.

### Layout rules

| Rule | Detail |
|---|---|
| Indent | 4 spaces. No tabs. |
| Sharing | Every class is `without sharing`. Access is enforced in code by naming the mode on each statement (see below). |
| Declaration | Modifiers and the declaration on one line: `public without sharing class X implements Y {` |
| Blank lines | After the class brace, and after the opening brace of each method, loop and multi-line `if`. Also after `try {` and before `} catch`. |
| One statement, one line | Never split a call, signature, condition, string or assignment over several lines, however long. The one exception is a Map or List literal with several entries, one entry per line. |
| Guards | A single-statement guard stays on one line: `if (x == null) return null;` |
| Catch variable | Always `ex`. |
| Order | Inner classes, constants and static variables, `@TestVisible` flags, public methods, private helpers. |

!!! note "Prettier is switched off for Apex"
    `.prettierignore` lists `**/*.cls`. `prettier-plugin-apex` re-wraps calls and changes indentation, so never run it on Apex.

### Comments

A comment sits directly above each method. Steps inside a method are numbered `// [1] What this does`, one plain sentence each. The numbers run in order through the method and restart at `[1]` in each helper.

### Method names

Start with a verb that says what the caller gets.

| Verb | Meaning | Example |
|---|---|---|
| `get` | Read something that exists and return it | `getOwnedConversation` |
| `build` | Assemble a new object from other values | `buildConversationSummary` |
| `create` | Make and save a new record | `createConversation` |
| `find` | Search, and return null when nothing matches | `findActiveConversation` |
| `is` / `has` | Answer true or false | `isCommandText` |
| `load`, `save`, `send`, `run`, `record` | The action the method performs | `sendMessage` |

Never name a method `toXxx` or `assertXxx`. A method that checks something and refuses with an exception is named for what it returns (`getOwnedConversation`), not for the check.

### Example

This is the shape of a real class, trimmed:

```apex
/*
Class Name: AIMaintenanceScheduler

Description: The package's one scheduled job, which runs the daily housekeeping.

Step 1: Fail messages left waiting at the cap on messages in flight
Step 2: Start the retention batch
Step 3: Start the idle conversation batch, only while the application is on

Version      Author                   Description
1.0          Chandler Stuart          Initial development
*/

public without sharing class AIMaintenanceScheduler implements Schedulable {

    public class AIMaintenanceSchedulerException extends Exception {}

    public static final String JOB_NAME = 'AI Assist Maintenance';

    @TestVisible
    private static Boolean isTestCustomExceptionThrown = false;

    // Schedules the daily run unless a job of this name already exists.
    public static Id scheduleDaily() {

        // [1] Throw on purpose when a test asks for it
        if (isTestCustomExceptionThrown) throw new AIMaintenanceSchedulerException('Test exception for AIMaintenanceScheduler.scheduleDaily');

        // [2] Do nothing when the job is already scheduled
        if ([SELECT COUNT() FROM CronTrigger WHERE CronJobDetail.Name = :JOB_NAME WITH SYSTEM_MODE] > 0) return null;

        // [3] Schedule the daily run and return the job's Id
        return System.schedule(JOB_NAME, DAILY_AT_2AM, new AIMaintenanceScheduler());
    }
}
```

### Conventions you will meet

- **Explicit access mode.** Queries use `WITH SYSTEM_MODE` or `WITH USER_MODE`, and DML uses `AccessLevel.SYSTEM_MODE` or `AccessLevel.USER_MODE`. Code that acts for the user (reading their conversation) uses user mode. Code that writes system-managed fields (the processing lock, usage totals) uses system mode.
- **Errors are logged, not lost.** A method catches its exception, logs it with `AIPlatformLogManager.logException(ex, 'ClassName', 'methodName')` and carries on or returns a safe value. A refusal shown to the user is an exception that carries a Custom Label, so the text is translatable.
- **Test hooks.** A `@TestVisible private static Boolean isTestCustomExceptionThrown` flag lets a test force the catch path. Most classes also declare their own `Exception` inner class.
- **Constants.** Strings and numbers that mean something live in `AIAssistApplicationConstants`, for example `PROCESSING_STATUS_QUEUED` or `FAILURE_REASON_TIMEOUT`.
- **Tab classes come in threes.** A `Controller` (the `@AuraEnabled` entry points), an `EditorService` (the logic) and a `DataStructure` (the inner classes sent to the component).

## Lightning web components

The reference example is `aiChatWorkingIndicator`. Components with more logic also have a Helper file, for example `aiChatMessage`.

### Files in a component folder

| File | Holds |
|---|---|
| `<name>.js` | The controller: what the component does. No hard-coded values, no long logic. |
| `<name>Settings.js` | Pure settings: constants, label text, CSS class names, status values. No functions, no imports. |
| `<name>Helper.js` | Plain exported functions with no component state. Only created when the controller has logic worth moving out. |
| `<name>.html` | The template. Each element on one line, with a plain-English comment above each section. |
| `<name>.css` | Only what SLDS cannot do. Colours come from the `--aia-*` tokens defined on the root component `aiAssistChat`. |

Each component owns its Settings and Helper. There is no shared utils component and no shared stylesheet: a little repeated code is the price of that. A child component's styles never go in its parent's CSS.

### Rules

- 2-space indent, formatted by hand like Apex. Do not run Prettier on the component's `.js` files: they are listed in `.prettierignore`. Each pattern-following component's `.html` has a large `printWidth` override in `.prettierrc`.
- An import is one line. A statement is never split over several lines.
- Order in the controller: imports, header comment, `@api` properties, tracked state, lifecycle methods, getters, `handle...` event handlers, private methods.
- Every step gets its own named variable (`stepViews`, `isDone`), not a chained expression. Booleans start with `is`, `has`, `show` or `can`. Event handlers start with `handle`.
- A literal that means something (a status, a class name, a number) goes in the Settings file with an UPPER_SNAKE_CASE name.
- Helper functions use the same verbs as Apex (`get`, `build`, `find`, `is`, `has`, `format`) and number their steps the same way.
- Never change behaviour, `@api` names or event names while reformatting.

### Example

```javascript
export default class AiChatWorkingIndicator extends LightningElement {

  // Values passed in by the parent component
  @api mode = DEFAULT_MODE; // 'steps' or 'typing'

  // True when the step card should show, false when the typing indicator should.
  get isSteps() {

    // [1] Compare the mode the parent passed in with the steps mode
    const currentMode = this.mode;
    const isStepsMode = currentMode === MODE_STEPS;

    return isStepsMode;
  }
}
```

!!! note "No Jest tests"
    The repository has no LWC Jest tests, by the owner's choice. [Codebase health](../codebase-health.md) reports this as "LWC components with Jest tests".
