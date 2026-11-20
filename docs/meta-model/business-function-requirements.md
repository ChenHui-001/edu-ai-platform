# 业务功能需求

- Output Language: zh-CN
- Status: in-progress
- Function Count: 289


## FUNC-auth-auth-captcha
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-captcha business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0001
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: public or pre-auth.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-captcha


## FUNC-auth-auth-register
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-register business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0002
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: public or pre-auth.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-register


## FUNC-auth-auth-registrations
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-registrations business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0003
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-registrations


## FUNC-auth-auth-registrations-audit
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-registrations-audit business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0004
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-registrations-audit


## FUNC-auth-auth-login
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-login business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0005
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-login


## FUNC-auth-auth-refresh
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-refresh business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0006
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-refresh


## FUNC-auth-auth-profile
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-profile business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0007, API-op-0008
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-profile


## FUNC-auth-auth-password
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-password business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0009
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-password


## FUNC-auth-auth-logout
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-logout business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0010
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-logout


## FUNC-auth-auth-forgot-password
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-forgot-password business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0011
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: public or pre-auth.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-forgot-password


## FUNC-auth-auth-reset-password
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-login-register
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-auth-auth-reset-password business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0012
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: public or pre-auth.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-auth-auth-reset-password


## FUNC-flow-flow-todo
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-todo business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0013
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-todo


## FUNC-flow-flow-done
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-done business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0014
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-done


## FUNC-flow-flow-instances
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-instances business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0015
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-instances


## FUNC-flow-flow-instances-instance-id
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-instances-instance-id business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0016
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-instances-instance-id


## FUNC-flow-flow-tasks-task-id-claim
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-tasks-task-id-claim business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0017
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-tasks-task-id-claim


## FUNC-flow-flow-tasks-task-id-approve
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-tasks-task-id-approve business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0018
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-tasks-task-id-approve


## FUNC-flow-flow-tasks-task-id-reject
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-tasks-task-id-reject business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0019
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-tasks-task-id-reject


## FUNC-flow-flow-tasks-task-id-return
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-tasks-task-id-return business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0020
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-tasks-task-id-return


## FUNC-flow-flow-tasks-task-id-cancel
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-tasks-task-id-cancel business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0021
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-tasks-task-id-cancel


## FUNC-flow-flow-definitions-sync
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-definitions-sync business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0022
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-definitions-sync


## FUNC-flow-flow-overdue
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-overdue business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0023
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-overdue


## FUNC-flow-flow-tasks-task-id-transfer-candidates
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-tasks-task-id-transfer-candidates business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0024
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-tasks-task-id-transfer-candidates


## FUNC-flow-flow-tasks-task-id-transfer
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-tasks-task-id-transfer business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0025
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-tasks-task-id-transfer


## FUNC-flow-flow-tasks-task-id-urge
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-tasks-task-id-urge business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0026
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-tasks-task-id-urge


## FUNC-flow-flow-tasks-task-id-deadline
- Domain: DOM-flow-todo
- Capability: CAP-flow-approval
- Scenario: SCN-flow-review
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-flow-flow-tasks-task-id-deadline business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0027
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-flow-flow-tasks-task-id-deadline


## FUNC-learning-learning-remediation
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-remediation business action.
- Actors: student, teacher
- Trigger Entries: API-op-0028, API-op-0029
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-remediation


## FUNC-learning-learning-remediation-plan-id
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-remediation-plan-id business action.
- Actors: student, teacher
- Trigger Entries: API-op-0030
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-remediation-plan-id


## FUNC-learning-learning-remediation-plan-id-quizzes
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-remediation-plan-id-quizzes business action.
- Actors: student, teacher
- Trigger Entries: API-op-0031
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-remediation-plan-id-quizzes


## FUNC-learning-learning-remediation-plan-id-answers
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-remediation-plan-id-answers business action.
- Actors: student, teacher
- Trigger Entries: API-op-0032
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-remediation-plan-id-answers


## FUNC-teaching-graph-teaching-graph
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teaching-graph-teaching-graph business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0033
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-teachingassignment
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teaching-graph-teaching-graph


## FUNC-teaching-graph-teaching-graph-assign
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teaching-graph-teaching-graph-assign business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0034
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-teachingassignment
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teaching-graph-teaching-graph-assign


## FUNC-question-question-quality
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-quality business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0035
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-quality


## FUNC-question-question-quality-publish
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-quality-publish business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0036
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-quality-publish


## FUNC-question-question-quality-question-id-visual
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-quality-question-id-visual business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0037
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-quality-question-id-visual


## FUNC-learning-learning-tutor
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-tutor business action.
- Actors: student, teacher
- Trigger Entries: API-op-0038
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-tutor


## FUNC-learning-learning-tutor-feedback
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-tutor-feedback business action.
- Actors: student, teacher
- Trigger Entries: API-op-0039, API-op-0040
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-tutor-feedback


## FUNC-learning-learning-tutor-feedback-feedback-id
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-tutor-feedback-feedback-id business action.
- Actors: student, teacher
- Trigger Entries: API-op-0041
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-tutor-feedback-feedback-id


