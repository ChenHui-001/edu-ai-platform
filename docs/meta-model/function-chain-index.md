# 功能实现链

- Output Language: zh-CN
- Status: in-progress
- Function Count: 289


## FUNC-auth-auth-captcha

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-captcha
- 业务目标: 完成 FUNC-auth-auth-captcha 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0001
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: public or pre-auth.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-captcha
- 证据摘要: OpenAPI + source code path mapping


## FUNC-auth-auth-register

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-register
- 业务目标: 完成 FUNC-auth-auth-register 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0002
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-captcha R/C/U, TBL-sys-login-log R/C/U, TBL-sys-rate-limit R/C/U, TBL-sys-registration R/C/U, TBL-sys-reset-code R/C/U, TBL-sys-revoked-token R/C/U, TBL-sys-user R/C/U, TBL-sys-user-token-revocation R/C/U
- 依赖查询表: TBL-sys-captcha R, TBL-sys-login-log R, TBL-sys-rate-limit R, TBL-sys-registration R, TBL-sys-reset-code R, TBL-sys-revoked-token R, TBL-sys-user R, TBL-sys-user-token-revocation R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: public or pre-auth.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-register
- 证据摘要: OpenAPI + source code path mapping


## FUNC-auth-auth-registrations

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-registrations
- 业务目标: 完成 FUNC-auth-auth-registrations 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0003
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-captcha R/C/U, TBL-sys-login-log R/C/U, TBL-sys-rate-limit R/C/U, TBL-sys-registration R/C/U, TBL-sys-reset-code R/C/U, TBL-sys-revoked-token R/C/U, TBL-sys-user R/C/U, TBL-sys-user-token-revocation R/C/U
- 依赖查询表: TBL-sys-captcha R, TBL-sys-login-log R, TBL-sys-rate-limit R, TBL-sys-registration R, TBL-sys-reset-code R, TBL-sys-revoked-token R, TBL-sys-user R, TBL-sys-user-token-revocation R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-registrations
- 证据摘要: OpenAPI + source code path mapping


## FUNC-auth-auth-registrations-audit

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-registrations-audit
- 业务目标: 完成 FUNC-auth-auth-registrations-audit 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0004
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-captcha R/C/U, TBL-sys-login-log R/C/U, TBL-sys-rate-limit R/C/U, TBL-sys-registration R/C/U, TBL-sys-reset-code R/C/U, TBL-sys-revoked-token R/C/U, TBL-sys-user R/C/U, TBL-sys-user-token-revocation R/C/U
- 依赖查询表: TBL-sys-captcha R, TBL-sys-login-log R, TBL-sys-rate-limit R, TBL-sys-registration R, TBL-sys-reset-code R, TBL-sys-revoked-token R, TBL-sys-user R, TBL-sys-user-token-revocation R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-registrations-audit
- 证据摘要: OpenAPI + source code path mapping


## FUNC-auth-auth-login

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-login
- 业务目标: 完成 FUNC-auth-auth-login 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0005
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-captcha R/C/U, TBL-sys-login-log R/C/U, TBL-sys-rate-limit R/C/U, TBL-sys-registration R/C/U, TBL-sys-reset-code R/C/U, TBL-sys-revoked-token R/C/U, TBL-sys-user R/C/U, TBL-sys-user-token-revocation R/C/U
- 依赖查询表: TBL-sys-captcha R, TBL-sys-login-log R, TBL-sys-rate-limit R, TBL-sys-registration R, TBL-sys-reset-code R, TBL-sys-revoked-token R, TBL-sys-user R, TBL-sys-user-token-revocation R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-login
- 证据摘要: OpenAPI + source code path mapping


## FUNC-auth-auth-refresh

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-refresh
- 业务目标: 完成 FUNC-auth-auth-refresh 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0006
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-captcha R/C/U, TBL-sys-login-log R/C/U, TBL-sys-rate-limit R/C/U, TBL-sys-registration R/C/U, TBL-sys-reset-code R/C/U, TBL-sys-revoked-token R/C/U, TBL-sys-user R/C/U, TBL-sys-user-token-revocation R/C/U
- 依赖查询表: TBL-sys-captcha R, TBL-sys-login-log R, TBL-sys-rate-limit R, TBL-sys-registration R, TBL-sys-reset-code R, TBL-sys-revoked-token R, TBL-sys-user R, TBL-sys-user-token-revocation R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-refresh
- 证据摘要: OpenAPI + source code path mapping


## FUNC-auth-auth-profile

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-profile
- 业务目标: 完成 FUNC-auth-auth-profile 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0007, API-op-0008
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-captcha R/C/U, TBL-sys-login-log R/C/U, TBL-sys-rate-limit R/C/U, TBL-sys-registration R/C/U, TBL-sys-reset-code R/C/U, TBL-sys-revoked-token R/C/U, TBL-sys-user R/C/U, TBL-sys-user-token-revocation R/C/U
- 依赖查询表: TBL-sys-captcha R, TBL-sys-login-log R, TBL-sys-rate-limit R, TBL-sys-registration R, TBL-sys-reset-code R, TBL-sys-revoked-token R, TBL-sys-user R, TBL-sys-user-token-revocation R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-profile
- 证据摘要: OpenAPI + source code path mapping


## FUNC-auth-auth-password

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-password
- 业务目标: 完成 FUNC-auth-auth-password 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0009
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-captcha R/C/U, TBL-sys-login-log R/C/U, TBL-sys-rate-limit R/C/U, TBL-sys-registration R/C/U, TBL-sys-reset-code R/C/U, TBL-sys-revoked-token R/C/U, TBL-sys-user R/C/U, TBL-sys-user-token-revocation R/C/U
- 依赖查询表: TBL-sys-captcha R, TBL-sys-login-log R, TBL-sys-rate-limit R, TBL-sys-registration R, TBL-sys-reset-code R, TBL-sys-revoked-token R, TBL-sys-user R, TBL-sys-user-token-revocation R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-password
- 证据摘要: OpenAPI + source code path mapping


## FUNC-auth-auth-logout

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-logout
- 业务目标: 完成 FUNC-auth-auth-logout 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0010
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-captcha R/C/U, TBL-sys-login-log R/C/U, TBL-sys-rate-limit R/C/U, TBL-sys-registration R/C/U, TBL-sys-reset-code R/C/U, TBL-sys-revoked-token R/C/U, TBL-sys-user R/C/U, TBL-sys-user-token-revocation R/C/U
- 依赖查询表: TBL-sys-captcha R, TBL-sys-login-log R, TBL-sys-rate-limit R, TBL-sys-registration R, TBL-sys-reset-code R, TBL-sys-revoked-token R, TBL-sys-user R, TBL-sys-user-token-revocation R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-logout
- 证据摘要: OpenAPI + source code path mapping


## FUNC-auth-auth-forgot-password

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-forgot-password
- 业务目标: 完成 FUNC-auth-auth-forgot-password 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0011
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-captcha R/C/U, TBL-sys-login-log R/C/U, TBL-sys-rate-limit R/C/U, TBL-sys-registration R/C/U, TBL-sys-reset-code R/C/U, TBL-sys-revoked-token R/C/U, TBL-sys-user R/C/U, TBL-sys-user-token-revocation R/C/U
- 依赖查询表: TBL-sys-captcha R, TBL-sys-login-log R, TBL-sys-rate-limit R, TBL-sys-registration R, TBL-sys-reset-code R, TBL-sys-revoked-token R, TBL-sys-user R, TBL-sys-user-token-revocation R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: public or pre-auth.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-forgot-password
- 证据摘要: OpenAPI + source code path mapping


## FUNC-auth-auth-reset-password

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-auth-auth-reset-password
- 业务目标: 完成 FUNC-auth-auth-reset-password 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-login-register / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0012
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-captcha, OBJ-loginlog, OBJ-ratelimit, OBJ-registration, OBJ-resetcode, OBJ-revokedtoken, OBJ-user, OBJ-usertokenrevocation
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-captcha R/C/U, TBL-sys-login-log R/C/U, TBL-sys-rate-limit R/C/U, TBL-sys-registration R/C/U, TBL-sys-reset-code R/C/U, TBL-sys-revoked-token R/C/U, TBL-sys-user R/C/U, TBL-sys-user-token-revocation R/C/U
- 依赖查询表: TBL-sys-captcha R, TBL-sys-login-log R, TBL-sys-rate-limit R, TBL-sys-registration R, TBL-sys-reset-code R, TBL-sys-revoked-token R, TBL-sys-user R, TBL-sys-user-token-revocation R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: public or pre-auth.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-auth-auth-reset-password
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-todo

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-todo
- 业务目标: 完成 FUNC-flow-flow-todo 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0013
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-todo
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-done

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-done
- 业务目标: 完成 FUNC-flow-flow-done 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0014
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-done
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-instances

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-instances
- 业务目标: 完成 FUNC-flow-flow-instances 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0015
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-instances
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-instances-instance-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-instances-instance-id
- 业务目标: 完成 FUNC-flow-flow-instances-instance-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0016
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-instances-instance-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-tasks-task-id-claim

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-tasks-task-id-claim
- 业务目标: 完成 FUNC-flow-flow-tasks-task-id-claim 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0017
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-tasks-task-id-claim
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-tasks-task-id-approve

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-tasks-task-id-approve
- 业务目标: 完成 FUNC-flow-flow-tasks-task-id-approve 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0018
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-tasks-task-id-approve
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-tasks-task-id-reject

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-tasks-task-id-reject
- 业务目标: 完成 FUNC-flow-flow-tasks-task-id-reject 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0019
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-tasks-task-id-reject
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-tasks-task-id-return

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-tasks-task-id-return
- 业务目标: 完成 FUNC-flow-flow-tasks-task-id-return 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0020
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-tasks-task-id-return
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-tasks-task-id-cancel

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-tasks-task-id-cancel
- 业务目标: 完成 FUNC-flow-flow-tasks-task-id-cancel 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0021
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-tasks-task-id-cancel
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-definitions-sync

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-definitions-sync
- 业务目标: 完成 FUNC-flow-flow-definitions-sync 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0022
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-definitions-sync
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-overdue

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-overdue
- 业务目标: 完成 FUNC-flow-flow-overdue 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0023
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-overdue
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-tasks-task-id-transfer-candidates

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-tasks-task-id-transfer-candidates
- 业务目标: 完成 FUNC-flow-flow-tasks-task-id-transfer-candidates 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0024
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-tasks-task-id-transfer-candidates
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-tasks-task-id-transfer

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-tasks-task-id-transfer
- 业务目标: 完成 FUNC-flow-flow-tasks-task-id-transfer 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0025
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-tasks-task-id-transfer
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-tasks-task-id-urge

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-tasks-task-id-urge
- 业务目标: 完成 FUNC-flow-flow-tasks-task-id-urge 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0026
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-tasks-task-id-urge
- 证据摘要: OpenAPI + source code path mapping


