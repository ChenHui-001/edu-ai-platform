# 数据库字段设计

- Output Language: zh-CN
- Status: in-progress
- Table Count: 63

字段属性来自 SQLAlchemy 模型；索引/默认值/可空为事实，长度、含义、访问者为事实或待补。

## TBL-edu-answer - edu_answer

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| submission_id | submission_id | INTEGER | unknown | False | unknown | FK->id+IDX | submission_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| paper_item_id | paper_item_id | INTEGER | unknown | False | unknown | FK->id+IDX | paper_item_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| question_id | question_id | INTEGER | unknown | False | unknown | FK->id+IDX | question_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| content | content | TEXT | unknown | True | unknown | none | content | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_correct | is_correct | BOOLEAN | unknown | True | unknown | IDX | is_correct | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| score | score | FLOAT | unknown | True | unknown | none | score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| full_score | full_score | FLOAT | unknown | False | 0.0 | none | full_score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grader_type | grader_type | VARCHAR(16) | 16 | False | auto | none | grader_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ai_comment | ai_comment | TEXT | unknown | True | unknown | none | ai_comment | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ai_error_points | ai_error_points | TEXT | unknown | True | unknown | none | ai_error_points | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| teacher_comment | teacher_comment | TEXT | unknown | True | unknown | none | teacher_comment | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-class - edu_class

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(64) | 64 | False | unknown | IDX | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | False | unknown | FK->id+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| head_teacher_id | head_teacher_id | INTEGER | unknown | True | unknown | FK->id | head_teacher_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_active | is_active | BOOLEAN | unknown | False | True | none | is_active | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| remark | remark | VARCHAR(255) | 255 | True | unknown | none | remark | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90BF98A0> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-class-request - edu_class_request

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| teacher_id | teacher_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | teacher_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(64) | 64 | False | unknown | UQ | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | False | unknown | FK->id+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| description | description | VARCHAR(255) | 255 | True | unknown | none | description | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | pending | UQ+IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| review_by | review_by | INTEGER | unknown | True | unknown | FK->id | review_by | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| review_at | review_at | DATETIME | unknown | True | unknown | none | review_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| review_note | review_note | VARCHAR(255) | 255 | True | unknown | none | review_note | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| class_id | class_id | INTEGER | unknown | True | unknown | FK->id | class_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90C22520> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-exam-standard - edu_exam_standard

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(128) | 128 | False | unknown | none | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| region | region | VARCHAR(32) | 32 | False | hubei | UQ+IDX | region | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| stage | stage | VARCHAR(16) | 16 | False | junior | UQ+IDX | stage | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_name | subject_name | VARCHAR(32) | 32 | False | unknown | UQ+IDX | subject_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| exam_type | exam_type | VARCHAR(32) | 32 | False | final | UQ+IDX | exam_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| total_score | total_score | FLOAT | unknown | False | 100.0 | none | total_score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| duration | duration | INTEGER | unknown | False | 120 | none | duration | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| sections | sections | TEXT | unknown | True | unknown | none | sections | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| difficulty_ratio | difficulty_ratio | TEXT | unknown | True | unknown | none | difficulty_ratio | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| description | description | TEXT | unknown | True | unknown | none | description | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_active | is_active | BOOLEAN | unknown | False | True | IDX | is_active | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_default | is_default | BOOLEAN | unknown | False | False | none | is_default | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| source | source | VARCHAR(16) | 16 | False | seed | IDX | source | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| sort | sort | INTEGER | unknown | False | 0 | none | sort | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| owner_id | owner_id | INTEGER | unknown | True | unknown | FK->id+IDX | owner_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90DE5940> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90DE5B20> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-flow-definition - edu_flow_definition

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| code | code | VARCHAR(64) | 64 | False | unknown | UQ+IDX | code | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(128) | 128 | False | unknown | none | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| flow_type | flow_type | VARCHAR(20) | 20 | False | unknown | none | flow_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| trigger_type | trigger_type | VARCHAR(20) | 20 | False | MANUAL | none | trigger_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| trigger_behavior | trigger_behavior | VARCHAR(100) | 100 | True | unknown | none | trigger_behavior | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| definition | definition | TEXT | unknown | False | unknown | none | definition | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| version | version | INTEGER | unknown | False | 1 | none | version | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | INTEGER | unknown | False | 1 | none | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F4A520> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F4A5C0> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-flow-history - edu_flow_history

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| instance_id | instance_id | INTEGER | unknown | False | unknown | FK->id+IDX | instance_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| activity_id | activity_id | VARCHAR(64) | 64 | True | unknown | none | activity_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| activity_name | activity_name | VARCHAR(128) | 128 | True | unknown | none | activity_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| operator_id | operator_id | INTEGER | unknown | True | unknown | FK->id | operator_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| operator_name | operator_name | VARCHAR(64) | 64 | True | unknown | none | operator_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| action | action | VARCHAR(20) | 20 | False | unknown | none | action | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| comment | comment | TEXT | unknown | True | unknown | none | comment | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| from_activity | from_activity | VARCHAR(64) | 64 | True | unknown | none | from_activity | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| to_activity | to_activity | VARCHAR(64) | 64 | True | unknown | none | to_activity | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F83F60> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-flow-instance - edu_flow_instance

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| def_id | def_id | INTEGER | unknown | False | unknown | FK->id+IDX | def_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| biz_type | biz_type | VARCHAR(32) | 32 | False | unknown | IDX | biz_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| biz_id | biz_id | INTEGER | unknown | False | unknown | IDX | biz_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| biz_key | biz_key | VARCHAR(128) | 128 | True | unknown | none | biz_key | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| current_activity_ids | current_activity_ids | TEXT | unknown | False | [] | none | current_activity_ids | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| variables | variables | TEXT | unknown | False | {} | none | variables | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(20) | 20 | False | RUNNING | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| creator_id | creator_id | INTEGER | unknown | True | unknown | FK->id+IDX | creator_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| started_at | started_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F4B6A0> | none | started_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ended_at | ended_at | DATETIME | unknown | True | unknown | none | ended_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F4B9C0> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-flow-task - edu_flow_task

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| instance_id | instance_id | INTEGER | unknown | False | unknown | FK->id+IDX | instance_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| activity_id | activity_id | VARCHAR(64) | 64 | False | unknown | none | activity_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| activity_type | activity_type | VARCHAR(20) | 20 | False | unknown | none | activity_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| activity_name | activity_name | VARCHAR(128) | 128 | False |  | none | activity_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| role_code | role_code | VARCHAR(32) | 32 | False | unknown | IDX | role_code | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| assignee_id | assignee_id | INTEGER | unknown | True | unknown | FK->id+IDX | assignee_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(20) | 20 | False | TODO | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| action | action | VARCHAR(20) | 20 | True | unknown | none | action | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| comment | comment | TEXT | unknown | True | unknown | none | comment | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F80E00> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| claimed_at | claimed_at | DATETIME | unknown | True | unknown | none | claimed_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| done_at | done_at | DATETIME | unknown | True | unknown | none | done_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| deadline | deadline | DATETIME | unknown | True | unknown | IDX | deadline | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| urge_count | urge_count | INTEGER | unknown | False | 0 | none | urge_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| last_urged_at | last_urged_at | DATETIME | unknown | True | unknown | none | last_urged_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| transfer_count | transfer_count | INTEGER | unknown | False | 0 | none | transfer_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| last_transferred_at | last_transferred_at | DATETIME | unknown | True | unknown | none | last_transferred_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-flow-transfer - edu_flow_transfer

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| task_id | task_id | INTEGER | unknown | False | unknown | FK->id+IDX | task_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| from_user_id | from_user_id | INTEGER | unknown | True | unknown | FK->id | from_user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| to_user_id | to_user_id | INTEGER | unknown | False | unknown | FK->id | to_user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| operator_id | operator_id | INTEGER | unknown | True | unknown | FK->id | operator_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| reason | reason | TEXT | unknown | True | unknown | none | reason | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F82980> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-grade - edu_grade

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(32) | 32 | False | unknown | IDX | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| stage | stage | VARCHAR(16) | 16 | False | primary | none | stage | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_num | grade_num | INTEGER | unknown | False | 1 | none | grade_num | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_active | is_active | BOOLEAN | unknown | False | True | none | is_active | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| sort | sort | INTEGER | unknown | False | 0 | none | sort | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-knowledge-mastery - edu_knowledge_mastery

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| student_id | student_id | INTEGER | unknown | False | unknown | FK->id+IDX | student_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| knowledge_point_id | knowledge_point_id | INTEGER | unknown | False | unknown | FK->id+IDX | knowledge_point_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | False | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| total_count | total_count | INTEGER | unknown | False | 0 | none | total_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| correct_count | correct_count | INTEGER | unknown | False | 0 | none | correct_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| mastery | mastery | FLOAT | unknown | False | 0.0 | none | mastery | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| wrong_count | wrong_count | INTEGER | unknown | False | 0 | none | wrong_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| study_seconds | study_seconds | INTEGER | unknown | False | 0 | none | study_seconds | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| last_practice_at | last_practice_at | DATETIME | unknown | True | unknown | none | last_practice_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90C51EE0> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-knowledge-point - edu_knowledge_point

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(128) | 128 | False | unknown | IDX | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| level | level | INTEGER | unknown | False | 1 | none | level | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| parent_id | parent_id | INTEGER | unknown | True | unknown | IDX | parent_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| path | path | VARCHAR(255) | 255 | True | unknown | none | path | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| term | term | INTEGER | unknown | False | 1 | none | term | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| code | code | VARCHAR(64) | 64 | True | unknown | UQ+IDX | code | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| description | description | TEXT | unknown | True | unknown | none | description | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| difficulty | difficulty | VARCHAR(16) | 16 | False | medium | none | difficulty | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| keywords | keywords | VARCHAR(255) | 255 | True | unknown | none | keywords | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| sort | sort | INTEGER | unknown | False | 0 | none | sort | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_active | is_active | BOOLEAN | unknown | False | True | none | is_active | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| textbook_version | textbook_version | VARCHAR(64) | 64 | True | unknown | none | textbook_version | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | published | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| source | source | VARCHAR(16) | 16 | False | manual | none | source | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| owner_id | owner_id | INTEGER | unknown | True | unknown | FK->id+IDX | owner_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| external_source | external_source | VARCHAR(64) | 64 | True | unknown | UQ | external_source | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| external_id | external_id | VARCHAR(64) | 64 | True | unknown | UQ | external_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-knowledge-prerequisite - edu_knowledge_prerequisite

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| topic_kp_id | topic_kp_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | topic_kp_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| prerequisite_kp_id | prerequisite_kp_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | prerequisite_kp_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| strength | strength | VARCHAR(8) | 8 | False | hard | none | strength | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| reason | reason | TEXT | unknown | True | unknown | none | reason | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| source | source | VARCHAR(32) | 32 | False | manual | none | source | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90EF7CE0> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-lesson-plan - edu_lesson_plan

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| title | title | VARCHAR(128) | 128 | False | unknown | IDX | title | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| topic | topic | VARCHAR(128) | 128 | False | unknown | none | topic | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | False | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | False | unknown | FK->id+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| textbook_version | textbook_version | VARCHAR(64) | 64 | True | unknown | none | textbook_version | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| knowledge_point_id | knowledge_point_id | INTEGER | unknown | True | unknown | FK->id+IDX | knowledge_point_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| duration_minutes | duration_minutes | INTEGER | unknown | False | 45 | none | duration_minutes | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| period | period | VARCHAR(32) | 32 | True | unknown | none | period | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| objectives | objectives | TEXT | unknown | False |  | none | objectives | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| key_points | key_points | TEXT | unknown | False |  | none | key_points | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| difficulties | difficulties | TEXT | unknown | False |  | none | difficulties | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| teaching_preparation | teaching_preparation | TEXT | unknown | True | unknown | none | teaching_preparation | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| class_exercise | class_exercise | TEXT | unknown | True | unknown | none | class_exercise | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| board_design | board_design | TEXT | unknown | True | unknown | none | board_design | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| homework | homework | TEXT | unknown | True | unknown | none | homework | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| reflection | reflection | TEXT | unknown | True | unknown | none | reflection | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| creator_id | creator_id | INTEGER | unknown | False | unknown | FK->id+IDX | creator_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| use_count | use_count | INTEGER | unknown | False | 0 | none | use_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_shared | is_shared | INTEGER | unknown | False | 0 | none | is_shared | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ai_generated | ai_generated | INTEGER | unknown | False | 0 | none | ai_generated | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ai_job_id | ai_job_id | INTEGER | unknown | True | unknown | none | ai_job_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90CB6660> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90CB6CA0> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-lesson-stage - edu_lesson_stage

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| lesson_id | lesson_id | INTEGER | unknown | False | unknown | FK->id+IDX | lesson_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(32) | 32 | False | unknown | none | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| duration_minutes | duration_minutes | INTEGER | unknown | False | 5 | none | duration_minutes | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| content | content | TEXT | unknown | False |  | none | content | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| teacher_activity | teacher_activity | TEXT | unknown | True | unknown | none | teacher_activity | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| student_activity | student_activity | TEXT | unknown | True | unknown | none | student_activity | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| sort_order | sort_order | INTEGER | unknown | False | 0 | IDX | sort_order | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-note - edu_note

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| title | title | VARCHAR(128) | 128 | False | unknown | IDX | title | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| content | content | TEXT | unknown | False | unknown | none | content | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| format | format | VARCHAR(16) | 16 | False | markdown | none | format | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| student_id | student_id | INTEGER | unknown | False | unknown | FK->id+IDX | student_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | True | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| knowledge_point_id | knowledge_point_id | INTEGER | unknown | True | unknown | FK->id+IDX | knowledge_point_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| tags | tags | VARCHAR(255) | 255 | True | unknown | none | tags | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ai_summary | ai_summary | TEXT | unknown | True | unknown | none | ai_summary | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ai_outline | ai_outline | TEXT | unknown | True | unknown | none | ai_outline | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ai_mindmap | ai_mindmap | TEXT | unknown | True | unknown | none | ai_mindmap | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_favorite | is_favorite | BOOLEAN | unknown | False | False | IDX | is_favorite | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| view_count | view_count | INTEGER | unknown | False | 0 | none | view_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_shared | is_shared | BOOLEAN | unknown | False | False | none | is_shared | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90C50540> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90C50680> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-paper - edu_paper

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(128) | 128 | False | unknown | IDX | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | False | unknown | FK->id+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | False | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| total_score | total_score | FLOAT | unknown | False | 100.0 | none | total_score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| duration | duration | INTEGER | unknown | False | 60 | none | duration | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| difficulty_ratio | difficulty_ratio | TEXT | unknown | True | unknown | none | difficulty_ratio | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| knowledge_coverage | knowledge_coverage | TEXT | unknown | True | unknown | none | knowledge_coverage | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| difficulty_report | difficulty_report | TEXT | unknown | True | unknown | none | difficulty_report | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| creator_id | creator_id | INTEGER | unknown | False | unknown | FK->id+IDX | creator_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| source | source | VARCHAR(16) | 16 | False | manual | none | source | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_shared | is_shared | BOOLEAN | unknown | False | False | none | is_shared | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| use_count | use_count | INTEGER | unknown | False | 0 | none | use_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| description | description | TEXT | unknown | True | unknown | none | description | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| exam_type | exam_type | VARCHAR(32) | 32 | True | unknown | IDX | exam_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| stage | stage | VARCHAR(16) | 16 | True | unknown | IDX | stage | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| textbook_version | textbook_version | VARCHAR(64) | 64 | True | unknown | none | textbook_version | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | published | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| standard_id | standard_id | INTEGER | unknown | True | unknown | IDX | standard_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| share_scope | share_scope | VARCHAR(16) | 16 | False | private | IDX | share_scope | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| review_comment | review_comment | TEXT | unknown | True | unknown | none | review_comment | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| review_by | review_by | INTEGER | unknown | True | unknown | FK->id | review_by | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| review_at | review_at | DATETIME | unknown | True | unknown | none | review_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| current_version | current_version | INTEGER | unknown | False | 1 | none | current_version | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| generation_params | generation_params | TEXT | unknown | True | unknown | none | generation_params | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| type_report | type_report | TEXT | unknown | True | unknown | none | type_report | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90DBC5E0> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90DBC7C0> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-paper-favorite - edu_paper_favorite

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| paper_id | paper_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | paper_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90E24900> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-paper-item - edu_paper_item

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| paper_id | paper_id | INTEGER | unknown | False | unknown | FK->id+IDX | paper_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| question_id | question_id | INTEGER | unknown | False | unknown | FK->id+IDX | question_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| sort_order | sort_order | INTEGER | unknown | False | 0 | none | sort_order | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| score | score | FLOAT | unknown | False | 5.0 | none | score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| section_name | section_name | VARCHAR(64) | 64 | True | unknown | none | section_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| section_code | section_code | VARCHAR(32) | 32 | True | unknown | IDX | section_code | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| section_sort | section_sort | INTEGER | unknown | False | 0 | none | section_sort | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| score_override | score_override | BOOLEAN | unknown | False | False | none | score_override | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-paper-share - edu_paper_share

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| paper_id | paper_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | paper_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| from_user_id | from_user_id | INTEGER | unknown | False | unknown | FK->id+IDX | from_user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| to_user_id | to_user_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | to_user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| permission | permission | VARCHAR(16) | 16 | False | view | none | permission | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| scope | scope | VARCHAR(16) | 16 | True | unknown | none | scope | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90DE42C0> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-paper-version - edu_paper_version

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| paper_id | paper_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | paper_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| version | version | INTEGER | unknown | False | 1 | UQ | version | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| snapshot | snapshot | TEXT | unknown | False | unknown | none | snapshot | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| change_note | change_note | VARCHAR(255) | 255 | True | unknown | none | change_note | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| item_count | item_count | INTEGER | unknown | False | 0 | none | item_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| total_score | total_score | FLOAT | unknown | False | 0.0 | none | total_score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_by | created_by | INTEGER | unknown | True | unknown | FK->id+IDX | created_by | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90DE74C0> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-question - edu_question

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| type | type | VARCHAR(16) | 16 | False | single | IDX | type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| stem | stem | TEXT | unknown | False | unknown | none | stem | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| options | options | TEXT | unknown | True | unknown | none | options | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| answer | answer | TEXT | unknown | True | unknown | none | answer | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| analysis | analysis | TEXT | unknown | True | unknown | none | analysis | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| score | score | FLOAT | unknown | False | 5.0 | none | score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| answer_min_words | answer_min_words | INTEGER | unknown | True | unknown | none | answer_min_words | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| difficulty | difficulty | VARCHAR(16) | 16 | False | medium | IDX | difficulty | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | False | unknown | FK->id+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | False | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| knowledge_point_id | knowledge_point_id | INTEGER | unknown | True | unknown | FK->id+IDX | knowledge_point_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| bank_type | bank_type | VARCHAR(16) | 16 | False | private | IDX | bank_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| owner_id | owner_id | INTEGER | unknown | False | unknown | FK->id+IDX | owner_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | published | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| fingerprint | fingerprint | VARCHAR(64) | 64 | True | unknown | IDX | fingerprint | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| source | source | VARCHAR(32) | 32 | False | manual | none | source | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| usage_count | usage_count | INTEGER | unknown | False | 0 | none | usage_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| external_source | external_source | VARCHAR(64) | 64 | True | unknown | UQ | external_source | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| external_id | external_id | VARCHAR(80) | 80 | True | unknown | UQ | external_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| extra_json | extra_json | TEXT | unknown | True | unknown | none | extra_json | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D90AE0> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D91080> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-question-favorite - edu_question_favorite

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | FK->id+IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| question_id | question_id | INTEGER | unknown | False | unknown | FK->id+IDX | question_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| tag | tag | VARCHAR(32) | 32 | True | unknown | IDX | tag | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| note | note | VARCHAR(255) | 255 | True | unknown | none | note | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90C8A520> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-question-knowledge - edu_question_knowledge

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| question_id | question_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | question_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| knowledge_point_id | knowledge_point_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | knowledge_point_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-remediation-plan - edu_remediation_plan

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| student_id | student_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | student_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| diagnosis_id | diagnosis_id | INTEGER | unknown | False | unknown | FK->id+UQ | diagnosis_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| title | title | VARCHAR(128) | 128 | False | unknown | none | title | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| payload | payload | TEXT | unknown | False | unknown | none | payload | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| version | version | INTEGER | unknown | False | 1 | none | version | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F1EA20> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F1ED40> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-review-plan - edu_review_plan

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| student_id | student_id | INTEGER | unknown | False | unknown | FK->id+IDX | student_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| wrong_question_id | wrong_question_id | INTEGER | unknown | True | unknown | FK->id+IDX | wrong_question_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| knowledge_point_id | knowledge_point_id | INTEGER | unknown | False | unknown | FK->id+IDX | knowledge_point_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | False | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| stage | stage | INTEGER | unknown | False | 1 | none | stage | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| scheduled_date | scheduled_date | VARCHAR(10) | 10 | False | unknown | IDX | scheduled_date | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_completed | is_completed | BOOLEAN | unknown | False | False | IDX | is_completed | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| completed_at | completed_at | DATETIME | unknown | True | unknown | none | completed_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| correct_rate | correct_rate | FLOAT | unknown | True | unknown | none | correct_rate | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90C53CE0> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-study-checkin - edu_study_checkin

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | FK->id+IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| goal_id | goal_id | INTEGER | unknown | True | unknown | FK->id+IDX | goal_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| checkin_date | checkin_date | VARCHAR(10) | 10 | False | unknown | IDX | checkin_date | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| actual_value | actual_value | INTEGER | unknown | False | 0 | none | actual_value | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| streak | streak | INTEGER | unknown | False | 1 | none | streak | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| note | note | VARCHAR(255) | 255 | True | unknown | none | note | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90CB5120> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-study-goal - edu_study_goal

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | FK->id+IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| title | title | VARCHAR(128) | 128 | False | unknown | none | title | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| target_type | target_type | VARCHAR(32) | 32 | False | daily | none | target_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| target_value | target_value | INTEGER | unknown | False | 10 | none | target_value | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| unit | unit | VARCHAR(16) | 16 | False | questions | none | unit | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | True | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| start_date | start_date | VARCHAR(10) | 10 | False |  | none | start_date | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| end_date | end_date | VARCHAR(10) | 10 | True | unknown | none | end_date | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_active | is_active | BOOLEAN | unknown | False | True | none | is_active | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90C8BB00> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90C8BC40> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-study-record - edu_study_record

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| student_id | student_id | INTEGER | unknown | False | unknown | FK->id+IDX | student_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | True | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| study_date | study_date | VARCHAR(10) | 10 | False | unknown | IDX | study_date | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| study_seconds | study_seconds | INTEGER | unknown | False | 0 | none | study_seconds | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| question_count | question_count | INTEGER | unknown | False | 0 | none | question_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| correct_count | correct_count | INTEGER | unknown | False | 0 | none | correct_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| note_count | note_count | INTEGER | unknown | False | 0 | none | note_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90C891C0> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-subject - edu_subject

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(32) | 32 | False | unknown | UQ+IDX | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| code | code | VARCHAR(32) | 32 | True | unknown | none | code | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| textbook_version | textbook_version | VARCHAR(64) | 64 | True | unknown | none | textbook_version | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_active | is_active | BOOLEAN | unknown | False | True | none | is_active | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| sort | sort | INTEGER | unknown | False | 0 | none | sort | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-submission - edu_submission

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| task_id | task_id | INTEGER | unknown | False | unknown | FK->id+IDX | task_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| student_id | student_id | INTEGER | unknown | False | unknown | FK->id+IDX | student_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| attempt | attempt | INTEGER | unknown | False | 1 | none | attempt | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | not_graded | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| score | score | FLOAT | unknown | True | unknown | none | score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| objective_score | objective_score | FLOAT | unknown | True | unknown | none | objective_score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subjective_score | subjective_score | FLOAT | unknown | True | unknown | none | subjective_score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| duration_seconds | duration_seconds | INTEGER | unknown | True | unknown | none | duration_seconds | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_passed | is_passed | BOOLEAN | unknown | True | unknown | none | is_passed | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| class_rank | class_rank | INTEGER | unknown | True | unknown | IDX | class_rank | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| comment | comment | TEXT | unknown | True | unknown | none | comment | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| switch_count | switch_count | INTEGER | unknown | False | 0 | none | switch_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| submit_count | submit_count | INTEGER | unknown | False | 0 | none | submit_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| submit_time | submit_time | DATETIME | unknown | True | unknown | none | submit_time | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_time | grade_time | DATETIME | unknown | True | unknown | none | grade_time | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90ED2480> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-task - edu_task

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| title | title | VARCHAR(128) | 128 | False | unknown | IDX | title | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| type | type | VARCHAR(16) | 16 | False | homework | IDX | type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| paper_id | paper_id | INTEGER | unknown | False | unknown | FK->id+IDX | paper_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | False | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | False | unknown | FK->id+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| creator_id | creator_id | INTEGER | unknown | False | unknown | FK->id+IDX | creator_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | draft | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| start_at | start_at | DATETIME | unknown | True | unknown | none | start_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| end_at | end_at | DATETIME | unknown | True | unknown | IDX | end_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| duration | duration | INTEGER | unknown | False | 60 | none | duration | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| publish_at | publish_at | DATETIME | unknown | True | unknown | none | publish_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| allow_retake | allow_retake | INTEGER | unknown | False | 1 | none | allow_retake | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| show_answer | show_answer | BOOLEAN | unknown | False | True | none | show_answer | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| anti_cheat | anti_cheat | BOOLEAN | unknown | False | False | none | anti_cheat | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| total_score | total_score | FLOAT | unknown | False | 100.0 | none | total_score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| pass_score | pass_score | FLOAT | unknown | False | 60.0 | none | pass_score | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| description | description | TEXT | unknown | True | unknown | none | description | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90EA2E80> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90EA2F20> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-task-assignment - edu_task_assignment

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| task_id | task_id | INTEGER | unknown | False | unknown | FK->id+IDX | task_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| class_id | class_id | INTEGER | unknown | True | unknown | FK->id+IDX | class_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| student_id | student_id | INTEGER | unknown | True | unknown | FK->id+IDX | student_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| group_name | group_name | VARCHAR(64) | 64 | True | unknown | none | group_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| notified | notified | BOOLEAN | unknown | False | False | none | notified | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-taxonomy-diagnosis-session - edu_taxonomy_diagnosis_session

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | FK->id+IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | False | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | True | unknown | FK->id+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| targets_json | targets_json | TEXT | unknown | False | unknown | none | targets_json | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| mode | mode | VARCHAR(16) | 16 | False | target | none | mode | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| question_limit | question_limit | INTEGER | unknown | False | 16 | none | question_limit | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| confirm_count | confirm_count | INTEGER | unknown | False | 3 | none | confirm_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| answers_json | answers_json | TEXT | unknown | False | [] | none | answers_json | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status_json | status_json | TEXT | unknown | False | {} | none | status_json | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| seed | seed | VARCHAR(64) | 64 | False | default | none | seed | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F1CFE0> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F1D440> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| finished_at | finished_at | DATETIME | unknown | True | unknown | none | finished_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-taxonomy-sync-run - edu_taxonomy_sync_run

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | FK->id+IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| action | action | VARCHAR(16) | 16 | False | unknown | none | action | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| source_commit | source_commit | VARCHAR(40) | 40 | False | unknown | none | source_commit | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | preview | none | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| report | report | TEXT | unknown | False | unknown | none | report | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| bundle_path | bundle_path | TEXT | unknown | True | unknown | none | bundle_path | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| backup_path | backup_path | TEXT | unknown | True | unknown | none | backup_path | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F494E0> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-teaching-assignment - edu_teaching_assignment

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| teacher_id | teacher_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | teacher_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| class_id | class_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | class_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | False | unknown | FK->id+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| school_year | school_year | VARCHAR(16) | 16 | False | 2026-2027 | none | school_year | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_active | is_active | BOOLEAN | unknown | False | True | none | is_active | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90C21260> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-tutor-feedback - edu_tutor_feedback

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | FK->id+IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| class_id | class_id | INTEGER | unknown | True | unknown | FK->id+IDX | class_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| question_id | question_id | INTEGER | unknown | False | unknown | FK->id | question_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| stage | stage | VARCHAR(16) | 16 | False | unknown | none | stage | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| content | content | TEXT | unknown | False | unknown | none | content | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| correction | correction | TEXT | unknown | True | unknown | none | correction | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| reviewer_id | reviewer_id | INTEGER | unknown | True | unknown | FK->id | reviewer_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | pending | none | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90F1FD80> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-edu-wrong-question - edu_wrong_question

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| student_id | student_id | INTEGER | unknown | False | unknown | FK->id+IDX | student_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| question_id | question_id | INTEGER | unknown | False | unknown | FK->id+IDX | question_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| subject_id | subject_id | INTEGER | unknown | False | unknown | FK->id+IDX | subject_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| knowledge_point_id | knowledge_point_id | INTEGER | unknown | True | unknown | FK->id+IDX | knowledge_point_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| wrong_answer | wrong_answer | TEXT | unknown | True | unknown | none | wrong_answer | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| error_count | error_count | INTEGER | unknown | False | 1 | none | error_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| error_reason | error_reason | VARCHAR(64) | 64 | True | unknown | IDX | error_reason | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ai_reason | ai_reason | TEXT | unknown | True | unknown | none | ai_reason | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| source_type | source_type | VARCHAR(16) | 16 | False | practice | none | source_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| source_id | source_id | INTEGER | unknown | True | unknown | none | source_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| source_name | source_name | VARCHAR(128) | 128 | True | unknown | none | source_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_mastered | is_mastered | BOOLEAN | unknown | False | False | IDX | is_mastered | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| mastered_at | mastered_at | DATETIME | unknown | True | unknown | none | mastered_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| last_wrong_at | last_wrong_at | DATETIME | unknown | False | <function now_local at 0x000001ED90EF6200> | IDX | last_wrong_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90EF62A0> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-agent-call-log - sys_agent_call_log

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| agent_name | agent_name | VARCHAR(64) | 64 | False | unknown | IDX | agent_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | True | unknown | IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| input_text | input_text | TEXT | unknown | True | unknown | none | input_text | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| output_text | output_text | TEXT | unknown | True | unknown | none | output_text | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| input_tokens | input_tokens | INTEGER | unknown | False | 0 | none | input_tokens | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| output_tokens | output_tokens | INTEGER | unknown | False | 0 | none | output_tokens | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| duration_ms | duration_ms | INTEGER | unknown | True | unknown | none | duration_ms | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | success | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| error_msg | error_msg | TEXT | unknown | True | unknown | none | error_msg | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_fallback | is_fallback | BOOLEAN | unknown | False | False | none | is_fallback | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| biz_type | biz_type | VARCHAR(32) | 32 | True | unknown | IDX | biz_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| biz_id | biz_id | INTEGER | unknown | True | unknown | none | biz_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D3B7E0> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-agent-job - sys_agent_job

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| agent | agent | VARCHAR(32) | 32 | False | unknown | IDX | agent | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | pending | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| progress | progress | INTEGER | unknown | False | 0 | none | progress | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| stage | stage | VARCHAR(64) | 64 | True | unknown | none | stage | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| params | params | TEXT | unknown | True | unknown | none | params | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| result | result | TEXT | unknown | True | unknown | none | result | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| error | error | TEXT | unknown | True | unknown | none | error | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| cancel_requested | cancel_requested | INTEGER | unknown | False | 0 | none | cancel_requested | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D66FC0> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| started_at | started_at | DATETIME | unknown | True | unknown | none | started_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| finished_at | finished_at | DATETIME | unknown | True | unknown | none | finished_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-agent-rate - sys_agent_rate

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| user_id | user_id | INTEGER | unknown | False | unknown | PK | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| window_minute | window_minute | INTEGER | unknown | False | unknown | PK | window_minute | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| count | count | INTEGER | unknown | False | 0 | none | count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D663E0> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-attachment - sys_attachment

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| filename | filename | VARCHAR(255) | 255 | False | unknown | none | filename | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| stored_name | stored_name | VARCHAR(255) | 255 | False | unknown | IDX | stored_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| file_path | file_path | VARCHAR(512) | 512 | False | unknown | none | file_path | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| file_size | file_size | INTEGER | unknown | False | 0 | none | file_size | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| file_type | file_type | VARCHAR(64) | 64 | True | unknown | none | file_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| category | category | VARCHAR(64) | 64 | True | unknown | IDX | category | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| biz_type | biz_type | VARCHAR(32) | 32 | True | unknown | IDX | biz_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| biz_id | biz_id | INTEGER | unknown | True | unknown | IDX | biz_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| uploader_id | uploader_id | INTEGER | unknown | True | unknown | FK->id | uploader_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| download_count | download_count | INTEGER | unknown | False | 0 | none | download_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_temp | is_temp | BOOLEAN | unknown | False | True | IDX | is_temp | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| visible_to_student | visible_to_student | BOOLEAN | unknown | False | True | IDX | visible_to_student | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D3A0C0> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-captcha - sys_captcha

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| key | key | VARCHAR(32) | 32 | False | unknown | PK | key | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| text | text | VARCHAR(8) | 8 | False | unknown | none | text | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| expire_at | expire_at | DATETIME | unknown | False | unknown | IDX | expire_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90E25A80> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-config - sys_config

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| key | key | VARCHAR(64) | 64 | False | unknown | IDX | key | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| value | value | TEXT | unknown | True | unknown | none | value | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| value_type | value_type | VARCHAR(16) | 16 | False | string | none | value_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| category | category | VARCHAR(32) | 32 | False | basic | IDX | category | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| label | label | VARCHAR(64) | 64 | True | unknown | none | label | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| description | description | VARCHAR(255) | 255 | True | unknown | none | description | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_public | is_public | BOOLEAN | unknown | False | False | none | is_public | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_by | updated_by | INTEGER | unknown | True | unknown | FK->id | updated_by | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90EA13A0> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90EA1620> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-error-log - sys_error_log

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| level | level | VARCHAR(16) | 16 | False | ERROR | IDX | level | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| module | module | VARCHAR(64) | 64 | True | unknown | IDX | module | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| path | path | VARCHAR(255) | 255 | True | unknown | none | path | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| message | message | TEXT | unknown | False | unknown | none | message | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| traceback | traceback | TEXT | unknown | True | unknown | none | traceback | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | True | unknown | none | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D10C20> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-job-execution-log - sys_job_execution_log

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| job_id | job_id | INTEGER | unknown | False | unknown | FK->id+IDX | job_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| job_name | job_name | VARCHAR(128) | 128 | False | unknown | IDX | job_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | running | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| started_at | started_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D131A0> | IDX | started_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| finished_at | finished_at | DATETIME | unknown | True | unknown | none | finished_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| duration_ms | duration_ms | INTEGER | unknown | True | unknown | none | duration_ms | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| message | message | TEXT | unknown | True | unknown | none | message | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| trigger_type | trigger_type | VARCHAR(16) | 16 | False | auto | none | trigger_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-job-lock - sys_job_lock

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| job_id | job_id | INTEGER | unknown | False | unknown | PK | job_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| owner | owner | VARCHAR(80) | 80 | False | unknown | none | owner | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| acquired_at | acquired_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D38400> | none | acquired_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| expire_at | expire_at | DATETIME | unknown | False | unknown | IDX | expire_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-llm-breaker - sys_llm_breaker

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| kind | kind | VARCHAR(16) | 16 | False |  | none | kind | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| reason | reason | TEXT | unknown | False |  | none | reason | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| streak | streak | INTEGER | unknown | False | 0 | none | streak | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| expire_at | expire_at | DATETIME | unknown | True | unknown | none | expire_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D38720> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-login-log - sys_login_log

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | True | unknown | IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| username | username | VARCHAR(64) | 64 | False | unknown | IDX | username | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| login_type | login_type | VARCHAR(16) | 16 | False | password | none | login_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | success | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| message | message | VARCHAR(255) | 255 | True | unknown | none | message | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ip | ip | VARCHAR(64) | 64 | True | unknown | IDX | ip | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| location | location | VARCHAR(64) | 64 | True | unknown | none | location | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| device | device | VARCHAR(128) | 128 | True | unknown | none | device | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| os | os | VARCHAR(64) | 64 | True | unknown | none | os | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_abnormal | is_abnormal | BOOLEAN | unknown | False | False | IDX | is_abnormal | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| login_at | login_at | DATETIME | unknown | False | <function now_local at 0x000001ED90CE6520> | IDX | login_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-notification - sys_notification

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | FK->id+IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| title | title | VARCHAR(128) | 128 | False | unknown | none | title | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| content | content | TEXT | unknown | True | unknown | none | content | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| type | type | VARCHAR(32) | 32 | False | system | none | type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| biz_type | biz_type | VARCHAR(32) | 32 | True | unknown | none | biz_type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| biz_id | biz_id | INTEGER | unknown | True | unknown | none | biz_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_read | is_read | BOOLEAN | unknown | False | False | IDX | is_read | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D64EA0> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-notify-pref - sys_notify_pref

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| user_id | user_id | INTEGER | unknown | False | unknown | PK+FK->id | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| prefs | prefs | TEXT | unknown | True | unknown | none | prefs | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D65EE0> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-operation-log - sys_operation_log

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | True | unknown | IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| username | username | VARCHAR(64) | 64 | True | unknown | none | username | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| module | module | VARCHAR(64) | 64 | False | unknown | IDX | module | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| action | action | VARCHAR(128) | 128 | False | unknown | IDX | action | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| method | method | VARCHAR(8) | 8 | True | unknown | none | method | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| path | path | VARCHAR(255) | 255 | True | unknown | none | path | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| ip | ip | VARCHAR(64) | 64 | True | unknown | none | ip | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| params | params | TEXT | unknown | True | unknown | none | params | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| result | result | TEXT | unknown | True | unknown | none | result | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | success | none | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| error_msg | error_msg | TEXT | unknown | True | unknown | none | error_msg | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| duration_ms | duration_ms | INTEGER | unknown | True | unknown | none | duration_ms | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90CE7880> | IDX | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-permission - sys_permission

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| code | code | VARCHAR(128) | 128 | False | unknown | IDX | code | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(64) | 64 | False | unknown | none | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| type | type | VARCHAR(16) | 16 | False | button | none | type | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| parent_id | parent_id | INTEGER | unknown | True | unknown | IDX | parent_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| path | path | VARCHAR(255) | 255 | True | unknown | none | path | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| icon | icon | VARCHAR(64) | 64 | True | unknown | none | icon | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| sort | sort | INTEGER | unknown | False | 0 | none | sort | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_hidden | is_hidden | BOOLEAN | unknown | False | False | none | is_hidden | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-rate-limit - sys_rate_limit

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| key | key | VARCHAR(160) | 160 | False | unknown | PK | key | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| window_start | window_start | FLOAT | unknown | False | unknown | none | window_start | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| hits | hits | INTEGER | unknown | False | 0 | none | hits | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| expire_at | expire_at | DATETIME | unknown | False | unknown | IDX | expire_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90E274C0> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-registration - sys_registration

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | FK->id+IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| identity | identity | VARCHAR(32) | 32 | False | unknown | none | identity | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| attachments | attachments | TEXT | unknown | True | unknown | none | attachments | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| reason | reason | TEXT | unknown | True | unknown | none | reason | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | pending | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| audit_user_id | audit_user_id | INTEGER | unknown | True | unknown | FK->id | audit_user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| audit_at | audit_at | DATETIME | unknown | True | unknown | none | audit_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| audit_reason | audit_reason | VARCHAR(255) | 255 | True | unknown | none | audit_reason | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90E83420> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-reset-code - sys_reset_code

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| target | target | VARCHAR(128) | 128 | False | unknown | PK | target | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| code | code | VARCHAR(8) | 8 | False | unknown | none | code | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| expire_at | expire_at | DATETIME | unknown | False | unknown | IDX | expire_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90E40040> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-revoked-token - sys_revoked_token

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| jti | jti | VARCHAR(32) | 32 | False | unknown | PK | jti | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| expire_at | expire_at | DATETIME | unknown | False | unknown | IDX | expire_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90E25DA0> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-role - sys_role

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| code | code | VARCHAR(64) | 64 | False | unknown | IDX | code | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(64) | 64 | False | unknown | none | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| description | description | VARCHAR(255) | 255 | True | unknown | none | description | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| data_scope | data_scope | VARCHAR(32) | 32 | False | self | none | data_scope | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_builtin | is_builtin | BOOLEAN | unknown | False | False | none | is_builtin | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_active | is_active | BOOLEAN | unknown | False | True | none | is_active | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| sort | sort | INTEGER | unknown | False | 0 | none | sort | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90E43E20> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-role-permission - sys_role_permission

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| role_id | role_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | role_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| permission_id | permission_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | permission_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-scheduled-job - sys_scheduled_job

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| name | name | VARCHAR(128) | 128 | False | unknown | IDX | name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| description | description | VARCHAR(255) | 255 | True | unknown | none | description | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| func_path | func_path | VARCHAR(255) | 255 | False | unknown | none | func_path | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| cron_expression | cron_expression | VARCHAR(64) | 64 | False | unknown | none | cron_expression | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_builtin | is_builtin | BOOLEAN | unknown | False | False | none | is_builtin | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| is_active | is_active | BOOLEAN | unknown | False | True | IDX | is_active | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| retry_times | retry_times | INTEGER | unknown | False | 2 | none | retry_times | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| last_run_at | last_run_at | DATETIME | unknown | True | unknown | none | last_run_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| last_status | last_status | VARCHAR(16) | 16 | True | unknown | none | last_status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| last_error | last_error | TEXT | unknown | True | unknown | none | last_error | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| run_count | run_count | INTEGER | unknown | False | 0 | none | run_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90D11E40> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-user - sys_user

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| username | username | VARCHAR(64) | 64 | False | unknown | IDX | username | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| password | password | VARCHAR(255) | 255 | False | unknown | none | password | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| real_name | real_name | VARCHAR(64) | 64 | False | unknown | IDX | real_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| email | email | VARCHAR(128) | 128 | True | unknown | none | email | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| phone | phone | VARCHAR(32) | 32 | True | unknown | IDX | phone | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| avatar | avatar | VARCHAR(255) | 255 | True | unknown | none | avatar | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| gender | gender | VARCHAR(8) | 8 | False | unknown | none | gender | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| identity | identity | VARCHAR(32) | 32 | False | student | none | identity | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| status | status | VARCHAR(16) | 16 | False | pending | IDX | status | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| school_name | school_name | VARCHAR(128) | 128 | True | unknown | none | school_name | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_id | grade_id | INTEGER | unknown | True | unknown | FK->id+IDX | grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| class_id | class_id | INTEGER | unknown | True | unknown | FK->id+IDX | class_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| grade_admin_grade_id | grade_admin_grade_id | INTEGER | unknown | True | unknown | FK->id | grade_admin_grade_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| must_change_password | must_change_password | BOOLEAN | unknown | False | False | none | must_change_password | unknown | high | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| last_login_at | last_login_at | DATETIME | unknown | True | unknown | none | last_login_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| last_login_ip | last_login_ip | VARCHAR(64) | 64 | True | unknown | none | last_login_ip | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| login_fail_count | login_fail_count | INTEGER | unknown | False | 0 | none | login_fail_count | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| locked_until | locked_until | DATETIME | unknown | True | unknown | none | locked_until | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90E41A80> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| updated_at | updated_at | DATETIME | unknown | False | <function now_local at 0x000001ED90E41B20> | none | updated_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-user-role - sys_user_role

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | id | INTEGER | unknown | False | unknown | PK | id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| user_id | user_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| role_id | role_id | INTEGER | unknown | False | unknown | FK->id+UQ+IDX | role_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |

## TBL-sys-user-token-revocation - sys_user_token_revocation

| Physical Column | Code Field | DB Type | Length/Precision | Nullable | Default | Key/Index | Meaning | Enum/Dictionary | Sensitivity | Writers | Readers | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| user_id | user_id | INTEGER | unknown | False | unknown | PK | user_id | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| invalid_before_ts | invalid_before_ts | FLOAT | unknown | False | unknown | none | invalid_before_ts | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| expire_at | expire_at | DATETIME | unknown | False | unknown | IDX | expire_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
| created_at | created_at | DATETIME | unknown | False | <function now_local at 0x000001ED90E26980> | none | created_at | unknown | low | unknown | unknown | backend/app/models, migrations | 事实/字段含义待补 |