## FUNC-taxonomy-sync-system-taxonomy-sync
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-taxonomy-sync-system-taxonomy-sync business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0042
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-taxonomysyncrun
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-taxonomy-sync-system-taxonomy-sync


## FUNC-taxonomy-sync-system-taxonomy-sync-preview
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-taxonomy-sync-system-taxonomy-sync-preview business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0043
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-taxonomysyncrun
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-taxonomy-sync-system-taxonomy-sync-preview


## FUNC-taxonomy-sync-system-taxonomy-sync-apply
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-taxonomy-sync-system-taxonomy-sync-apply business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0044
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-taxonomysyncrun
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-taxonomy-sync-system-taxonomy-sync-apply


## FUNC-taxonomy-sync-system-taxonomy-sync-run-id-restore
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-taxonomy-sync-system-taxonomy-sync-run-id-restore business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0045
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-taxonomysyncrun
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-taxonomy-sync-system-taxonomy-sync-run-id-restore


## FUNC-admin-user-system-users
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-admin-user-system-users business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0046, API-op-0047
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-permission, OBJ-role, OBJ-rolepermission, OBJ-teachingassignment, OBJ-user, OBJ-userrole
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-admin-user-system-users


## FUNC-admin-user-system-users-user-id
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-admin-user-system-users-user-id business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0048, API-op-0049
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-permission, OBJ-role, OBJ-rolepermission, OBJ-teachingassignment, OBJ-user, OBJ-userrole
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-admin-user-system-users-user-id


## FUNC-admin-user-system-users-user-id-teachings
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-admin-user-system-users-user-id-teachings business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0050
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-permission, OBJ-role, OBJ-rolepermission, OBJ-teachingassignment, OBJ-user, OBJ-userrole
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-admin-user-system-users-user-id-teachings


## FUNC-other-system-password-reset
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-other-system-password-reset business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0051
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: none
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-other-system-password-reset


## FUNC-admin-user-system-users-user-id-unlock
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-admin-user-system-users-user-id-unlock business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0052
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-permission, OBJ-role, OBJ-rolepermission, OBJ-teachingassignment, OBJ-user, OBJ-userrole
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-admin-user-system-users-user-id-unlock


## FUNC-admin-role-system-roles
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-admin-role-system-roles business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0053, API-op-0054
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-role, OBJ-rolepermission
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-admin-role-system-roles


## FUNC-admin-role-system-roles-role-id
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-admin-role-system-roles-role-id business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0055, API-op-0056
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-role, OBJ-rolepermission
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-admin-role-system-roles-role-id


## FUNC-admin-role-system-roles-role-id-copy
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-admin-role-system-roles-role-id-copy business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0057
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-role, OBJ-rolepermission
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-admin-role-system-roles-role-id-copy


## FUNC-admin-permission-system-permissions
- Domain: DOM-identity-access
- Capability: CAP-identity
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-admin-permission-system-permissions business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0058
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-permission, OBJ-rolepermission
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-admin-permission-system-permissions


## FUNC-notification-system-notifications
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-notification-system-notifications business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0059
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-notification, OBJ-notifypref
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-notification-system-notifications


## FUNC-notification-system-notifications-notif-id-read
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-notification-system-notifications-notif-id-read business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0060
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-notification, OBJ-notifypref
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-notification-system-notifications-notif-id-read


## FUNC-notification-system-notifications-read-all
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-notification-system-notifications-read-all business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0061
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-notification, OBJ-notifypref
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-notification-system-notifications-read-all


## FUNC-other-system-notification-prefs
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-other-system-notification-prefs business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0062, API-op-0063
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: none
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-other-system-notification-prefs


## FUNC-system-config-system-config
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-system-config-system-config business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0064, API-op-0065
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-sysconfig
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-system-config-system-config


## FUNC-system-version-system-version
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-system-version-system-version business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0066
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: none
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-system-version-system-version


## FUNC-system-config-system-config-key
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-system-config-system-config-key business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0067
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-sysconfig
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-system-config-system-config-key


## FUNC-ai-config-system-ai-config
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-ai-config-system-ai-config business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0068, API-op-0069
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-sysconfig
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-config-system-ai-config


## FUNC-ai-config-system-ai-config-test
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-ai-config-system-ai-config-test business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0070
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-sysconfig
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-config-system-ai-config-test


## FUNC-teacher-grade-edu-grades
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-grade-edu-grades business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0071, API-op-0072
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-grade
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-grade-edu-grades


## FUNC-teacher-grade-edu-grades-grade-id
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-grade-edu-grades-grade-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0073, API-op-0074
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-grade
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-grade-edu-grades-grade-id


## FUNC-teacher-subject-edu-subjects
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-subject-edu-subjects business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0075, API-op-0076
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-grade, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-subject-edu-subjects


## FUNC-teacher-subject-edu-subjects-subject-id
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-subject-edu-subjects-subject-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0077, API-op-0078
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-grade, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-subject-edu-subjects-subject-id


## FUNC-teacher-subject-edu-subjects-subject-id-clone
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-subject-edu-subjects-subject-id-clone business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0079
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-grade, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-subject-edu-subjects-subject-id-clone


## FUNC-teacher-class-edu-classes-public
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-edu-classes-public business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0080
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-edu-classes-public