## FUNC-flow-flow-tasks-task-id-deadline

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-flow-flow-tasks-task-id-deadline
- 业务目标: 完成 FUNC-flow-flow-tasks-task-id-deadline 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-flow-todo / SCN-flow-review / CAP-flow-approval
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0027
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-flowdefinition, OBJ-flowhistory, OBJ-flowinstance, OBJ-flowtask, OBJ-flowtransfer, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification, COMMON-idempotency

### Physical Data Operations
- 核心 CUD 表: TBL-edu-flow-definition R/C/U/D, TBL-edu-flow-history R/C/U/D, TBL-edu-flow-instance R/C/U/D, TBL-edu-flow-task R/C/U/D, TBL-edu-flow-transfer R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-flow-definition R, TBL-edu-flow-history R, TBL-edu-flow-instance R, TBL-edu-flow-task R, TBL-edu-flow-transfer R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-flow-flow-tasks-task-id-deadline
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-remediation

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-remediation
- 业务目标: 完成 FUNC-learning-learning-remediation 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0028, API-op-0029
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-remediation
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-remediation-plan-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-remediation-plan-id
- 业务目标: 完成 FUNC-learning-learning-remediation-plan-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0030
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-remediation-plan-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-remediation-plan-id-quizzes

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-remediation-plan-id-quizzes
- 业务目标: 完成 FUNC-learning-learning-remediation-plan-id-quizzes 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0031
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-remediation-plan-id-quizzes
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-remediation-plan-id-answers

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-remediation-plan-id-answers
- 业务目标: 完成 FUNC-learning-learning-remediation-plan-id-answers 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0032
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-remediation-plan-id-answers
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teaching-graph-teaching-graph

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teaching-graph-teaching-graph
- 业务目标: 完成 FUNC-teaching-graph-teaching-graph 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0033
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-teachingassignment
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-teaching-assignment R/C/U/D
- 依赖查询表: TBL-edu-class R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-teaching-assignment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teaching-graph-teaching-graph
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teaching-graph-teaching-graph-assign

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teaching-graph-teaching-graph-assign
- 业务目标: 完成 FUNC-teaching-graph-teaching-graph-assign 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0034
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-teachingassignment
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-teaching-assignment R/C/U/D
- 依赖查询表: TBL-edu-class R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-teaching-assignment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teaching-graph-teaching-graph-assign
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-quality

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-quality
- 业务目标: 完成 FUNC-question-question-quality 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0035
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-quality
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-quality-publish

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-quality-publish
- 业务目标: 完成 FUNC-question-question-quality-publish 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0036
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-quality-publish
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-quality-question-id-visual

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-quality-question-id-visual
- 业务目标: 完成 FUNC-question-question-quality-question-id-visual 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0037
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-quality-question-id-visual
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-tutor

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-tutor
- 业务目标: 完成 FUNC-learning-learning-tutor 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0038
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-tutor
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-tutor-feedback

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-tutor-feedback
- 业务目标: 完成 FUNC-learning-learning-tutor-feedback 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0039, API-op-0040
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-tutor-feedback
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-tutor-feedback-feedback-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-tutor-feedback-feedback-id
- 业务目标: 完成 FUNC-learning-learning-tutor-feedback-feedback-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0041
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-tutor-feedback-feedback-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-taxonomy-sync-system-taxonomy-sync

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-taxonomy-sync-system-taxonomy-sync
- 业务目标: 完成 FUNC-taxonomy-sync-system-taxonomy-sync 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0042
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-taxonomysyncrun
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-taxonomy-sync-run R/C/U/D
- 依赖查询表: TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-taxonomy-sync-run R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-taxonomy-sync-system-taxonomy-sync
- 证据摘要: OpenAPI + source code path mapping


## FUNC-taxonomy-sync-system-taxonomy-sync-preview

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-taxonomy-sync-system-taxonomy-sync-preview
- 业务目标: 完成 FUNC-taxonomy-sync-system-taxonomy-sync-preview 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0043
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-taxonomysyncrun
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-taxonomy-sync-run R/C/U/D
- 依赖查询表: TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-taxonomy-sync-run R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-taxonomy-sync-system-taxonomy-sync-preview
- 证据摘要: OpenAPI + source code path mapping


## FUNC-taxonomy-sync-system-taxonomy-sync-apply

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-taxonomy-sync-system-taxonomy-sync-apply
- 业务目标: 完成 FUNC-taxonomy-sync-system-taxonomy-sync-apply 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0044
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-taxonomysyncrun
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-taxonomy-sync-run R/C/U/D
- 依赖查询表: TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-taxonomy-sync-run R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-taxonomy-sync-system-taxonomy-sync-apply
- 证据摘要: OpenAPI + source code path mapping


## FUNC-taxonomy-sync-system-taxonomy-sync-run-id-restore

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-taxonomy-sync-system-taxonomy-sync-run-id-restore
- 业务目标: 完成 FUNC-taxonomy-sync-system-taxonomy-sync-run-id-restore 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0045
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-taxonomysyncrun
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-taxonomy-sync-run R/C/U/D
- 依赖查询表: TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-taxonomy-sync-run R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-taxonomy-sync-system-taxonomy-sync-run-id-restore
- 证据摘要: OpenAPI + source code path mapping


## FUNC-admin-user-system-users

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-admin-user-system-users
- 业务目标: 完成 FUNC-admin-user-system-users 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-admin-manage / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0046, API-op-0047
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-permission, OBJ-role, OBJ-rolepermission, OBJ-teachingassignment, OBJ-user, OBJ-userrole
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-teaching-assignment R/C/U/D, TBL-sys-permission R/C/U, TBL-sys-role R/C/U, TBL-sys-role-permission R/C/U, TBL-sys-user R/C/U, TBL-sys-user-role R/C/U
- 依赖查询表: TBL-edu-teaching-assignment R, TBL-sys-permission R, TBL-sys-role R, TBL-sys-role-permission R, TBL-sys-user R, TBL-sys-user-role R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-admin-user-system-users
- 证据摘要: OpenAPI + source code path mapping


## FUNC-admin-user-system-users-user-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-admin-user-system-users-user-id
- 业务目标: 完成 FUNC-admin-user-system-users-user-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-admin-manage / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0048, API-op-0049
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-permission, OBJ-role, OBJ-rolepermission, OBJ-teachingassignment, OBJ-user, OBJ-userrole
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-teaching-assignment R/C/U/D, TBL-sys-permission R/C/U, TBL-sys-role R/C/U, TBL-sys-role-permission R/C/U, TBL-sys-user R/C/U, TBL-sys-user-role R/C/U
- 依赖查询表: TBL-edu-teaching-assignment R, TBL-sys-permission R, TBL-sys-role R, TBL-sys-role-permission R, TBL-sys-user R, TBL-sys-user-role R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-admin-user-system-users-user-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-admin-user-system-users-user-id-teachings

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-admin-user-system-users-user-id-teachings
- 业务目标: 完成 FUNC-admin-user-system-users-user-id-teachings 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-admin-manage / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0050
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-permission, OBJ-role, OBJ-rolepermission, OBJ-teachingassignment, OBJ-user, OBJ-userrole
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-teaching-assignment R/C/U/D, TBL-sys-permission R/C/U, TBL-sys-role R/C/U, TBL-sys-role-permission R/C/U, TBL-sys-user R/C/U, TBL-sys-user-role R/C/U
- 依赖查询表: TBL-edu-teaching-assignment R, TBL-sys-permission R, TBL-sys-role R, TBL-sys-role-permission R, TBL-sys-user R, TBL-sys-user-role R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-admin-user-system-users-user-id-teachings
- 证据摘要: OpenAPI + source code path mapping


## FUNC-other-system-password-reset

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-other-system-password-reset
- 业务目标: 完成 FUNC-other-system-password-reset 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0051
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: none
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: 待细化
- 依赖查询表: 待细化
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-other-system-password-reset
- 证据摘要: OpenAPI + source code path mapping


