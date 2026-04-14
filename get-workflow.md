# Retrieve workflow - HubSpot docs

> **Source:** [https://developers.hubspot.com/docs/api-reference/2026-09-beta/automation/workflows/get-workflow](https://developers.hubspot.com/docs/api-reference/2026-09-beta/automation/workflows/get-workflow)  
> **Scraped:** 2026-04-14 07:29 UTC

---

Retrieve workflow

cURL

``` curl --request GET \ \--url https://api.hubapi.com/automation/2026-09-beta/flows/{flowId} \ \--header 'Authorization: Bearer <token>' ```

200

default

``` { "type": "CONTACT_FLOW", "id": "<string>", "isEnabled": true, "flowType": "WORKFLOW", "revisionId": "<string>", "createdAt": "2023-11-07T05:31:56Z", "updatedAt": "2023-11-07T05:31:56Z", "nextAvailableActionId": "<string>", "actions": [ { "actionId": "<string>", "inputValue": { "actionId": "<string>", "dataKey": "<string>", "type": "FIELD_DATA" }, "staticBranches": [ { "branchValue": "<string>", "connection": { "edgeType": "GOTO", "nextActionId": "<string>" } } ], "type": "STATIC_BRANCH", "defaultBranch": { "edgeType": "GOTO", "nextActionId": "<string>" }, "defaultBranchName": "<string>" } ], "timeWindows": [ { "day": "FRIDAY", "endTime": { "hour": 123, "minute": 123 }, "startTime": { "hour": 123, "minute": 123 } } ], "blockedDates": [ { "dayOfMonth": 123, "month": "APRIL", "year": 123 } ], "customProperties": {}, "dataSources": [ { "associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 123, "name": "<string>", "objectTypeId": "<string>", "type": "ASSOCIATION", "sortBy": { "order": "ASC", "property": "<string>", "missing": "<string>" } } ], "crmObjectCreationStatus": "PENDING", "suppressionListIds": [ 123 ], "canEnrollFromSalesforce": true, "objectTypeId": "<string>", "name": "<string>", "description": "<string>", "uuid": "<string>", "startActionId": "<string>", "enrollmentCriteria": { "listFilterBranch": { "filterBranchOperator": "<string>", "filterBranchType": "OR", "filterBranches": [ { "filterBranchOperator": "<string>", "filterBranchType": "AND", "filterBranches": "<array>", "filters": [ "<unknown>" ] } ], "filters": [ { "filterType": "PROPERTY", "operation": "<unknown>", "property": "<string>" } ] }, "reEnrollmentTriggersFilterBranches": [ { "filterBranchOperator": "<string>", "filterBranchType": "AND", "filterBranches": "<array>", "filters": [ { "filterType": "PROPERTY", "operation": "<unknown>", "property": "<string>" } ] } ], "shouldReEnroll": true, "type": "LIST_BASED", "unEnrollObjectsNotMeetingCriteria": true }, "enrollmentSchedule": { "timeOfDay": { "hour": 123, "minute": 123 }, "type": "DAILY" }, "goalFilterBranch": { "filterBranchOperator": "<string>", "filterBranchType": "OR", "filterBranches": [ { "filterBranchOperator": "<string>", "filterBranchType": "AND", "filterBranches": "<array>", "filters": [ { "filterType": "PROPERTY", "operation": "<unknown>", "property": "<string>" } ] } ], "filters": [ { "filterType": "PROPERTY", "operation": { "includeObjectsWithNoValueSet": true, "operationType": "BOOL", "operator": "<string>", "value": true }, "property": "<string>" } ] }, "eventAnchor": { "contactProperty": "<string>", "type": "CONTACT_PROPERTY_ANCHOR" }, "unEnrollmentSetting": { "flowIds": [ "<string>" ], "type": "ALL" } } ```

GET

/

automation

/

2026-09-beta

/

flows

/

{flowId}

Try it

Retrieve workflow

cURL

``` curl --request GET \ \--url https://api.hubapi.com/automation/2026-09-beta/flows/{flowId} \ \--header 'Authorization: Bearer <token>' ```

200

default

``` { "type": "CONTACT_FLOW", "id": "<string>", "isEnabled": true, "flowType": "WORKFLOW", "revisionId": "<string>", "createdAt": "2023-11-07T05:31:56Z", "updatedAt": "2023-11-07T05:31:56Z", "nextAvailableActionId": "<string>", "actions": [ { "actionId": "<string>", "inputValue": { "actionId": "<string>", "dataKey": "<string>", "type": "FIELD_DATA" }, "staticBranches": [ { "branchValue": "<string>", "connection": { "edgeType": "GOTO", "nextActionId": "<string>" } } ], "type": "STATIC_BRANCH", "defaultBranch": { "edgeType": "GOTO", "nextActionId": "<string>" }, "defaultBranchName": "<string>" } ], "timeWindows": [ { "day": "FRIDAY", "endTime": { "hour": 123, "minute": 123 }, "startTime": { "hour": 123, "minute": 123 } } ], "blockedDates": [ { "dayOfMonth": 123, "month": "APRIL", "year": 123 } ], "customProperties": {}, "dataSources": [ { "associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 123, "name": "<string>", "objectTypeId": "<string>", "type": "ASSOCIATION", "sortBy": { "order": "ASC", "property": "<string>", "missing": "<string>" } } ], "crmObjectCreationStatus": "PENDING", "suppressionListIds": [ 123 ], "canEnrollFromSalesforce": true, "objectTypeId": "<string>", "name": "<string>", "description": "<string>", "uuid": "<string>", "startActionId": "<string>", "enrollmentCriteria": { "listFilterBranch": { "filterBranchOperator": "<string>", "filterBranchType": "OR", "filterBranches": [ { "filterBranchOperator": "<string>", "filterBranchType": "AND", "filterBranches": "<array>", "filters": [ "<unknown>" ] } ], "filters": [ { "filterType": "PROPERTY", "operation": "<unknown>", "property": "<string>" } ] }, "reEnrollmentTriggersFilterBranches": [ { "filterBranchOperator": "<string>", "filterBranchType": "AND", "filterBranches": "<array>", "filters": [ { "filterType": "PROPERTY", "operation": "<unknown>", "property": "<string>" } ] } ], "shouldReEnroll": true, "type": "LIST_BASED", "unEnrollObjectsNotMeetingCriteria": true }, "enrollmentSchedule": { "timeOfDay": { "hour": 123, "minute": 123 }, "type": "DAILY" }, "goalFilterBranch": { "filterBranchOperator": "<string>", "filterBranchType": "OR", "filterBranches": [ { "filterBranchOperator": "<string>", "filterBranchType": "AND", "filterBranches": "<array>", "filters": [ { "filterType": "PROPERTY", "operation": "<unknown>", "property": "<string>" } ] } ], "filters": [ { "filterType": "PROPERTY", "operation": { "includeObjectsWithNoValueSet": true, "operationType": "BOOL", "operator": "<string>", "value": true }, "property": "<string>" } ] }, "eventAnchor": { "contactProperty": "<string>", "type": "CONTACT_PROPERTY_ANCHOR" }, "unEnrollmentSetting": { "flowIds": [ "<string>" ], "type": "ALL" } } ```

Supported products

Required Scopes

#### Authorizations

oauth2private_appsoauth2private_apps

​

Authorization

string

header

required

The access token received from the authorization server in the OAuth 2.0 flow.

#### Path Parameters

​

flowId

string

required

The unique identifier of the automation flow to retrieve.

#### Response

200

application/json

successful operation

  * Option 1

  * Option 2




​

type

enum<string>

default:CONTACT_FLOW

required

Available options:

`CONTACT_FLOW`,

`PLATFORM_FLOW`

​

id

string

required

​

isEnabled

boolean

required

​

flowType

enum<string>

required

Available options:

`WORKFLOW`,

`ACTION_SET`,

`UNKNOWN`

​

revisionId

string

required

​

createdAt

string<date-time>

required

​

updatedAt

string<date-time>

required

​

nextAvailableActionId

string

required

​

actions

(STATIC_BRANCH · object | LIST_BRANCH · object | AB_TEST_BRANCH · object | CUSTOM_CODE · object | WEBHOOK · object | SINGLE_CONNECTION · object)[]

required

  * STATIC_BRANCH

  * LIST_BRANCH

  * AB_TEST_BRANCH

  * CUSTOM_CODE

  * WEBHOOK

  * SINGLE_CONNECTION




Show child attributes

​

timeWindows

object[]

required

Show child attributes

​

blockedDates

object[]

required

Show child attributes

​

customProperties

object

required

Show child attributes

​

dataSources

(ASSOCIATION · object | ASSOCIATION_TIMESTAMP · object | STATIC_PROPERTY_FILTER · object | ENROLLED_RECORD_PROPERTY_FILTER · object | DATASET_FIELD_PROPERTY_FILTER · object | ENROLLED_ARGUMENT_PROPERTY_FILTER · object)[]

required

  * ASSOCIATION

  * ASSOCIATION_TIMESTAMP

  * STATIC_PROPERTY_FILTER

  * ENROLLED_RECORD_PROPERTY_FILTER

  * DATASET_FIELD_PROPERTY_FILTER

  * ENROLLED_ARGUMENT_PROPERTY_FILTER




Show child attributes

​

crmObjectCreationStatus

enum<string>

required

Available options:

`PENDING`,

`COMPLETE`

​

suppressionListIds

integer<int32>[]

required

​

canEnrollFromSalesforce

boolean

required

​

objectTypeId

string

required

​

name

string

​

description

string

​

uuid

string

​

startActionId

string

​

enrollmentCriteria

LIST_BASED · object

  * LIST_BASED

  * EVENT_BASED

  * MANUAL

  * DATASET




Show child attributes

​

enrollmentSchedule

DAILY · object

  * DAILY

  * WEEKLY

  * MONTHLY_SPECIFIC_DAYS

  * MONTHLY_RELATIVE_DAYS

  * YEARLY

  * PROPERTY_BASED




Show child attributes

​

goalFilterBranch

OR · object

  * OR

  * AND

  * NOT_ALL

  * NOT_ANY

  * RESTRICTED

  * UNIFIED_EVENTS

  * PROPERTY_ASSOCIATION

  * ASSOCIATION




Show child attributes

​

eventAnchor

CONTACT_PROPERTY_ANCHOR · object

  * CONTACT_PROPERTY_ANCHOR

  * STATIC_DATE_ANCHOR




Show child attributes

​

unEnrollmentSetting

object

Show child attributes

Last modified on March 30, 2026

Was this page helpful?

YesNo

⌘I