## FUNC-teacher-class-edu-classes
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-edu-classes business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0081, API-op-0082
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-edu-classes


## FUNC-teacher-class-edu-classes-stats
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-edu-classes-stats business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0083
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-edu-classes-stats


## FUNC-teacher-class-edu-classes-class-id
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-edu-classes-class-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0084, API-op-0085
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-edu-classes-class-id


## FUNC-teacher-class-edu-classes-batch
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-edu-classes-batch business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0086
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-edu-classes-batch


## FUNC-teacher-class-edu-classes-class-id-students
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-edu-classes-class-id-students business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0087, API-op-0088
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-edu-classes-class-id-students


## FUNC-teacher-class-edu-classes-class-id-students-export
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-edu-classes-class-id-students-export business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0089
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-edu-classes-class-id-students-export


## FUNC-teacher-class-edu-classes-class-id-students-batch-remove
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-edu-classes-class-id-students-batch-remove business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0090
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-edu-classes-class-id-students-batch-remove


## FUNC-teacher-class-edu-classes-class-id-students-student-id
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-edu-classes-class-id-students-student-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0091
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-edu-classes-class-id-students-student-id


## FUNC-other-edu-people-brief
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-other-edu-people-brief business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0092
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: none
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-other-edu-people-brief


## FUNC-teacher-class-request-edu-class-requests
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-request-edu-class-requests business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0093, API-op-0094
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-request-edu-class-requests


## FUNC-teacher-class-request-edu-class-requests-mine
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-request-edu-class-requests-mine business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0095
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-request-edu-class-requests-mine


## FUNC-teacher-class-request-edu-class-requests-req-id-review
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-request-edu-class-requests-req-id-review business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0096
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-request-edu-class-requests-req-id-review


## FUNC-teacher-class-request-edu-class-requests-req-id
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-class-request-edu-class-requests-req-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0097
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-classrequest, OBJ-notification
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-class-request-edu-class-requests-req-id


## FUNC-teacher-teaching-edu-teaching-matrix
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-teaching-edu-teaching-matrix business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0098
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-subject, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-teaching-edu-teaching-matrix


## FUNC-teacher-teaching-edu-teaching-assignments
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-teaching-edu-teaching-assignments business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0099, API-op-0100
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-subject, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-teaching-edu-teaching-assignments


## FUNC-teacher-teaching-edu-teaching-assignments-asg-id
- Domain: DOM-teaching-content
- Capability: CAP-teaching-basics
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-teacher-teaching-edu-teaching-assignments-asg-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0101
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-class, OBJ-subject, OBJ-teachingassignment, OBJ-user
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-teacher-teaching-edu-teaching-assignments-asg-id


## FUNC-knowledge-edu-knowledge-graph
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-graph business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0102
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-graph


## FUNC-knowledge-edu-knowledge-tree
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-tree business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0103
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-tree


## FUNC-knowledge-edu-knowledge
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0104, API-op-0105
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge


## FUNC-knowledge-edu-knowledge-list
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-list business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0106
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-list


## FUNC-knowledge-edu-knowledge-stats
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-stats business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0107
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-stats


## FUNC-knowledge-edu-knowledge-template
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-template business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0108
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-template


## FUNC-knowledge-edu-knowledge-export
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-export business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0109
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-export


## FUNC-knowledge-edu-knowledge-mastery-overview
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-mastery-overview business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0110
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-mastery-overview


## FUNC-knowledge-edu-knowledge-search
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-search business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0111
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-search


## FUNC-knowledge-edu-knowledge-rag-status
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-rag-status business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0112
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-rag-status


## FUNC-knowledge-edu-knowledge-kp-id
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-kp-id business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0113, API-op-0114, API-op-0115
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-kp-id


## FUNC-knowledge-edu-knowledge-kp-id-attachments
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-kp-id-attachments business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0116, API-op-0117
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-kp-id-attachments


## FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0118, API-op-0119
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-kp-id-attachments-att-id


## FUNC-knowledge-edu-knowledge-batch
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-batch business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0120
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-batch


## FUNC-knowledge-edu-knowledge-import
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-import business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0121
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-import


## FUNC-knowledge-edu-knowledge-reindex
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-reindex business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0122
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-reindex


## FUNC-knowledge-edu-knowledge-purge-generic
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-purge-generic business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0123
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-purge-generic


## FUNC-knowledge-edu-knowledge-diagnosis-targets
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-diagnosis-targets business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0124
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-diagnosis-targets


## FUNC-knowledge-edu-knowledge-diagnosis-sessions
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-diagnosis-sessions business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0125
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-diagnosis-sessions


## FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0126
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-diagnosis-sessions-session-id


## FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-next
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-next business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0127
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-diagnosis-sessions-session-id-next


## FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-answers
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-answers business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0128
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-diagnosis-sessions-session-id-answers


## FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-summary
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-summary business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0129
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-diagnosis-sessions-session-id-summary


## FUNC-knowledge-edu-knowledge-kp-id-prerequisites
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-kp-id-prerequisites business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0130, API-op-0131
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-kp-id-prerequisites


## FUNC-knowledge-edu-knowledge-kp-id-dependents
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-kp-id-dependents business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0132
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-kp-id-dependents