## FUNC-admin-user-system-users-user-id-unlock

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-admin-user-system-users-user-id-unlock
- 业务目标: 完成 FUNC-admin-user-system-users-user-id-unlock 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-admin-manage / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0052
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-permission, OBJ-role, OBJ-rolepermission, OBJ-teachingassignment, OBJ-user, OBJ-userrole
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-teaching-assignment R/C/U/D, TBL-sys-permission R/C/U, TBL-sys-role R/C/U, TBL-sys-role-permission R/C/U, TBL-sys-user R/C/U, TBL-sys-user-role R/C/U
- 依赖查询表: TBL-edu-teaching-assignment R, TBL-sys-permission R, TBL-sys-role R, TBL-sys-role-permission R, TBL-sys-user R, TBL-sys-user-role R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-admin-user-system-users-user-id-unlock
- 证据摘要: OpenAPI + source code path mapping


## FUNC-admin-role-system-roles

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-admin-role-system-roles
- 业务目标: 完成 FUNC-admin-role-system-roles 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-admin-manage / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0053, API-op-0054
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-role, OBJ-rolepermission
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-sys-role R/C/U, TBL-sys-role-permission R/C/U
- 依赖查询表: TBL-sys-role R, TBL-sys-role-permission R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-admin-role-system-roles
- 证据摘要: OpenAPI + source code path mapping


## FUNC-admin-role-system-roles-role-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-admin-role-system-roles-role-id
- 业务目标: 完成 FUNC-admin-role-system-roles-role-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-admin-manage / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0055, API-op-0056
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-role, OBJ-rolepermission
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-sys-role R/C/U, TBL-sys-role-permission R/C/U
- 依赖查询表: TBL-sys-role R, TBL-sys-role-permission R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-admin-role-system-roles-role-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-admin-role-system-roles-role-id-copy

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-admin-role-system-roles-role-id-copy
- 业务目标: 完成 FUNC-admin-role-system-roles-role-id-copy 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-admin-manage / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0057
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-role, OBJ-rolepermission
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-sys-role R/C/U, TBL-sys-role-permission R/C/U
- 依赖查询表: TBL-sys-role R, TBL-sys-role-permission R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-admin-role-system-roles-role-id-copy
- 证据摘要: OpenAPI + source code path mapping


## FUNC-admin-permission-system-permissions

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-admin-permission-system-permissions
- 业务目标: 完成 FUNC-admin-permission-system-permissions 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-identity-access / SCN-admin-manage / CAP-identity
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0058
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-permission, OBJ-rolepermission
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-sys-permission R/C/U, TBL-sys-role-permission R/C/U
- 依赖查询表: TBL-sys-permission R, TBL-sys-role-permission R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-admin-permission-system-permissions
- 证据摘要: OpenAPI + source code path mapping


## FUNC-notification-system-notifications

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-notification-system-notifications
- 业务目标: 完成 FUNC-notification-system-notifications 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0059
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-notification, OBJ-notifypref
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification

### Physical Data Operations
- 核心 CUD 表: TBL-sys-notification R/C/U, TBL-sys-notify-pref R/C/U
- 依赖查询表: TBL-sys-notification R, TBL-sys-notify-pref R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-notification-system-notifications
- 证据摘要: OpenAPI + source code path mapping


## FUNC-notification-system-notifications-notif-id-read

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-notification-system-notifications-notif-id-read
- 业务目标: 完成 FUNC-notification-system-notifications-notif-id-read 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0060
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-notification, OBJ-notifypref
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification

### Physical Data Operations
- 核心 CUD 表: TBL-sys-notification R/C/U, TBL-sys-notify-pref R/C/U
- 依赖查询表: TBL-sys-notification R, TBL-sys-notify-pref R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-notification-system-notifications-notif-id-read
- 证据摘要: OpenAPI + source code path mapping


## FUNC-notification-system-notifications-read-all

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-notification-system-notifications-read-all
- 业务目标: 完成 FUNC-notification-system-notifications-read-all 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0061
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-notification, OBJ-notifypref
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification

### Physical Data Operations
- 核心 CUD 表: TBL-sys-notification R/C/U, TBL-sys-notify-pref R/C/U
- 依赖查询表: TBL-sys-notification R, TBL-sys-notify-pref R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-notification-system-notifications-read-all
- 证据摘要: OpenAPI + source code path mapping


## FUNC-other-system-notification-prefs

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-other-system-notification-prefs
- 业务目标: 完成 FUNC-other-system-notification-prefs 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0062, API-op-0063
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: none
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification

### Physical Data Operations
- 核心 CUD 表: 待细化
- 依赖查询表: 待细化
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-other-system-notification-prefs
- 证据摘要: OpenAPI + source code path mapping


## FUNC-system-config-system-config

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-system-config-system-config
- 业务目标: 完成 FUNC-system-config-system-config 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0064, API-op-0065
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-sysconfig
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-sys-config R/C/U
- 依赖查询表: TBL-sys-config R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-system-config-system-config
- 证据摘要: OpenAPI + source code path mapping


## FUNC-system-version-system-version

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-system-version-system-version
- 业务目标: 完成 FUNC-system-version-system-version 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0066
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: none
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: 待细化
- 依赖查询表: 待细化
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-system-version-system-version
- 证据摘要: OpenAPI + source code path mapping


## FUNC-system-config-system-config-key

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-system-config-system-config-key
- 业务目标: 完成 FUNC-system-config-system-config-key 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0067
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-sysconfig
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-sys-config R/C/U
- 依赖查询表: TBL-sys-config R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-system-config-system-config-key
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-config-system-ai-config

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-config-system-ai-config
- 业务目标: 完成 FUNC-ai-config-system-ai-config 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0068, API-op-0069
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-sysconfig
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-agent-call-log R/C/U, TBL-sys-config R/C/U
- 依赖查询表: TBL-sys-agent-call-log R, TBL-sys-config R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-config-system-ai-config
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-config-system-ai-config-test

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-config-system-ai-config-test
- 业务目标: 完成 FUNC-ai-config-system-ai-config-test 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0070
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-sysconfig
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-agent-call-log R/C/U, TBL-sys-config R/C/U
- 依赖查询表: TBL-sys-agent-call-log R, TBL-sys-config R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-config-system-ai-config-test
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-grade-edu-grades

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-grade-edu-grades
- 业务目标: 完成 FUNC-teacher-grade-edu-grades 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0071, API-op-0072
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-grade
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D
- 依赖查询表: TBL-edu-grade R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-grade-edu-grades
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-grade-edu-grades-grade-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-grade-edu-grades-grade-id
- 业务目标: 完成 FUNC-teacher-grade-edu-grades-grade-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0073, API-op-0074
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-grade
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D
- 依赖查询表: TBL-edu-grade R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-grade-edu-grades-grade-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-subject-edu-subjects

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-subject-edu-subjects
- 业务目标: 完成 FUNC-teacher-subject-edu-subjects 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0075, API-op-0076
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-grade, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-subject R/C/U/D
- 依赖查询表: TBL-edu-grade R, TBL-edu-subject R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-subject-edu-subjects
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-subject-edu-subjects-subject-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-subject-edu-subjects-subject-id
- 业务目标: 完成 FUNC-teacher-subject-edu-subjects-subject-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0077, API-op-0078
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-grade, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-subject R/C/U/D
- 依赖查询表: TBL-edu-grade R, TBL-edu-subject R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-subject-edu-subjects-subject-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-subject-edu-subjects-subject-id-clone

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-subject-edu-subjects-subject-id-clone
- 业务目标: 完成 FUNC-teacher-subject-edu-subjects-subject-id-clone 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0079
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-grade, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-subject R/C/U/D
- 依赖查询表: TBL-edu-grade R, TBL-edu-subject R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-subject-edu-subjects-subject-id-clone
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-edu-classes-public

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-edu-classes-public
- 业务目标: 完成 FUNC-teacher-class-edu-classes-public 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0080
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-edu-grade R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-edu-grade R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-edu-classes-public
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-edu-classes

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-edu-classes
- 业务目标: 完成 FUNC-teacher-class-edu-classes 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0081, API-op-0082
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-edu-grade R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-edu-grade R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-edu-classes
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-edu-classes-stats

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-edu-classes-stats
- 业务目标: 完成 FUNC-teacher-class-edu-classes-stats 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0083
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-edu-grade R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-edu-grade R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-edu-classes-stats
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-edu-classes-class-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-edu-classes-class-id
- 业务目标: 完成 FUNC-teacher-class-edu-classes-class-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0084, API-op-0085
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-edu-grade R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-edu-grade R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-edu-classes-class-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-edu-classes-batch

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-edu-classes-batch
- 业务目标: 完成 FUNC-teacher-class-edu-classes-batch 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0086
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-edu-grade R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-edu-grade R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-edu-classes-batch
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-edu-classes-class-id-students

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-edu-classes-class-id-students
- 业务目标: 完成 FUNC-teacher-class-edu-classes-class-id-students 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0087, API-op-0088
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-edu-grade R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-edu-grade R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-edu-classes-class-id-students
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-edu-classes-class-id-students-export

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-edu-classes-class-id-students-export
- 业务目标: 完成 FUNC-teacher-class-edu-classes-class-id-students-export 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0089
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-edu-grade R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-edu-grade R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-edu-classes-class-id-students-export
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-edu-classes-class-id-students-batch-remove

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-edu-classes-class-id-students-batch-remove
- 业务目标: 完成 FUNC-teacher-class-edu-classes-class-id-students-batch-remove 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0090
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-edu-grade R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-edu-grade R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-edu-classes-class-id-students-batch-remove
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-edu-classes-class-id-students-student-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-edu-classes-class-id-students-student-id
- 业务目标: 完成 FUNC-teacher-class-edu-classes-class-id-students-student-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0091
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-grade, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-edu-grade R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-edu-grade R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-edu-classes-class-id-students-student-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-other-edu-people-brief

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-other-edu-people-brief
- 业务目标: 完成 FUNC-other-edu-people-brief 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0092
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: none
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: 待细化
- 依赖查询表: 待细化
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-other-edu-people-brief
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-request-edu-class-requests

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-request-edu-class-requests
- 业务目标: 完成 FUNC-teacher-class-request-edu-class-requests 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0093, API-op-0094
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-request-edu-class-requests
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-request-edu-class-requests-mine

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-request-edu-class-requests-mine
- 业务目标: 完成 FUNC-teacher-class-request-edu-class-requests-mine 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0095
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-request-edu-class-requests-mine
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-request-edu-class-requests-req-id-review

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-request-edu-class-requests-req-id-review
- 业务目标: 完成 FUNC-teacher-class-request-edu-class-requests-req-id-review 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0096
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-request-edu-class-requests-req-id-review
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-class-request-edu-class-requests-req-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-class-request-edu-class-requests-req-id
- 业务目标: 完成 FUNC-teacher-class-request-edu-class-requests-req-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0097
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-classrequest, OBJ-notification
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-class-request R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-class-request R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-class-request-edu-class-requests-req-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-teaching-edu-teaching-matrix

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-teaching-edu-teaching-matrix
- 业务目标: 完成 FUNC-teacher-teaching-edu-teaching-matrix 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0098
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-subject, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-subject R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-subject R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-teaching-edu-teaching-matrix
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-teaching-edu-teaching-assignments

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-teaching-edu-teaching-assignments
- 业务目标: 完成 FUNC-teacher-teaching-edu-teaching-assignments 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0099, API-op-0100
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-subject, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-subject R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-subject R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-teaching-edu-teaching-assignments
- 证据摘要: OpenAPI + source code path mapping


