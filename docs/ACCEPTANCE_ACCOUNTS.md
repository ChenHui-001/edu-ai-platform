# 固定验收账号

> 三个长期固定、密码不变的私有账号，用于日常使用与测试。
> 账号定义以 [`tools/ensure_acceptance_accounts.py`](../tools/ensure_acceptance_accounts.py)
> 为**唯一真源**；口令本身**不入仓库**，存在仓库外的受限文件里。

## 一、账号

| 角色 | 账号 | identity | 绑定班级 | 说明 |
|---|---|---|---|---|
| 系统管理员 | `owner_admin` | `sys_admin` | — | 全部权限（65 个权限点） |
| 教师 | `owner_teacher` | `teacher` | 一年级(1)班 | 含该班「数学」授课关系 |
| 学生 | `owner_student` | `student` | 一年级(1)班 | 与教师同班，能看到班级数据 |

口令由你在本地保管（仓库外的 `PRIVATE_ACCOUNTS_PASSWORD_*.txt`，服务器侧
`/opt/edu-ai-platform/.acceptance_password`，权限 0600 root:root）。
**本文档不写口令**，也不在任何地方回显它。

## 二、什么时候用

| 时机 | 做什么 |
|---|---|
| 日常自测 | 直接用这三个账号登录生产：`https://592587860.xyz:8443` |
| 换环境后 | 换机、迁库、重建库之后，账号是**数据**会丢 —— 跑一次下面的脚本重新拉齐 |
| 怀疑口令被改 | 重跑脚本即可重置回你保管的口令 |
| 测试中输错被锁 | 重跑脚本会清零 `locked_until` 与 `login_fail_count` |
| 新增验收账号 | 改脚本里的 `ACCOUNTS` 列表（唯一真源），再跑脚本 |

## 三、怎么执行

### 生产服务器

```bash
# 1. 口令文件（若已存在则跳过），权限必须 0600
umask 077
vi /opt/edu-ai-platform/.acceptance_password    # 每行一个：管理员 / 教师 / 学生
chmod 600 /opt/edu-ai-platform/.acceptance_password

# 2. 脚本送进容器并执行（tools/ 不进镜像，需 docker cp）
docker cp tools/ensure_acceptance_accounts.py edu-platform:/tmp/ensure_acceptance_accounts.py
docker cp /opt/edu-ai-platform/.acceptance_password edu-platform:/tmp/acceptance_password
docker exec -u root edu-platform sh -c \
  'chmod 644 /tmp/ensure_acceptance_accounts.py && chown app:app /tmp/acceptance_password'

docker exec edu-platform sh -c \
  'cd /app && python /tmp/ensure_acceptance_accounts.py --password-file /tmp/acceptance_password'
```

### 本地开发

```powershell
python tools/ensure_acceptance_accounts.py --password-file D:/secure/pwd.txt
python tools/ensure_acceptance_accounts.py --password-file D:/secure/pwd.txt --dry-run
```

## 四、口令来源

按优先级从高到低：

1. `--password-file <路径>`
2. 环境变量 `ACCEPTANCE_PASSWORD_FILE` 指向的文件
3. 环境变量 `ACCEPTANCE_PASSWORD`（三个账号共用同一个口令）

都拿不到就报错退出 —— 脚本**刻意不内置默认口令**。
固定口令必须由你自己保管，不能进代码库。

文件支持两种格式：

- **每行一个**（顺序：管理员 / 教师 / 学生）
- **key=value**（`owner_admin=xxx`，顺序无关，更不容易错位）

## 五、脚本做对了什么

- **幂等**：可反复执行。已存在的账号只重置口令，不重复建。
- **建全关联**：角色 + 班级 + 授课关系一次对齐。少绑一处就会出现
  「能登录但页面上什么都看不到」——教师看不到学生、学生不在班级、
  待办列表空。
- **环境就绪**：先跑 `init_roles` / `init_grades_subjects`（都是幂等，只增不删），
  所以全新库、迁库后也能一键就绪，不依赖演示数据开关。
- **重置锁定**：`must_change_password=False`、`locked_until=None`、
  `login_fail_count=0`。前两个保证「密码固定」这个用途成立
  （否则每次登录都被拦去改密）；第三个避免测试输错一次就锁 15 分钟。
- **不回显口令**：只重置哈希，不打印明文。

## 六、安全边界

这三个是**私有验收账号**，不对公网开放用途：

- 口令保存在仓库外的受限文件里（服务器 0600 root:root），不提交、不打印。
- 真实生产用户走正常流程：注册 → 审批 → 首登强制改密，不受影响。
- `enforce_default_admin_password` 只会处置仍在用出厂口令
  `Admin@123456` 的超级管理员，且**不会**命中这三个账号
  （它们的口令不是出厂口令）。

若哪天要下线这三个账号：删掉脚本 `ACCOUNTS` 列表对应项并重跑脚本，
或在系统管理页直接禁用该账号。