## FUNC-knowledge-edu-knowledge-kp-id-prerequisites-prerequisite-id
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-kp-id-prerequisites-prerequisite-id business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0133
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-kp-id-prerequisites-prerequisite-id


## FUNC-knowledge-edu-knowledge-ai-generate
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-ai-generate business action.
- Actors: teacher, student, sys_admin, system
- Trigger Entries: API-op-0134
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-ai-generate


## FUNC-knowledge-edu-knowledge-ai-enrich
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-knowledge-edu-knowledge-ai-enrich business action.
- Actors: teacher, student, sys_admin, system
- Trigger Entries: API-op-0135
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-knowledge-edu-knowledge-ai-enrich


## FUNC-question-question-questions
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0136, API-op-0137
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions


## FUNC-question-question-questions-stats
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-stats business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0138
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-stats


## FUNC-question-question-questions-batch-create
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-batch-create business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0139
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-batch-create


## FUNC-question-question-questions-batch
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-batch business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0140
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-batch


## FUNC-question-question-questions-template
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-template business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0141
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-template


## FUNC-question-question-questions-q-id
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-q-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0142, API-op-0143, API-op-0144
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-q-id


## FUNC-question-question-questions-q-id-status
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-q-id-status business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0145
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-q-id-status


## FUNC-question-question-questions-q-id-duplicates
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-q-id-duplicates business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0146
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-q-id-duplicates


## FUNC-question-question-questions-import
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-import business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0147
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-import


## FUNC-question-question-questions-export
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-export business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0148
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-export


## FUNC-question-question-papers
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0149, API-op-0150
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers


## FUNC-question-question-papers-stats
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-stats business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0151
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-stats


## FUNC-question-question-papers-batch
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-batch business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0152
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-batch


## FUNC-question-question-papers-paper-id
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0153, API-op-0154, API-op-0155
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id


## FUNC-question-question-papers-paper-id-archive
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-archive business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0156
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-archive


## FUNC-question-question-papers-paper-id-copy
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-copy business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0157
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-copy


## FUNC-question-question-papers-paper-id-share
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-share business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0158
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-share


## FUNC-question-question-papers-paper-id-export
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-export business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0159
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-export


## FUNC-question-question-questions-ai-variants
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-ai-variants business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0160
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-ai-variants


## FUNC-question-question-questions-ai-enrich
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-ai-enrich business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0161
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-ai-enrich


## FUNC-question-question-questions-ai-quality
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-questions-ai-quality business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0162
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-questions-ai-quality


## FUNC-question-question-papers-paper-id-ai-analyze
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-ai-analyze business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0163
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-ai-analyze


## FUNC-question-question-papers-paper-id-ai-recommend
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-ai-recommend business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0164
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-ai-recommend


## FUNC-question-question-standards
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-standards business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0165, API-op-0166
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-standards


## FUNC-question-question-standards-options
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-standards-options business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0167
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-standards-options


## FUNC-question-question-standards-std-id
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-standards-std-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0168, API-op-0169, API-op-0170
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-standards-std-id


## FUNC-question-question-standards-std-id-duplicate
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-standards-std-id-duplicate business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0171
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-standards-std-id-duplicate


## FUNC-question-question-standards-generate-missing
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-standards-generate-missing business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0172
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-standards-generate-missing


## FUNC-question-question-standards-seed
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-standards-seed business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0173
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-standards-seed


## FUNC-question-question-standards-std-id-reset
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-standards-std-id-reset business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0174
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-standards-std-id-reset


## FUNC-question-question-papers-compose-regenerate
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-compose-regenerate business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0175
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-compose-regenerate


## FUNC-question-question-papers-compose-preview
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-compose-preview business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0176
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-compose-preview


## FUNC-question-question-papers-compose-ai
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-compose-ai business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0177
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-compose-ai


## FUNC-question-question-papers-compose-save
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-compose-save business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0178
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-compose-save


## FUNC-question-question-papers-paper-id-preview
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-preview business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0179
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-preview


## FUNC-question-question-papers-paper-id-items
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-items business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0180
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-items


## FUNC-question-question-papers-paper-id-items-item-id-regenerate
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-items-item-id-regenerate business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0181
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-items-item-id-regenerate


## FUNC-question-question-papers-paper-id-items-item-id
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-items-item-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0182
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-items-item-id


## FUNC-question-question-papers-paper-id-sections-rename
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-sections-rename business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0183
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-sections-rename


## FUNC-question-question-papers-paper-id-restructure
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-restructure business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0184
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-restructure


## FUNC-question-question-papers-paper-id-versions
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-versions business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0185
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-versions


## FUNC-question-question-papers-paper-id-versions-version
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-versions-version business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0186
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-versions-version


## FUNC-question-question-papers-paper-id-versions-version-diff
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-versions-version-diff business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0187
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-versions-version-diff


## FUNC-question-question-papers-paper-id-versions-version-restore
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-versions-version-restore business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0188
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-versions-version-restore


## FUNC-question-question-papers-library-list
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-library-list business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0189
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-library-list


## FUNC-question-question-papers-paper-id-favorite
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-favorite business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0190
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-favorite


## FUNC-question-question-papers-paper-id-share-scope
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-share-scope business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0191
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-share-scope