## FUNC-teacher-teaching-edu-teaching-assignments-asg-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-teacher-teaching-edu-teaching-assignments-asg-id
- 业务目标: 完成 FUNC-teacher-teaching-edu-teaching-assignments-asg-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-teaching-basics
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0101
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-class, OBJ-subject, OBJ-teachingassignment, OBJ-user
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-class R/C/U/D, TBL-edu-subject R/C/U/D, TBL-edu-teaching-assignment R/C/U/D, TBL-sys-user R/C/U
- 依赖查询表: TBL-edu-class R, TBL-edu-subject R, TBL-edu-teaching-assignment R, TBL-sys-user R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-teacher-teaching-edu-teaching-assignments-asg-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-graph

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-graph
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-graph 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0102
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-graph
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-tree

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-tree
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-tree 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0103
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-tree
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge
- 业务目标: 完成 FUNC-knowledge-edu-knowledge 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0104, API-op-0105
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-list

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-list
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-list 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0106
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-list
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-stats

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-stats
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-stats 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0107
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-stats
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-template

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-template
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-template 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0108
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-template
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-export

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-export
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-export 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0109
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-export
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-mastery-overview

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-mastery-overview
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-mastery-overview 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0110
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-mastery-overview
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-search

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-search
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-search 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0111
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-search
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-rag-status

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-rag-status
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-rag-status 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0112
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-rag-status
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-kp-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-kp-id
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-kp-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0113, API-op-0114, API-op-0115
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-kp-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-kp-id-attachments

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-kp-id-attachments
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-kp-id-attachments 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0116, API-op-0117
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-kp-id-attachments
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-kp-id-attachments-att-id
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0118, API-op-0119
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-batch

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-batch
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-batch 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0120
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-batch
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-import

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-import
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-import 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0121
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-import
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-reindex

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-reindex
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-reindex 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0122
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-reindex
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-purge-generic

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-purge-generic
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-purge-generic 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0123
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-purge-generic
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-diagnosis-targets

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-diagnosis-targets
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-diagnosis-targets 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0124
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-diagnosis-targets
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-diagnosis-sessions

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-diagnosis-sessions
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-diagnosis-sessions 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0125
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-diagnosis-sessions
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-diagnosis-sessions-session-id
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0126
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-next

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-diagnosis-sessions-session-id-next
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-next 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0127
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-next
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-answers

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-diagnosis-sessions-session-id-answers
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-answers 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0128
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-answers
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-summary

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-diagnosis-sessions-session-id-summary
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-summary 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0129
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-summary
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-kp-id-prerequisites

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-kp-id-prerequisites
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-kp-id-prerequisites 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0130, API-op-0131
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-kp-id-prerequisites
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-kp-id-dependents

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-kp-id-dependents
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-kp-id-dependents 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0132
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-kp-id-dependents
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-kp-id-prerequisites-prerequisite-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-kp-id-prerequisites-prerequisite-id
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-kp-id-prerequisites-prerequisite-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0133
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-kp-id-prerequisites-prerequisite-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-ai-generate

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-ai-generate
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-ai-generate 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0134
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-ai-generate
- 证据摘要: OpenAPI + source code path mapping


