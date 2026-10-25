# Testing

Every Apex class that needs a test has a `<ClassName>Test` class that follows one pattern. This page shows the pattern, the shared test data, the gotchas that cause most failures, and how to run the tests.

The reference example is `AIAgentTriggerHandlerTest`.

## The test class pattern

A test class has:

1. A header comment with `Applicable Classes` and the one-row version table.
2. A list of scenarios directly under the class brace, one line each: `// testScenarioN: <what is done> -> <what is expected>.`
3. Optionally, a `@TestSetup` method that switches the application on.
4. Methods named `testScenario1`, `testScenario2` and so on, matching the list.

Every test method has the same shape:

```apex
@IsTest private class AIAgentTriggerHandlerTest {

    // testScenario3: Updating an AIAgent__c without changing its retention settings does not start the batch.

    @TestSetup static void setup() {

        AIAssistSettings__c settings = AIAssistSettings__c.getOrgDefaults();
        settings.IsEnabled__c = true;
        upsert settings;
    }

    @IsTest static void testScenario3() {

        User superUser = AIAssistTestDataFactory.createSuperUser();

        System.runAs(superUser) {
            // [1] Create an agent with retention settings
            AIAgent__c agent = AIAssistTestDataFactory.createAIAgents(1, AIAssistTestDataFactory.createAIModelConfigurations(1, true)[0].Id, false)[0];
            insert agent;

            // [2] Change only the agent name and update the agent
            Test.startTest();
                agent.Name = 'A completely new name';
                update agent;
            Test.stopTest();

            // [3] Count the retention batches that ran
            Integer batchCount = [SELECT COUNT() FROM AsyncApexJob WHERE ApexClass.Name = 'AIConversationRetentionRecalcBatch'];

            // [4] Check that no batch ran
            Assert.areEqual(0, batchCount, 'No batch should run when the retention settings did not change.');
        }
    }
}
```

### Rules in brief

| Rule | Detail |
|---|---|
| Run as a real user | Start with `User superUser = AIAssistTestDataFactory.createSuperUser();` and put the body in `System.runAs(superUser)`. A test that also needs another user nests a second `System.runAs`. |
| Arrange, act, assert | Build data, put only the action between `Test.startTest()` and `Test.stopTest()`, query results after `Test.stopTest()`, assert last. |
| Numbered steps | `// [1] ...` in every method, restarting at `[1]` each time. |
| Asserts | `Assert.areEqual`, `isNull`, `isNotNull`, each with a message, and each on one line. No `try`/`catch` or `Assert.fail` wrappers: the code under test catches its own exceptions. |
| No private helpers | A test class has no private methods and no helper classes. Repeat the lines in each test, or add a method to `AIAssistTestDataFactory`. The only exception is a small inner class that must exist to implement an interface the platform calls, such as `HttpCalloutMock`. |
| Prefer the real trigger | Insert or update records and let the trigger run. Call a handler directly only for null or empty input. |
| Exception scenario | Set the class's `@TestVisible isTestCustomExceptionThrown` flag, check the business effect did not happen, and check exactly one `AIPlatformLog__c` row with the right `ClassName__c` and `MethodName__c`. |
| Layout | Same one-statement-per-line rule as the [Apex pattern](code-patterns.md). |

## Shared test data

`AIAssistTestDataFactory` builds the records tests need, each with the minimum valid values. Most methods take a count and a `shouldDoInsert` flag: `createAIAgents(1, modelConfigurationId, true)`.

| Method (examples) | Use it for |
|---|---|
| `createSuperUser()` | The user every test runs as. Holds `AIAssistSuperUser` and an active default usage policy that covers everyone. |
| `createUsers(n, insert)` and `assignPermissionSet(users, 'AIAssistUser')` | An end user who holds only the User permission set. |
| `createAIModelConfigurations`, `createAIAgents`, `createAIPromptTemplates` | Agent setup. |
| `createAIConversations`, `createAIConversationMessages` | Chat data. |
| `createAIUsagePolicyForUser`, `createDefaultUsagePolicy`, `deactivateUsagePolicies` | Usage limits and access. |
| `createAIPIIRegistries`, `createAIPIIFieldMetadata`, `createAIPIIMappings` | PII protection. |
| `createAIDataSources`, `createAIWorkflowActions` | Tools. |

For provider calls, `AIAssistTestProviderMock.install(kind)` registers an `HttpCalloutMock`. Call it before `Test.startTest()`. The kinds are `KIND_ANSWER` (replies `Fake reply`), `KIND_ECHO`, `KIND_FAIL` (a non-retryable error), `KIND_RETRY` (the first call fails with a retryable status) and `KIND_AGENT` (the Anthropic Agent API). `AIAssistTestProviderMock.callCount` says how many callouts were made. Two stubs, `AIDataSourceTestStub` and `AIWorkflowActionTestStub`, stand in for a customer's Apex class.

## Gotchas

### Permission sets and system mode

- Custom fields are invisible to a user until a permission set grants them. A test that sets a field the running user cannot see fails with "fields being inaccessible", or SOQL fails with "No such column". This is why tests run as the Super User.
- `AIAssistSuperUser` must cover every object and field in the repo. When you add an object or field, add it there, or tests for it will fail.
- `WITH SYSTEM_MODE` and `AccessLevel.SYSTEM_MODE` skip object and field permissions but do not skip sharing. Code that must see other people's private records needs to be `without sharing`, which every class here is.
- Code that touches system-managed fields (the processing lock, usage totals) names `SYSTEM_MODE` explicitly. If a test fails with field access errors in such code, check the statement names its mode.
- `User` is a setup object. The factory inserts users and permission set assignments as an administrator in a separate `System.runAs` (`getSetupUser()`), so the test can write other records afterwards without a mixed-DML error. Do the same if you insert setup records yourself.

### Async code

- `Test.stopTest()` runs queued jobs, batches and future work to completion. Read state you want to compare before `stopTest`, and query the result after it.
- The platform event `AIPlatformLogEvent__e` becomes an `AIPlatformLog__c` row when the test ends, so check logs after `Test.stopTest()`.
- `AsyncInfo.hasMaxStackDepth()` throws outside a queueable or finalizer. The production code wraps it in `try`/`catch`. Do the same if you call it.
- A queueable's finalizer runs after the job. A message processing test therefore sees the lock released and the next message started only after `Test.stopTest()`.
- Callouts need the mock registered before the job runs: call `AIAssistTestProviderMock.install(...)` before `Test.startTest()`.
- Usage is counted per day in the org's time zone. `AIUsageService.todayForTest` (`@TestVisible`) lets a test move to the next day without waiting.

## Running the tests

Run every local test in an org that holds the source:

```bash
sf apex run test --test-level RunLocalTests --code-coverage --result-format human --wait 45
```

Run one class:

```bash
sf apex run test --class-names AIAgentTriggerHandlerTest --result-format human --wait 10
```

CI runs `RunLocalTests` in a fresh scratch org, then `check-coverage.js` from the AIAssist-CICD repo, which fails the run below 75% coverage. See [CI and releases](ci.md). In a scratch org, `assign-permsets.js` (also in AIAssist-CICD) assigns every permission set to the default user first.

## LWC tests

There are no LWC Jest tests in this repository, by the owner's choice. The [Codebase health](../codebase-health.md) page reports this on every build as "LWC components with Jest tests" and lists "Components without Jest tests". That row is a status report, not a to-do for a pull request.