## FUNC-question-question-papers-paper-id-share-info
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-share-info business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0192
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-share-info


## FUNC-question-question-papers-paper-id-review
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-review business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0193
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-review


## FUNC-question-question-papers-paper-id-export-docx
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-export-docx business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0194
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-export-docx


## FUNC-question-question-papers-paper-id-export-pdf
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-export-pdf business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0195
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-export-pdf


## FUNC-question-question-papers-paper-id-export-answer-sheet
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-export-answer-sheet business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0196
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-export-answer-sheet


## FUNC-question-question-papers-paper-id-export-html
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-export-html business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0197
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-export-html


## FUNC-question-question-papers-paper-id-export-jobs
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-paper-id-export-jobs business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0198
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-paper-id-export-jobs


## FUNC-question-question-papers-export-jobs-job-id
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-export-jobs-job-id business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0199
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-export-jobs-job-id


## FUNC-question-question-papers-export-jobs-job-id-file
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-export-jobs-job-id-file business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0200
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-export-jobs-job-id-file


## FUNC-question-question-papers-compose-ai-async
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-compose-ai-async business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0201
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-compose-ai-async


## FUNC-question-question-papers-compose-jobs-job-id
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-compose-jobs-job-id business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0202
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-compose-jobs-job-id


## FUNC-question-question-papers-compose-jobs-job-id-cancel
- Domain: DOM-question-paper
- Capability: CAP-question-bank
- Scenario: SCN-teacher-prepare
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-question-question-papers-compose-jobs-job-id-cancel business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0203
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-question-question-papers-compose-jobs-job-id-cancel


## FUNC-task-task-tasks
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-tasks business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0204, API-op-0205
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-tasks


## FUNC-task-task-tasks-stats
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-tasks-stats business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0206
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-tasks-stats


## FUNC-task-task-tasks-batch
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-tasks-batch business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0207
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-tasks-batch


## FUNC-task-task-tasks-task-id
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-tasks-task-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0208, API-op-0209, API-op-0210
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-tasks-task-id


## FUNC-task-task-tasks-task-id-submissions
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-tasks-task-id-submissions business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0211
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-tasks-task-id-submissions


## FUNC-task-task-my-tasks
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-my-tasks business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0212
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-my-tasks


## FUNC-task-task-tasks-task-id-paper
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-tasks-task-id-paper business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0213
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-tasks-task-id-paper


## FUNC-task-task-tasks-task-id-submit
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-tasks-task-id-submit business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0214
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-tasks-task-id-submit


## FUNC-task-task-tasks-task-id-heartbeat
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-tasks-task-id-heartbeat business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0215
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-tasks-task-id-heartbeat


## FUNC-task-task-submissions-submission-id
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-submissions-submission-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0216
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-submissions-submission-id


## FUNC-task-task-my-scores
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-my-scores business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0217
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-my-scores


## FUNC-task-task-tasks-task-id-pending-students
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-tasks-task-id-pending-students business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0218
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-tasks-task-id-pending-students


## FUNC-task-task-tasks-task-id-urge
- Domain: DOM-task-assessment
- Capability: CAP-task-management
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-task-task-tasks-task-id-urge business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0219
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-task-task-tasks-task-id-urge


## FUNC-grading-grading-pending
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-pending business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0220
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-pending


## FUNC-grading-grading-submissions
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-submissions business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0221
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-submissions


## FUNC-grading-grading-stats
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-stats business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0222
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-stats


## FUNC-grading-grading-submissions-submission-id
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-submissions-submission-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0223
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-submissions-submission-id


## FUNC-grading-grading-submissions-submission-id-grade
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-submissions-submission-id-grade business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0224
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-submissions-submission-id-grade


## FUNC-grading-grading-submissions-submission-id-reject
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-submissions-submission-id-reject business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0225
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-submissions-submission-id-reject


## FUNC-grading-grading-submissions-submission-id-publish
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-submissions-submission-id-publish business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0226
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-submissions-submission-id-publish


## FUNC-grading-grading-batch-grade
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-batch-grade business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0227
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-batch-grade


## FUNC-grading-grading-batch-publish
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-batch-publish business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0228
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-batch-publish


## FUNC-grading-grading-unpublish
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-unpublish business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0229
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-unpublish


## FUNC-grading-grading-tasks-task-id-report
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-tasks-task-id-report business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0230
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-tasks-task-id-report


## FUNC-grading-grading-tasks-task-id-ai-comment
- Domain: DOM-task-assessment
- Capability: CAP-grading
- Scenario: SCN-teacher-teach
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-grading-grading-tasks-task-id-ai-comment business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0231
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-grading-grading-tasks-task-id-ai-comment


## FUNC-learning-learning-notes
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-notes business action.
- Actors: student, teacher
- Trigger Entries: API-op-0232, API-op-0233
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-notes


## FUNC-learning-learning-notes-shared
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-notes-shared business action.
- Actors: student, teacher
- Trigger Entries: API-op-0234
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-notes-shared


## FUNC-learning-learning-notes-note-id
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-notes-note-id business action.
- Actors: student, teacher
- Trigger Entries: API-op-0235, API-op-0236, API-op-0237
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-notes-note-id