## FUNC-knowledge-edu-knowledge-ai-enrich

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-knowledge-edu-knowledge-ai-enrich
- 业务目标: 完成 FUNC-knowledge-edu-knowledge-ai-enrich 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0135
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-grade, OBJ-knowledgemastery, OBJ-knowledgepoint, OBJ-knowledgeprerequisite, OBJ-subject
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-grade R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-knowledge-point R/C/U/D, TBL-edu-knowledge-prerequisite R/C/U/D, TBL-edu-subject R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-grade R, TBL-edu-knowledge-mastery R, TBL-edu-knowledge-point R, TBL-edu-knowledge-prerequisite R, TBL-edu-subject R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-knowledge-edu-knowledge-ai-enrich
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions
- 业务目标: 完成 FUNC-question-question-questions 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0136, API-op-0137
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-stats

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-stats
- 业务目标: 完成 FUNC-question-question-questions-stats 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0138
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-stats
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-batch-create

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-batch-create
- 业务目标: 完成 FUNC-question-question-questions-batch-create 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0139
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-batch-create
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-batch

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-batch
- 业务目标: 完成 FUNC-question-question-questions-batch 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0140
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-batch
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-template

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-template
- 业务目标: 完成 FUNC-question-question-questions-template 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0141
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-template
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-q-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-q-id
- 业务目标: 完成 FUNC-question-question-questions-q-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0142, API-op-0143, API-op-0144
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-q-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-q-id-status

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-q-id-status
- 业务目标: 完成 FUNC-question-question-questions-q-id-status 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0145
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-q-id-status
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-q-id-duplicates

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-q-id-duplicates
- 业务目标: 完成 FUNC-question-question-questions-q-id-duplicates 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0146
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-q-id-duplicates
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-import

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-import
- 业务目标: 完成 FUNC-question-question-questions-import 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0147
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-import
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-export

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-export
- 业务目标: 完成 FUNC-question-question-questions-export 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0148
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-export
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers
- 业务目标: 完成 FUNC-question-question-papers 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0149, API-op-0150
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-stats

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-stats
- 业务目标: 完成 FUNC-question-question-papers-stats 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0151
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-stats
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-batch

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-batch
- 业务目标: 完成 FUNC-question-question-papers-batch 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0152
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-batch
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id
- 业务目标: 完成 FUNC-question-question-papers-paper-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0153, API-op-0154, API-op-0155
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-archive

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-archive
- 业务目标: 完成 FUNC-question-question-papers-paper-id-archive 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0156
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-archive
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-copy

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-copy
- 业务目标: 完成 FUNC-question-question-papers-paper-id-copy 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0157
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-copy
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-share

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-share
- 业务目标: 完成 FUNC-question-question-papers-paper-id-share 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0158
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-share
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-export

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-export
- 业务目标: 完成 FUNC-question-question-papers-paper-id-export 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0159
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-export
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-ai-variants

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-ai-variants
- 业务目标: 完成 FUNC-question-question-questions-ai-variants 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0160
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-ai-variants
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-ai-enrich

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-ai-enrich
- 业务目标: 完成 FUNC-question-question-questions-ai-enrich 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0161
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-ai-enrich
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-questions-ai-quality

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-questions-ai-quality
- 业务目标: 完成 FUNC-question-question-questions-ai-quality 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0162
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-questions-ai-quality
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-ai-analyze

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-ai-analyze
- 业务目标: 完成 FUNC-question-question-papers-paper-id-ai-analyze 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0163
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-ai-analyze
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-ai-recommend

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-ai-recommend
- 业务目标: 完成 FUNC-question-question-papers-paper-id-ai-recommend 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0164
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-ai-recommend
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-standards

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-standards
- 业务目标: 完成 FUNC-question-question-standards 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0165, API-op-0166
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-standards
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-standards-options

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-standards-options
- 业务目标: 完成 FUNC-question-question-standards-options 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0167
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-standards-options
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-standards-std-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-standards-std-id
- 业务目标: 完成 FUNC-question-question-standards-std-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0168, API-op-0169, API-op-0170
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-standards-std-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-standards-std-id-duplicate

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-standards-std-id-duplicate
- 业务目标: 完成 FUNC-question-question-standards-std-id-duplicate 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0171
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-standards-std-id-duplicate
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-standards-generate-missing

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-standards-generate-missing
- 业务目标: 完成 FUNC-question-question-standards-generate-missing 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0172
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-standards-generate-missing
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-standards-seed

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-standards-seed
- 业务目标: 完成 FUNC-question-question-standards-seed 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0173
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-standards-seed
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-standards-std-id-reset

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-standards-std-id-reset
- 业务目标: 完成 FUNC-question-question-standards-std-id-reset 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0174
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-standards-std-id-reset
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-compose-regenerate

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-compose-regenerate
- 业务目标: 完成 FUNC-question-question-papers-compose-regenerate 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0175
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-compose-regenerate
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-compose-preview

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-compose-preview
- 业务目标: 完成 FUNC-question-question-papers-compose-preview 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0176
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-compose-preview
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-compose-ai

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-compose-ai
- 业务目标: 完成 FUNC-question-question-papers-compose-ai 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0177
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-compose-ai
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-compose-save

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-compose-save
- 业务目标: 完成 FUNC-question-question-papers-compose-save 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0178
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-compose-save
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-preview

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-preview
- 业务目标: 完成 FUNC-question-question-papers-paper-id-preview 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0179
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-preview
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-items

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-items
- 业务目标: 完成 FUNC-question-question-papers-paper-id-items 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0180
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-items
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-items-item-id-regenerate

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-items-item-id-regenerate
- 业务目标: 完成 FUNC-question-question-papers-paper-id-items-item-id-regenerate 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0181
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-items-item-id-regenerate
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-items-item-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-items-item-id
- 业务目标: 完成 FUNC-question-question-papers-paper-id-items-item-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0182
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-items-item-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-sections-rename

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-sections-rename
- 业务目标: 完成 FUNC-question-question-papers-paper-id-sections-rename 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0183
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-sections-rename
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-restructure

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-restructure
- 业务目标: 完成 FUNC-question-question-papers-paper-id-restructure 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0184
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-restructure
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-versions

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-versions
- 业务目标: 完成 FUNC-question-question-papers-paper-id-versions 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0185
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-versions
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-versions-version

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-versions-version
- 业务目标: 完成 FUNC-question-question-papers-paper-id-versions-version 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0186
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-versions-version
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-versions-version-diff

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-versions-version-diff
- 业务目标: 完成 FUNC-question-question-papers-paper-id-versions-version-diff 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0187
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-versions-version-diff
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-versions-version-restore

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-versions-version-restore
- 业务目标: 完成 FUNC-question-question-papers-paper-id-versions-version-restore 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0188
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-versions-version-restore
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-library-list

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-library-list
- 业务目标: 完成 FUNC-question-question-papers-library-list 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0189
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-library-list
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-favorite

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-favorite
- 业务目标: 完成 FUNC-question-question-papers-paper-id-favorite 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0190
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-favorite
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-share-scope

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-share-scope
- 业务目标: 完成 FUNC-question-question-papers-paper-id-share-scope 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0191
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-share-scope
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-share-info

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-share-info
- 业务目标: 完成 FUNC-question-question-papers-paper-id-share-info 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0192
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-share-info
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-review

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-review
- 业务目标: 完成 FUNC-question-question-papers-paper-id-review 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0193
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-review
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-export-docx

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-export-docx
- 业务目标: 完成 FUNC-question-question-papers-paper-id-export-docx 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0194
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-export-docx
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-export-pdf

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-export-pdf
- 业务目标: 完成 FUNC-question-question-papers-paper-id-export-pdf 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0195
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-export-pdf
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-export-answer-sheet

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-export-answer-sheet
- 业务目标: 完成 FUNC-question-question-papers-paper-id-export-answer-sheet 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0196
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-export-answer-sheet
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-export-html

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-export-html
- 业务目标: 完成 FUNC-question-question-papers-paper-id-export-html 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0197
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-export-html
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-paper-id-export-jobs

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-paper-id-export-jobs
- 业务目标: 完成 FUNC-question-question-papers-paper-id-export-jobs 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0198
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-paper-id-export-jobs
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-export-jobs-job-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-export-jobs-job-id
- 业务目标: 完成 FUNC-question-question-papers-export-jobs-job-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0199
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-export-jobs-job-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-export-jobs-job-id-file

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-export-jobs-job-id-file
- 业务目标: 完成 FUNC-question-question-papers-export-jobs-job-id-file 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0200
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-export-jobs-job-id-file
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-compose-ai-async

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-compose-ai-async
- 业务目标: 完成 FUNC-question-question-papers-compose-ai-async 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0201
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-compose-ai-async
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-compose-jobs-job-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-compose-jobs-job-id
- 业务目标: 完成 FUNC-question-question-papers-compose-jobs-job-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0202
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-scheduler

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-compose-jobs-job-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-question-question-papers-compose-jobs-job-id-cancel

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-question-question-papers-compose-jobs-job-id-cancel
- 业务目标: 完成 FUNC-question-question-papers-compose-jobs-job-id-cancel 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-question-paper / SCN-teacher-prepare / CAP-question-bank
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0203
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment, OBJ-examstandard, OBJ-paper, OBJ-paperfavorite, OBJ-paperitem, OBJ-papershare, OBJ-paperversion, OBJ-question, OBJ-questionknowledge
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-scheduler

### Physical Data Operations
- 核心 CUD 表: TBL-edu-exam-standard R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-favorite R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-paper-share R/C/U/D, TBL-edu-paper-version R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-knowledge R/C/U/D, TBL-sys-attachment R/C/U
- 依赖查询表: TBL-edu-exam-standard R, TBL-edu-paper R, TBL-edu-paper-favorite R, TBL-edu-paper-item R, TBL-edu-paper-share R, TBL-edu-paper-version R, TBL-edu-question R, TBL-edu-question-knowledge R, TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-question-question-papers-compose-jobs-job-id-cancel
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-tasks

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-tasks
- 业务目标: 完成 FUNC-task-task-tasks 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0204, API-op-0205
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-tasks
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-tasks-stats

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-tasks-stats
- 业务目标: 完成 FUNC-task-task-tasks-stats 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0206
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-tasks-stats
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-tasks-batch

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-tasks-batch
- 业务目标: 完成 FUNC-task-task-tasks-batch 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0207
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-tasks-batch
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-tasks-task-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-tasks-task-id
- 业务目标: 完成 FUNC-task-task-tasks-task-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0208, API-op-0209, API-op-0210
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-tasks-task-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-tasks-task-id-submissions

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-tasks-task-id-submissions
- 业务目标: 完成 FUNC-task-task-tasks-task-id-submissions 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0211
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-tasks-task-id-submissions
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-my-tasks

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-my-tasks
- 业务目标: 完成 FUNC-task-task-my-tasks 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0212
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-my-tasks
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-tasks-task-id-paper

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-tasks-task-id-paper
- 业务目标: 完成 FUNC-task-task-tasks-task-id-paper 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0213
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-tasks-task-id-paper
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-tasks-task-id-submit

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-tasks-task-id-submit
- 业务目标: 完成 FUNC-task-task-tasks-task-id-submit 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0214
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-tasks-task-id-submit
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-tasks-task-id-heartbeat

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-tasks-task-id-heartbeat
- 业务目标: 完成 FUNC-task-task-tasks-task-id-heartbeat 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0215
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-tasks-task-id-heartbeat
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-submissions-submission-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-submissions-submission-id
- 业务目标: 完成 FUNC-task-task-submissions-submission-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0216
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-submissions-submission-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-my-scores

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-my-scores
- 业务目标: 完成 FUNC-task-task-my-scores 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0217
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-my-scores
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-tasks-task-id-pending-students

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-tasks-task-id-pending-students
- 业务目标: 完成 FUNC-task-task-tasks-task-id-pending-students 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0218
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-tasks-task-id-pending-students
- 证据摘要: OpenAPI + source code path mapping


## FUNC-task-task-tasks-task-id-urge

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-task-task-tasks-task-id-urge
- 业务目标: 完成 FUNC-task-task-tasks-task-id-urge 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-task-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0219
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-notification, OBJ-paper, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-taskassignment, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-notification

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-task-assignment R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-notification R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-task-assignment R, TBL-edu-wrong-question R, TBL-sys-notification R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-task-task-tasks-task-id-urge
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-pending

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-pending
- 业务目标: 完成 FUNC-grading-grading-pending 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0220
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-pending
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-submissions

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-submissions
- 业务目标: 完成 FUNC-grading-grading-submissions 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0221
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-submissions
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-stats

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-stats
- 业务目标: 完成 FUNC-grading-grading-stats 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0222
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-stats
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-submissions-submission-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-submissions-submission-id
- 业务目标: 完成 FUNC-grading-grading-submissions-submission-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0223
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-submissions-submission-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-submissions-submission-id-grade

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-submissions-submission-id-grade
- 业务目标: 完成 FUNC-grading-grading-submissions-submission-id-grade 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0224
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-submissions-submission-id-grade
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-submissions-submission-id-reject

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-submissions-submission-id-reject
- 业务目标: 完成 FUNC-grading-grading-submissions-submission-id-reject 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0225
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-submissions-submission-id-reject
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-submissions-submission-id-publish

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-submissions-submission-id-publish
- 业务目标: 完成 FUNC-grading-grading-submissions-submission-id-publish 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0226
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-submissions-submission-id-publish
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-batch-grade

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-batch-grade
- 业务目标: 完成 FUNC-grading-grading-batch-grade 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0227
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-batch-grade
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-batch-publish

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-batch-publish
- 业务目标: 完成 FUNC-grading-grading-batch-publish 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0228
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-batch-publish
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-unpublish

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-unpublish
- 业务目标: 完成 FUNC-grading-grading-unpublish 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0229
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-unpublish
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-tasks-task-id-report

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-tasks-task-id-report
- 业务目标: 完成 FUNC-grading-grading-tasks-task-id-report 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0230
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-tasks-task-id-report
- 证据摘要: OpenAPI + source code path mapping