## FUNC-learning-learning-notes-note-id-share
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-notes-note-id-share business action.
- Actors: student, teacher
- Trigger Entries: API-op-0238
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-notes-note-id-share


## FUNC-learning-learning-notes-note-id-organize
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-notes-note-id-organize business action.
- Actors: student, teacher
- Trigger Entries: API-op-0239
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-notes-note-id-organize


## FUNC-learning-learning-notes-note-id-export
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-notes-note-id-export business action.
- Actors: student, teacher
- Trigger Entries: API-op-0240
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-notes-note-id-export


## FUNC-learning-learning-wrong-questions
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-wrong-questions business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0241
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-wrong-questions


## FUNC-learning-learning-wrong-questions-wid
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-wrong-questions-wid business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0242
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-wrong-questions-wid


## FUNC-learning-learning-wrong-questions-wid-analyze
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-wrong-questions-wid-analyze business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0243
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-wrong-questions-wid-analyze


## FUNC-learning-learning-wrong-questions-wid-redo
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-wrong-questions-wid-redo business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0244
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-wrong-questions-wid-redo


## FUNC-learning-learning-wrong-questions-export
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-wrong-questions-export business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0245
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-wrong-questions-export


## FUNC-learning-learning-review-plans
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-review-plans business action.
- Actors: student, teacher
- Trigger Entries: API-op-0246
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-review-plans


## FUNC-learning-learning-review-plans-plan-id-complete
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-review-plans-plan-id-complete business action.
- Actors: student, teacher
- Trigger Entries: API-op-0247
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-review-plans-plan-id-complete


## FUNC-learning-learning-review-mastery
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-review-mastery business action.
- Actors: student, teacher
- Trigger Entries: API-op-0248
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-review-mastery


## FUNC-learning-learning-review-plan
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-review-plan business action.
- Actors: student, teacher
- Trigger Entries: API-op-0249
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-review-plan


## FUNC-learning-learning-practice
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-practice business action.
- Actors: student, teacher
- Trigger Entries: API-op-0250
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-practice


## FUNC-learning-learning-practice-history
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-practice-history business action.
- Actors: student, teacher
- Trigger Entries: API-op-0251
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-practice-history


## FUNC-learning-learning-practice-task-id
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-practice-task-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0252
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-practice-task-id


## FUNC-learning-learning-favorites
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-favorites business action.
- Actors: student, teacher
- Trigger Entries: API-op-0253, API-op-0254
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-favorites


## FUNC-learning-learning-favorites-fav-id
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-favorites-fav-id business action.
- Actors: student, teacher
- Trigger Entries: API-op-0255
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-favorites-fav-id


## FUNC-learning-learning-favorites-by-question-question-id
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-favorites-by-question-question-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0256
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-favorites-by-question-question-id


## FUNC-learning-learning-favorites-check-batch
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-favorites-check-batch business action.
- Actors: student, teacher
- Trigger Entries: API-op-0257
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-favorites-check-batch


## FUNC-learning-learning-favorites-check-question-id
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-favorites-check-question-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0258
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-favorites-check-question-id


## FUNC-learning-learning-favorites-practice
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-favorites-practice business action.
- Actors: student, teacher
- Trigger Entries: API-op-0259
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-favorites-practice


## FUNC-learning-learning-wrong-questions-wid-variant
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-wrong-questions-wid-variant business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0260
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-wrong-questions-wid-variant


## FUNC-learning-learning-custom-paper
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-custom-paper business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0261
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-custom-paper


## FUNC-learning-learning-goals
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-goals business action.
- Actors: student, teacher
- Trigger Entries: API-op-0262, API-op-0263
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-goals


## FUNC-learning-learning-goals-goal-id
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-goals-goal-id business action.
- Actors: student, teacher
- Trigger Entries: API-op-0264, API-op-0265
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-goals-goal-id


## FUNC-learning-learning-goals-goal-id-checkin
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-goals-goal-id-checkin business action.
- Actors: student, teacher
- Trigger Entries: API-op-0266
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-goals-goal-id-checkin


## FUNC-learning-learning-path-recommend
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-path-recommend business action.
- Actors: student, teacher
- Trigger Entries: API-op-0267
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-path-recommend


## FUNC-learning-learning-flashcards
- Domain: DOM-learning-support
- Capability: CAP-learning-tools
- Scenario: SCN-student-learn
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-learning-learning-flashcards business action.
- Actors: student, teacher
- Trigger Entries: API-op-0268
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-learning-learning-flashcards


## FUNC-ai-agent-agent-list
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-list business action.
- Actors: teacher, student, sys_admin, system
- Trigger Entries: API-op-0269
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-list


## FUNC-ai-agent-agent-status
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-status business action.
- Actors: teacher, student, sys_admin, system
- Trigger Entries: API-op-0270
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-status


## FUNC-ai-agent-agent-chat
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-chat business action.
- Actors: teacher, student, sys_admin, system
- Trigger Entries: API-op-0271
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-chat


## FUNC-ai-agent-agent-chat-stream
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-chat-stream business action.
- Actors: teacher, student, sys_admin, system
- Trigger Entries: API-op-0272
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-chat-stream


## FUNC-ai-agent-agent-question-generator
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-question-generator business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0273
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-question-generator


## FUNC-ai-agent-agent-paper-composer
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-paper-composer business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0274
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-paper-composer


## FUNC-ai-agent-agent-grading
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-grading business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0275
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-grading


## FUNC-ai-agent-agent-study-planner
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-study-planner business action.
- Actors: teacher, student, sys_admin, system
- Trigger Entries: API-op-0276
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-study-planner


## FUNC-ai-agent-agent-tutor
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-tutor business action.
- Actors: teacher, student, sys_admin, system
- Trigger Entries: API-op-0277
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-tutor


## FUNC-ai-agent-agent-note-organizer
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-note-organizer business action.
- Actors: teacher, student, sys_admin, system
- Trigger Entries: API-op-0278
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-note-organizer


## FUNC-ai-agent-agent-jobs
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-jobs business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0279, API-op-0280
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-jobs


## FUNC-ai-agent-agent-jobs-job-id
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-jobs-job-id business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0281
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-jobs-job-id


## FUNC-ai-agent-agent-logs
- Domain: DOM-ai-services
- Capability: CAP-ai-assistance
- Scenario: SCN-ai-assist
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-ai-agent-agent-logs business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0282
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ai-agent-agent-logs


## FUNC-report-report-student-overview
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-student-overview business action.
- Actors: student, teacher
- Trigger Entries: API-op-0283
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-student-overview


## FUNC-report-report-student-score-trend
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-student-score-trend business action.
- Actors: student, teacher
- Trigger Entries: API-op-0284
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-student-score-trend


## FUNC-report-report-student-knowledge-radar
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-student-knowledge-radar business action.
- Actors: student, teacher
- Trigger Entries: API-op-0285
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-student-knowledge-radar


## FUNC-report-report-student-wrong-analysis
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-student-wrong-analysis business action.
- Actors: student, teacher
- Trigger Entries: API-op-0286
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-student-wrong-analysis


## FUNC-report-report-student-learning-suggestion
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-student-learning-suggestion business action.
- Actors: student, teacher
- Trigger Entries: API-op-0287
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: student scope for own data; teacher may view class scope.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-student-learning-suggestion


## FUNC-report-report-teacher-class-overview
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-teacher-class-overview business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0288
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-teacher-class-overview


## FUNC-report-report-teacher-student-comparison
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-teacher-student-comparison business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0289
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-teacher-student-comparison


## FUNC-report-report-teacher-student-detail
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-teacher-student-detail business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0290
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-teacher-student-detail


## FUNC-report-report-teacher-knowledge-effect
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-teacher-knowledge-effect business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0291
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-teacher-knowledge-effect


## FUNC-report-report-teacher-class-weak-points
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-teacher-class-weak-points business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0292
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-teacher-class-weak-points


## FUNC-report-report-admin-overview
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-admin-overview business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0293
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-admin-overview


## FUNC-report-report-admin-grade-comparison
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-admin-grade-comparison business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0294
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-admin-grade-comparison


## FUNC-report-report-admin-subject-comparison
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-admin-subject-comparison business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0295
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-admin-subject-comparison


## FUNC-report-report-admin-system-runtime
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-admin-system-runtime business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0296
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-admin-system-runtime


## FUNC-report-report-export-excel
- Domain: DOM-reporting
- Capability: CAP-reporting
- Scenario: SCN-teacher-teach
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-report-report-export-excel business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0297
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-report-report-export-excel


## FUNC-log-logs-login
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-log-logs-login business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0298
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-errorlog, OBJ-loginlog, OBJ-operationlog
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-log-logs-login


## FUNC-log-logs-operation
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-log-logs-operation business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0299
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-errorlog, OBJ-loginlog, OBJ-operationlog
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-log-logs-operation


## FUNC-log-logs-error
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-log-logs-error business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0300
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-errorlog, OBJ-loginlog, OBJ-operationlog
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-log-logs-error


## FUNC-log-logs-export
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-log-logs-export business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0301
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-errorlog, OBJ-loginlog, OBJ-operationlog
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-log-logs-export


## FUNC-job-jobs-handlers
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-job-jobs-handlers business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0302
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-jobexecutionlog, OBJ-scheduledjob
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-job-jobs-handlers


## FUNC-job-jobs
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-job-jobs business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0303, API-op-0304
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-jobexecutionlog, OBJ-scheduledjob
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-job-jobs


## FUNC-job-jobs-job-id
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-job-jobs-job-id business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0305, API-op-0306
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-jobexecutionlog, OBJ-scheduledjob
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-job-jobs-job-id


## FUNC-job-jobs-job-id-toggle
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-job-jobs-job-id-toggle business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0307
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-jobexecutionlog, OBJ-scheduledjob
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-job-jobs-job-id-toggle


## FUNC-job-jobs-job-id-run
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-job-jobs-job-id-run business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0308
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-jobexecutionlog, OBJ-scheduledjob
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-job-jobs-job-id-run


## FUNC-job-jobs-status
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-job-jobs-status business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0309
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-jobexecutionlog, OBJ-scheduledjob
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-job-jobs-status


## FUNC-job-jobs-job-id-executions
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-job-jobs-job-id-executions business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0310
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-jobexecutionlog, OBJ-scheduledjob
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-job-jobs-job-id-executions