## FUNC-grading-grading-tasks-task-id-ai-comment

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-grading-grading-tasks-task-id-ai-comment
- 业务目标: 完成 FUNC-grading-grading-tasks-task-id-ai-comment 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-task-assessment / SCN-teacher-teach / CAP-grading
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0231
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-answer, OBJ-knowledgemastery, OBJ-paperitem, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-paper-item R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-grading-grading-tasks-task-id-ai-comment
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-notes

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-notes
- 业务目标: 完成 FUNC-learning-learning-notes 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0232, API-op-0233
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-notes
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-notes-shared

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-notes-shared
- 业务目标: 完成 FUNC-learning-learning-notes-shared 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0234
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-notes-shared
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-notes-note-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-notes-note-id
- 业务目标: 完成 FUNC-learning-learning-notes-note-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0235, API-op-0236, API-op-0237
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-notes-note-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-notes-note-id-share

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-notes-note-id-share
- 业务目标: 完成 FUNC-learning-learning-notes-note-id-share 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0238
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-notes-note-id-share
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-notes-note-id-organize

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-notes-note-id-organize
- 业务目标: 完成 FUNC-learning-learning-notes-note-id-organize 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0239
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-notes-note-id-organize
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-notes-note-id-export

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-notes-note-id-export
- 业务目标: 完成 FUNC-learning-learning-notes-note-id-export 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0240
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-notes-note-id-export
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-wrong-questions

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-wrong-questions
- 业务目标: 完成 FUNC-learning-learning-wrong-questions 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0241
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-wrong-questions
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-wrong-questions-wid

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-wrong-questions-wid
- 业务目标: 完成 FUNC-learning-learning-wrong-questions-wid 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0242
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-wrong-questions-wid
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-wrong-questions-wid-analyze

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-wrong-questions-wid-analyze
- 业务目标: 完成 FUNC-learning-learning-wrong-questions-wid-analyze 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0243
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-wrong-questions-wid-analyze
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-wrong-questions-wid-redo

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-wrong-questions-wid-redo
- 业务目标: 完成 FUNC-learning-learning-wrong-questions-wid-redo 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0244
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-wrong-questions-wid-redo
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-wrong-questions-export

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-wrong-questions-export
- 业务目标: 完成 FUNC-learning-learning-wrong-questions-export 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0245
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-wrong-questions-export
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-review-plans

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-review-plans
- 业务目标: 完成 FUNC-learning-learning-review-plans 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0246
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-review-plans
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-review-plans-plan-id-complete

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-review-plans-plan-id-complete
- 业务目标: 完成 FUNC-learning-learning-review-plans-plan-id-complete 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0247
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-review-plans-plan-id-complete
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-review-mastery

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-review-mastery
- 业务目标: 完成 FUNC-learning-learning-review-mastery 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0248
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-review-mastery
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-review-plan

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-review-plan
- 业务目标: 完成 FUNC-learning-learning-review-plan 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0249
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-review-plan
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-practice

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-practice
- 业务目标: 完成 FUNC-learning-learning-practice 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0250
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-practice
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-practice-history

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-practice-history
- 业务目标: 完成 FUNC-learning-learning-practice-history 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0251
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-practice-history
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-practice-task-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-practice-task-id
- 业务目标: 完成 FUNC-learning-learning-practice-task-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0252
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-practice-task-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-favorites

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-favorites
- 业务目标: 完成 FUNC-learning-learning-favorites 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0253, API-op-0254
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-favorites
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-favorites-fav-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-favorites-fav-id
- 业务目标: 完成 FUNC-learning-learning-favorites-fav-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0255
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-favorites-fav-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-favorites-by-question-question-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-favorites-by-question-question-id
- 业务目标: 完成 FUNC-learning-learning-favorites-by-question-question-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0256
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-favorites-by-question-question-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-favorites-check-batch

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-favorites-check-batch
- 业务目标: 完成 FUNC-learning-learning-favorites-check-batch 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0257
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-favorites-check-batch
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-favorites-check-question-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-favorites-check-question-id
- 业务目标: 完成 FUNC-learning-learning-favorites-check-question-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0258
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-favorites-check-question-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-favorites-practice

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-favorites-practice
- 业务目标: 完成 FUNC-learning-learning-favorites-practice 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0259
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-favorites-practice
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-wrong-questions-wid-variant

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-wrong-questions-wid-variant
- 业务目标: 完成 FUNC-learning-learning-wrong-questions-wid-variant 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0260
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-wrong-questions-wid-variant
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-custom-paper

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-custom-paper
- 业务目标: 完成 FUNC-learning-learning-custom-paper 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0261
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-custom-paper
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-goals

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-goals
- 业务目标: 完成 FUNC-learning-learning-goals 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0262, API-op-0263
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-goals
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-goals-goal-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-goals-goal-id
- 业务目标: 完成 FUNC-learning-learning-goals-goal-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0264, API-op-0265
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-goals-goal-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-goals-goal-id-checkin

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-goals-goal-id-checkin
- 业务目标: 完成 FUNC-learning-learning-goals-goal-id-checkin 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0266
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-goals-goal-id-checkin
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-path-recommend

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-path-recommend
- 业务目标: 完成 FUNC-learning-learning-path-recommend 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0267
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-path-recommend
- 证据摘要: OpenAPI + source code path mapping


## FUNC-learning-learning-flashcards

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-learning-learning-flashcards
- 业务目标: 完成 FUNC-learning-learning-flashcards 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-learning-support / SCN-student-learn / CAP-learning-tools
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0268
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-knowledgemastery, OBJ-note, OBJ-question, OBJ-questionfavorite, OBJ-reviewplan, OBJ-studycheckin, OBJ-studygoal, OBJ-studyrecord, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-note R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-question-favorite R/C/U/D, TBL-edu-review-plan R/C/U/D, TBL-edu-study-checkin R/C/U/D, TBL-edu-study-goal R/C/U/D, TBL-edu-study-record R/C/U/D, TBL-edu-wrong-question R/C/U/D
- 依赖查询表: TBL-edu-knowledge-mastery R, TBL-edu-note R, TBL-edu-question R, TBL-edu-question-favorite R, TBL-edu-review-plan R, TBL-edu-study-checkin R, TBL-edu-study-goal R, TBL-edu-study-record R, TBL-edu-wrong-question R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-learning-learning-flashcards
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-list

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-list
- 业务目标: 完成 FUNC-ai-agent-agent-list 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0269
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-list
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-status

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-status
- 业务目标: 完成 FUNC-ai-agent-agent-status 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0270
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-status
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-chat

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-chat
- 业务目标: 完成 FUNC-ai-agent-agent-chat 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0271
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-chat
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-chat-stream

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-chat-stream
- 业务目标: 完成 FUNC-ai-agent-agent-chat-stream 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0272
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-chat-stream
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-question-generator

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-question-generator
- 业务目标: 完成 FUNC-ai-agent-agent-question-generator 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0273
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-question-generator
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-paper-composer

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-paper-composer
- 业务目标: 完成 FUNC-ai-agent-agent-paper-composer 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0274
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-paper-composer
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-grading

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-grading
- 业务目标: 完成 FUNC-ai-agent-agent-grading 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0275
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-grading
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-study-planner

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-study-planner
- 业务目标: 完成 FUNC-ai-agent-agent-study-planner 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0276
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-study-planner
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-tutor

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-tutor
- 业务目标: 完成 FUNC-ai-agent-agent-tutor 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0277
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-tutor
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-note-organizer

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-note-organizer
- 业务目标: 完成 FUNC-ai-agent-agent-note-organizer 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0278
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-note-organizer
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-jobs

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-jobs
- 业务目标: 完成 FUNC-ai-agent-agent-jobs 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0279, API-op-0280
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-jobs
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-jobs-job-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-jobs-job-id
- 业务目标: 完成 FUNC-ai-agent-agent-jobs-job-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0281
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-jobs-job-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ai-agent-agent-logs

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ai-agent-agent-logs
- 业务目标: 完成 FUNC-ai-agent-agent-logs 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-ai-services / SCN-ai-assist / CAP-ai-assistance
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0282
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentcalllog, OBJ-agentjob, OBJ-agentrate, OBJ-llmbreakerstate, OBJ-paper, OBJ-paperitem, OBJ-question
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-paper R/C/U/D, TBL-edu-paper-item R/C/U/D, TBL-edu-question R/C/U/D, TBL-sys-agent-call-log R/C/U, TBL-sys-agent-job R/C/U, TBL-sys-agent-rate R/C/U, TBL-sys-llm-breaker R/C/U
- 依赖查询表: TBL-edu-paper R, TBL-edu-paper-item R, TBL-edu-question R, TBL-sys-agent-call-log R, TBL-sys-agent-job R, TBL-sys-agent-rate R, TBL-sys-llm-breaker R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ai-agent-agent-logs
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-student-overview

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-student-overview
- 业务目标: 完成 FUNC-report-report-student-overview 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0283
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-student-overview
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-student-score-trend

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-student-score-trend
- 业务目标: 完成 FUNC-report-report-student-score-trend 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0284
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-student-score-trend
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-student-knowledge-radar

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-student-knowledge-radar
- 业务目标: 完成 FUNC-report-report-student-knowledge-radar 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0285
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-student-knowledge-radar
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-student-wrong-analysis

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-student-wrong-analysis
- 业务目标: 完成 FUNC-report-report-student-wrong-analysis 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0286
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-student-wrong-analysis
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-student-learning-suggestion

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-student-learning-suggestion
- 业务目标: 完成 FUNC-report-report-student-learning-suggestion 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0287
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: student scope for own data; teacher may view class scope.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-student-learning-suggestion
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-teacher-class-overview

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-teacher-class-overview
- 业务目标: 完成 FUNC-report-report-teacher-class-overview 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0288
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-teacher-class-overview
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-teacher-student-comparison

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-teacher-student-comparison
- 业务目标: 完成 FUNC-report-report-teacher-student-comparison 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0289
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-teacher-student-comparison
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-teacher-student-detail

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-teacher-student-detail
- 业务目标: 完成 FUNC-report-report-teacher-student-detail 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0290
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-teacher-student-detail
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-teacher-knowledge-effect

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-teacher-knowledge-effect
- 业务目标: 完成 FUNC-report-report-teacher-knowledge-effect 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0291
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-teacher-knowledge-effect
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-teacher-class-weak-points

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-teacher-class-weak-points
- 业务目标: 完成 FUNC-report-report-teacher-class-weak-points 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0292
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-teacher-class-weak-points
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-admin-overview

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-admin-overview
- 业务目标: 完成 FUNC-report-report-admin-overview 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0293
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-admin-overview
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-admin-grade-comparison

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-admin-grade-comparison
- 业务目标: 完成 FUNC-report-report-admin-grade-comparison 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0294
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-admin-grade-comparison
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-admin-subject-comparison

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-admin-subject-comparison
- 业务目标: 完成 FUNC-report-report-admin-subject-comparison 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0295
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-admin-subject-comparison
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-admin-system-runtime

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-admin-system-runtime
- 业务目标: 完成 FUNC-report-report-admin-system-runtime 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0296
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-admin-system-runtime
- 证据摘要: OpenAPI + source code path mapping