## FUNC-attachment-attachments-public-upload
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-attachment-attachments-public-upload business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0311
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: public or pre-auth.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-attachment-attachments-public-upload


## FUNC-attachment-attachments-upload
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-attachment-attachments-upload business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0312
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-attachment-attachments-upload


## FUNC-attachment-attachments-batch
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-attachment-attachments-batch business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0313
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-attachment-attachments-batch


## FUNC-attachment-attachments
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-attachment-attachments business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0314
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-attachment-attachments


## FUNC-attachment-attachments-att-id-preview
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-attachment-attachments-att-id-preview business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0315
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-attachment-attachments-att-id-preview


## FUNC-attachment-attachments-att-id-download
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-attachment-attachments-att-id-download business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0316
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-attachment-attachments-att-id-download


## FUNC-attachment-attachments-att-id-bind
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-attachment-attachments-att-id-bind business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0317
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-attachment-attachments-att-id-bind


## FUNC-attachment-attachments-att-id
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-attachment-attachments-att-id business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0318
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-attachment
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: Authenticated user with endpoint permission.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-attachment-attachments-att-id


## FUNC-lesson-lesson-plans
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-plans business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0319, API-op-0320
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-plans


## FUNC-lesson-lesson-plans-stats
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-plans-stats business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0321
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-plans-stats


## FUNC-lesson-lesson-plans-plan-id
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-plans-plan-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0322, API-op-0323, API-op-0324
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-plans-plan-id


## FUNC-lesson-lesson-plans-plan-id-copy
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-plans-plan-id-copy business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0325
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-plans-plan-id-copy


## FUNC-lesson-lesson-plans-plan-id-share
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-plans-plan-id-share business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0326
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-plans-plan-id-share


## FUNC-lesson-lesson-plans-batch
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-plans-batch business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0327
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-plans-batch


## FUNC-lesson-lesson-plans-plan-id-attachments
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-plans-plan-id-attachments business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0328, API-op-0329
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-plans-plan-id-attachments


## FUNC-lesson-lesson-plans-plan-id-attachments-att-id
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: business
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-plans-plan-id-attachments-att-id business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0330
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-plans-plan-id-attachments-att-id


## FUNC-lesson-lesson-ai-generate
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-ai-generate business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0331
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-ai-generate


## FUNC-lesson-lesson-ai-jobs-job-id
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-ai-jobs-job-id business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0332
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-ai-jobs-job-id


## FUNC-lesson-lesson-ai-jobs-job-id-cancel
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-ai-jobs-job-id-cancel business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0333
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-ai-jobs-job-id-cancel


## FUNC-lesson-lesson-ai-jobs
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-ai-jobs business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0334
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-ai-jobs


## FUNC-lesson-lesson-ai-jobs-job-id-save
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-ai-jobs-job-id-save business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0335
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-ai-jobs-job-id-save


## FUNC-lesson-lesson-ai-jobs-job-id-export
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-ai-jobs-job-id-export business action.
- Actors: sys_admin, system
- Trigger Entries: API-op-0336
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-ai-jobs-job-id-export


## FUNC-lesson-lesson-ai-options
- Domain: DOM-teaching-content
- Capability: CAP-knowledge-management
- Scenario: SCN-teacher-prepare
- Function Type: platform
- Interaction: interactive
- Business Goal: Complete FUNC-lesson-lesson-ai-options business action.
- Actors: teacher, sys_admin
- Trigger Entries: API-op-0337
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: teacher scope; sys_admin may override.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-lesson-lesson-ai-options


## FUNC-health-health
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-health-health business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0338
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: none
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: public.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-health-health


## FUNC-ready-ready
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: interactive
- Business Goal: Complete FUNC-ready-ready business action.
- Actors: system, relevant role user
- Trigger Entries: API-op-0339
- Menu Rationale: User-facing menu entry.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: none
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: public.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-ready-ready


## FUNC-jobs-clean-expired-exams
- Domain: DOM-platform-ops
- Capability: CAP-platform-administration
- Scenario: SCN-admin-manage
- Function Type: operations
- Interaction: non-interactive
- Business Goal: Complete FUNC-jobs-clean-expired-exams business action.
- Actors: sys_admin, system
- Trigger Entries: JOB-clean-expired-exams
- Menu Rationale: System automatic trigger, no menu required.
- Preconditions: Valid session or public endpoint, required business data exists.
- Inputs: Request path, query, body, or scheduled payload as applicable.
- Main Steps: Enter page or trigger API, validate input, execute business rule, persist result, return response.
- Business Rules: Follow domain default rules and API validation.
- Core Objects: none
- External Objects: none
- Outputs And Results: API response and persisted business state.
- State Changes: Update relevant business state per API semantics.
- Failure Outcomes: Validation error, permission error, or failed business state.
- Manual Intervention: Retry via UI/API or admin correction.
- Upstream Functions: none
- Downstream Functions: none
- Permission And Data Scope: sys_admin or grade_admin as configured.
- Non-Functional Clauses: security, consistency, observability.
- Requirement Evidence: openapi.json, interface-index.md, function-chain-index.md.
- Implementation Chain: ./function-chain-index.md#func-jobs-clean-expired-exams