## FUNC-report-report-export-excel

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-report-report-export-excel
- 业务目标: 完成 FUNC-report-report-export-excel 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-reporting / SCN-teacher-teach / CAP-reporting
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0297
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-answer, OBJ-knowledgemastery, OBJ-question, OBJ-submission, OBJ-task, OBJ-wrongquestion
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-edu-answer R/C/U/D, TBL-edu-knowledge-mastery R/C/U/D, TBL-edu-question R/C/U/D, TBL-edu-submission R/C/U/D, TBL-edu-task R/C/U/D, TBL-edu-wrong-question R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-answer R, TBL-edu-knowledge-mastery R, TBL-edu-question R, TBL-edu-submission R, TBL-edu-task R, TBL-edu-wrong-question R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-report-report-export-excel
- 证据摘要: OpenAPI + source code path mapping


## FUNC-log-logs-login

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-log-logs-login
- 业务目标: 完成 FUNC-log-logs-login 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0298
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-errorlog, OBJ-loginlog, OBJ-operationlog
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-auth-security, COMMON-authorization, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-sys-error-log R/C/U, TBL-sys-login-log R/C/U, TBL-sys-operation-log R/C/U
- 依赖查询表: TBL-sys-error-log R, TBL-sys-login-log R, TBL-sys-operation-log R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-log-logs-login
- 证据摘要: OpenAPI + source code path mapping


## FUNC-log-logs-operation

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-log-logs-operation
- 业务目标: 完成 FUNC-log-logs-operation 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0299
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-errorlog, OBJ-loginlog, OBJ-operationlog
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-sys-error-log R/C/U, TBL-sys-login-log R/C/U, TBL-sys-operation-log R/C/U
- 依赖查询表: TBL-sys-error-log R, TBL-sys-login-log R, TBL-sys-operation-log R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-log-logs-operation
- 证据摘要: OpenAPI + source code path mapping


## FUNC-log-logs-error

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-log-logs-error
- 业务目标: 完成 FUNC-log-logs-error 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0300
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-errorlog, OBJ-loginlog, OBJ-operationlog
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-sys-error-log R/C/U, TBL-sys-login-log R/C/U, TBL-sys-operation-log R/C/U
- 依赖查询表: TBL-sys-error-log R, TBL-sys-login-log R, TBL-sys-operation-log R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-log-logs-error
- 证据摘要: OpenAPI + source code path mapping


## FUNC-log-logs-export

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-log-logs-export
- 业务目标: 完成 FUNC-log-logs-export 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0301
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-errorlog, OBJ-loginlog, OBJ-operationlog
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job

### Physical Data Operations
- 核心 CUD 表: TBL-sys-error-log R/C/U, TBL-sys-login-log R/C/U, TBL-sys-operation-log R/C/U
- 依赖查询表: TBL-sys-error-log R, TBL-sys-login-log R, TBL-sys-operation-log R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-log-logs-export
- 证据摘要: OpenAPI + source code path mapping


## FUNC-job-jobs-handlers

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-job-jobs-handlers
- 业务目标: 完成 FUNC-job-jobs-handlers 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0302
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-jobexecutionlog, OBJ-scheduledjob
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-scheduler

### Physical Data Operations
- 核心 CUD 表: TBL-sys-job-execution-log R/C/U, TBL-sys-scheduled-job R/C/U
- 依赖查询表: TBL-sys-job-execution-log R, TBL-sys-scheduled-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-job-jobs-handlers
- 证据摘要: OpenAPI + source code path mapping


## FUNC-job-jobs

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-job-jobs
- 业务目标: 完成 FUNC-job-jobs 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0303, API-op-0304
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-jobexecutionlog, OBJ-scheduledjob
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-scheduler

### Physical Data Operations
- 核心 CUD 表: TBL-sys-job-execution-log R/C/U, TBL-sys-scheduled-job R/C/U
- 依赖查询表: TBL-sys-job-execution-log R, TBL-sys-scheduled-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-job-jobs
- 证据摘要: OpenAPI + source code path mapping


## FUNC-job-jobs-job-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-job-jobs-job-id
- 业务目标: 完成 FUNC-job-jobs-job-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0305, API-op-0306
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-jobexecutionlog, OBJ-scheduledjob
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-scheduler

### Physical Data Operations
- 核心 CUD 表: TBL-sys-job-execution-log R/C/U, TBL-sys-scheduled-job R/C/U
- 依赖查询表: TBL-sys-job-execution-log R, TBL-sys-scheduled-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-job-jobs-job-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-job-jobs-job-id-toggle

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-job-jobs-job-id-toggle
- 业务目标: 完成 FUNC-job-jobs-job-id-toggle 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0307
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-jobexecutionlog, OBJ-scheduledjob
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-scheduler

### Physical Data Operations
- 核心 CUD 表: TBL-sys-job-execution-log R/C/U, TBL-sys-scheduled-job R/C/U
- 依赖查询表: TBL-sys-job-execution-log R, TBL-sys-scheduled-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-job-jobs-job-id-toggle
- 证据摘要: OpenAPI + source code path mapping


## FUNC-job-jobs-job-id-run

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-job-jobs-job-id-run
- 业务目标: 完成 FUNC-job-jobs-job-id-run 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0308
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-jobexecutionlog, OBJ-scheduledjob
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-scheduler

### Physical Data Operations
- 核心 CUD 表: TBL-sys-job-execution-log R/C/U, TBL-sys-scheduled-job R/C/U
- 依赖查询表: TBL-sys-job-execution-log R, TBL-sys-scheduled-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-job-jobs-job-id-run
- 证据摘要: OpenAPI + source code path mapping


## FUNC-job-jobs-status

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-job-jobs-status
- 业务目标: 完成 FUNC-job-jobs-status 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0309
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-jobexecutionlog, OBJ-scheduledjob
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-scheduler

### Physical Data Operations
- 核心 CUD 表: TBL-sys-job-execution-log R/C/U, TBL-sys-scheduled-job R/C/U
- 依赖查询表: TBL-sys-job-execution-log R, TBL-sys-scheduled-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-job-jobs-status
- 证据摘要: OpenAPI + source code path mapping


## FUNC-job-jobs-job-id-executions

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-job-jobs-job-id-executions
- 业务目标: 完成 FUNC-job-jobs-job-id-executions 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0310
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-jobexecutionlog, OBJ-scheduledjob
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-scheduler

### Physical Data Operations
- 核心 CUD 表: TBL-sys-job-execution-log R/C/U, TBL-sys-scheduled-job R/C/U
- 依赖查询表: TBL-sys-job-execution-log R, TBL-sys-scheduled-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-job-jobs-job-id-executions
- 证据摘要: OpenAPI + source code path mapping


## FUNC-attachment-attachments-public-upload

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-attachment-attachments-public-upload
- 业务目标: 完成 FUNC-attachment-attachments-public-upload 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0311
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-sys-attachment R/C/U
- 依赖查询表: TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: public or pre-auth.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-attachment-attachments-public-upload
- 证据摘要: OpenAPI + source code path mapping


## FUNC-attachment-attachments-upload

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-attachment-attachments-upload
- 业务目标: 完成 FUNC-attachment-attachments-upload 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0312
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-sys-attachment R/C/U
- 依赖查询表: TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-attachment-attachments-upload
- 证据摘要: OpenAPI + source code path mapping


## FUNC-attachment-attachments-batch

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-attachment-attachments-batch
- 业务目标: 完成 FUNC-attachment-attachments-batch 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0313
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-sys-attachment R/C/U
- 依赖查询表: TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-attachment-attachments-batch
- 证据摘要: OpenAPI + source code path mapping


## FUNC-attachment-attachments

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-attachment-attachments
- 业务目标: 完成 FUNC-attachment-attachments 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0314
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-sys-attachment R/C/U
- 依赖查询表: TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-attachment-attachments
- 证据摘要: OpenAPI + source code path mapping


## FUNC-attachment-attachments-att-id-preview

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-attachment-attachments-att-id-preview
- 业务目标: 完成 FUNC-attachment-attachments-att-id-preview 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0315
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-sys-attachment R/C/U
- 依赖查询表: TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-attachment-attachments-att-id-preview
- 证据摘要: OpenAPI + source code path mapping


## FUNC-attachment-attachments-att-id-download

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-attachment-attachments-att-id-download
- 业务目标: 完成 FUNC-attachment-attachments-att-id-download 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0316
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-sys-attachment R/C/U
- 依赖查询表: TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-attachment-attachments-att-id-download
- 证据摘要: OpenAPI + source code path mapping


## FUNC-attachment-attachments-att-id-bind

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-attachment-attachments-att-id-bind
- 业务目标: 完成 FUNC-attachment-attachments-att-id-bind 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0317
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-sys-attachment R/C/U
- 依赖查询表: TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-attachment-attachments-att-id-bind
- 证据摘要: OpenAPI + source code path mapping


## FUNC-attachment-attachments-att-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-attachment-attachments-att-id
- 业务目标: 完成 FUNC-attachment-attachments-att-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0318
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-attachment
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-sys-attachment R/C/U
- 依赖查询表: TBL-sys-attachment R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: Authenticated user with endpoint permission.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-attachment-attachments-att-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-plans

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-plans
- 业务目标: 完成 FUNC-lesson-lesson-plans 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0319, API-op-0320
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-plans
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-plans-stats

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-plans-stats
- 业务目标: 完成 FUNC-lesson-lesson-plans-stats 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0321
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-plans-stats
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-plans-plan-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-plans-plan-id
- 业务目标: 完成 FUNC-lesson-lesson-plans-plan-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0322, API-op-0323, API-op-0324
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-plans-plan-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-plans-plan-id-copy

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-plans-plan-id-copy
- 业务目标: 完成 FUNC-lesson-lesson-plans-plan-id-copy 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0325
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-plans-plan-id-copy
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-plans-plan-id-share

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-plans-plan-id-share
- 业务目标: 完成 FUNC-lesson-lesson-plans-plan-id-share 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0326
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-plans-plan-id-share
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-plans-batch

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-plans-batch
- 业务目标: 完成 FUNC-lesson-lesson-plans-batch 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0327
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-plans-batch
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-plans-plan-id-attachments

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-plans-plan-id-attachments
- 业务目标: 完成 FUNC-lesson-lesson-plans-plan-id-attachments 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0328, API-op-0329
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-plans-plan-id-attachments
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-plans-plan-id-attachments-att-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-plans-plan-id-attachments-att-id
- 业务目标: 完成 FUNC-lesson-lesson-plans-plan-id-attachments-att-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0330
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-file-storage

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-plans-plan-id-attachments-att-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-ai-generate

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-ai-generate
- 业务目标: 完成 FUNC-lesson-lesson-ai-generate 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0331
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-ai-generate
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-ai-jobs-job-id

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-ai-jobs-job-id
- 业务目标: 完成 FUNC-lesson-lesson-ai-jobs-job-id 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0332
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-ai-jobs-job-id
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-ai-jobs-job-id-cancel

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-ai-jobs-job-id-cancel
- 业务目标: 完成 FUNC-lesson-lesson-ai-jobs-job-id-cancel 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0333
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-ai-jobs-job-id-cancel
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-ai-jobs

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-ai-jobs
- 业务目标: 完成 FUNC-lesson-lesson-ai-jobs 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0334
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-ai-jobs
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-ai-jobs-job-id-save

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-ai-jobs-job-id-save
- 业务目标: 完成 FUNC-lesson-lesson-ai-jobs-job-id-save 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0335
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-ai-jobs-job-id-save
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-ai-jobs-job-id-export

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-ai-jobs-job-id-export
- 业务目标: 完成 FUNC-lesson-lesson-ai-jobs-job-id-export 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0336
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-ai-jobs-job-id-export
- 证据摘要: OpenAPI + source code path mapping


## FUNC-lesson-lesson-ai-options

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-lesson-lesson-ai-options
- 业务目标: 完成 FUNC-lesson-lesson-ai-options 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-teaching-content / SCN-teacher-prepare / CAP-knowledge-management
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0337
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: OBJ-agentjob, OBJ-lessonplan, OBJ-lessonstage
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-async-job, COMMON-rate-limit

### Physical Data Operations
- 核心 CUD 表: TBL-edu-lesson-plan R/C/U/D, TBL-edu-lesson-stage R/C/U/D, TBL-sys-agent-job R/C/U
- 依赖查询表: TBL-edu-lesson-plan R, TBL-edu-lesson-stage R, TBL-sys-agent-job R
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: teacher scope; sys_admin may override.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-lesson-lesson-ai-options
- 证据摘要: OpenAPI + source code path mapping


## FUNC-health-health

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-health-health
- 业务目标: 完成 FUNC-health-health 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0338
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: none
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: 待细化
- 依赖查询表: 待细化
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: public.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-health-health
- 证据摘要: OpenAPI + source code path mapping


## FUNC-ready-ready

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-ready-ready
- 业务目标: 完成 FUNC-ready-ready 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: interactive / menu
- 菜单/任务/事件/API入口: API-op-0339
- 页面/子页/业务操作或自动触发条件: 待细化

### Implementation Chain
1. entry -> page/action/trigger
2. frontend handler -> request wrapper
3. API -> controller
4. service -> domain rule
5. service -> DAO/ORM
6. service -> child API/common capability
7. persistence -> business result/state

### Object Roles
- 核心对象: none
- 模块内支撑对象: none
- 外部依赖对象及所有者/访问方式: none
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization

### Physical Data Operations
- 核心 CUD 表: 待细化
- 依赖查询表: 待细化
- 间接影响表: none
- 审计/日志表: none
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: public.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-ready-ready
- 证据摘要: OpenAPI + source code path mapping


## FUNC-jobs-clean-expired-exams

### Requirement Link
- 需求面板: ./business-function-requirements.md#func-jobs-clean-expired-exams
- 业务目标: 完成 FUNC-jobs-clean-expired-exams 相关业务动作
- 业务结果: 更新业务状态并保留审计/日志

### Identity And Entry
- 业务域/场景/能力: DOM-platform-ops / SCN-admin-manage / CAP-platform-administration
- 交互方式和触发类型: non-interactive / scheduled
- 菜单/任务/事件/API入口: JOB-clean-expired-exams。
- 页面/子页/业务操作或自动触发条件: 每天 03:00。

### Implementation Chain
1. APScheduler -> app.services.task_jobs.clean_expired_exams
2. frontend handler -> none
3. scheduler -> task_jobs.run_job
4. service -> 归档超期任务
5. service -> SQLAlchemy Session
6. service -> notification / execution log
7. persistence -> TBL-edu-task U, TBL-sys-job-execution-log C, TBL-sys-notification C

### Object Roles
- 核心对象: none
- 模块内支撑对象: ScheduledJob, JobExecutionLog
- 外部依赖对象及所有者/访问方式: notification service via backend
- DTO/VO/Command/Query/Event: none

### Technical And Common Dependencies
- TCAP: COMP-fastapi routing; COMP-sqlalchemy persistence
- CAPI: COMMON-authorization, COMMON-scheduler

### Physical Data Operations
- 核心 CUD 表: 待细化
- 依赖查询表: 待细化
- 间接影响表: none
- 审计/日志表: TBL-sys-job-execution-log
- 无持久化时: not applicable

### Rules And State
- 前置条件: Valid session or public endpoint; required business data exists.
- 业务规则: Follow domain default rules and API validation.
- 状态迁移: Update relevant business state per API semantics.
- 权限与数据范围: sys_admin or grade_admin as configured.

### Closure
- 状态: partial
- 断链位置和影响: 业务分支与字段级转换需继续深挖。
- 缺失源码/配置: none
- 下一步可执行检索: read controller/service code for FUNC-jobs-clean-expired-exams
- 证据摘要: OpenAPI + source code path mapping
