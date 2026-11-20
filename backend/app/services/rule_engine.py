"""规则求值引擎（生产版）。

把散落在业务代码里的 `raise BusinessException(...)` 外置成**可声明、可求值**的规则。
规则来自本体 M3 模型（YAML），由本模块加载并注册；业务代码只声明"这条规则在此处生效"。

安全立场（与 code-paas 的关键差异）：
  code-paas 的 `simple_eval(expression, names=params)` 默认开放 Python 内建函数
  与属性访问。本项目的规则表达式来自可被管理员编辑的 YAML，因此必须显式收窄：
    1. 只允许白名单函数，其余一律拒绝；
    2. 禁用 dunder 属性穿透与未声明字段的下标访问；
    3. 表达式长度与禁用标识符上限；
    4. 字段可见性 **fail-closed** —— 规则不显式声明 `reads` 时，对象字段一律不可读；
    5. 敏感字段硬黑名单，即使被声明也不放行。

原型的可行性验证见 audit-reports/ontology-inventory/prototype/（80/80 通过）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Optional

from simpleeval import SimpleEval


MAX_EXPRESSION_LENGTH = 500

# 表达式方言：七模型框架用 SQL 风格大写关键字（AND/OR/NOT），
# 而 simpleeval 只吃 Python 语法（and/or/not）。
# 框架的 M3 模板与 reference-example 里全是大写，若直接送进 simpleeval
# 会 100% SyntaxError。这里做一层**词法级**转换（只替换独立单词，
# 不碰字符串字面量里的 "AND"），让框架原生表达式无需改写即可求值。
_SQL_TO_PY = {
    "AND": "and",
    "OR": "or",
    "NOT": "not",
    "TRUE": "True",
    "FALSE": "False",
    "NULL": "None",
}


def _to_python_dialect(expression: str) -> str:
    """把 SQL 风格大写关键字转成 Python 语法，跳过字符串字面量内部。"""
    out: list = []
    i = 0
    n = len(expression)
    quote: Optional[str] = None
    while i < n:
        ch = expression[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(expression[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (expression[j].isalnum() or expression[j] == "_"):
                j += 1
            word = expression[i:j]
            out.append(_SQL_TO_PY.get(word, word))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _is_number(value: Any) -> bool:
    """框架 M3 模板里用的 isNumber()：布尔不是数字（Python 里 bool 是 int 的子类）。"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class _Projection:
    """规则可见的对象投影：只暴露声明过的字段名。

    为什么需要它：规则表达式要写 `question.grade_id`（点号语法），
    但直接传 SQLAlchemy 模型进去等于把整个 Python 对象图交给求值器——
    `question.__dict__`、`question._sa_instance_state` 都能摸到。
    投影类只把白名单字段挂到 `__slots__` 上，其余属性访问一律 AttributeError。
    """

    __slots__ = ("_data", "_fields")

    def __init__(self, data: Dict[str, Any], fields: Iterable[str]):
        object.__setattr__(self, "_data", data)
        object.__setattr__(self, "_fields", tuple(fields))

    def __getattr__(self, name: str) -> Any:
        fields = object.__getattribute__(self, "_fields")
        if name not in fields:
            raise AttributeError(f"规则不可访问字段：{name}")
        return object.__getattribute__(self, "_data")[name]

    def __getitem__(self, key: str) -> Any:
        # 下标访问与点号访问必须走**同一套**白名单。
        # 否则 `x['password_hash']` 会绕过 __getattr__ 的检查。
        fields = object.__getattribute__(self, "_fields")
        if key not in fields:
            raise KeyError(f"规则不可访问字段：{key}")
        return object.__getattribute__(self, "_data")[key]

    def __len__(self) -> int:
        return len(object.__getattribute__(self, "_data"))

    def __contains__(self, item: Any) -> bool:
        # 只允许「字段名 in 投影」，不允许「值 in 数据」——
        # 后者会泄漏数据内容并让 'x' in proj 这种写法含义模糊。
        return item in object.__getattribute__(self, "_fields")

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _Projection):
            return (object.__getattribute__(self, "_data")
                    == object.__getattribute__(other, "_data"))
        return NotImplemented

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return f"_Projection({sorted(object.__getattribute__(self, '_fields'))})"


_SAFE_SCALARS = (int, float, str, bool, type(None))

# 敏感字段名：即使规则声明了也不放行。
# 这些是"公开标量属性"但本质是机密，放进表达式上下文就等于泄漏。
_SENSITIVE_FIELDS = frozenset({
    "password", "password_hash", "hashed_password", "secret", "token",
    "api_key", "apikey", "access_token", "refresh_token", "private_key",
    "salt", "jwt_secret", "secret_key",
})

# 集合类容器：保留原对象不投影。
# 投影成 _Projection 会把 `len(items)` / `x in items` 的语义改掉
# （dict 的 len 是键数、list 的 len 是元素数，混在一起会算错）。
_SAFE_CONTAINERS = (list, tuple, set, frozenset)


def _project_names(names: Dict[str, Any], declared: Optional[Iterable[str]] = None) -> tuple:
    """把 names 投影成 (可求值命名空间, 允许访问的字段名集合)。

    - 标量（int/float/str/bool/None）原样保留
    - dict → 投影为 _Projection，字段 = 自身 keys
    - ORM 对象 / 其他对象 → 投影为 _Projection，字段 = 其 __dict__ 里的
      **公开且标量**属性（不碰 _sa_instance_state 这类下划线私有字段）

    `declared` 是规则**显式声明**可读的字段集合。

    为 None 时**不放行任何对象字段**（fail-closed）：
    规则不声明 reads，就读不到对象的任何属性，只有显式传入的标量
    与 dict 的**顶层键**可用。

    这里刻意不做「为 None 时退化为全部公开标量属性」的宽松默认：
    那意味着漏写 reads 的规则能读到整个 ORM 对象的公开字段——
    password_hash 虽然有硬黑名单，但业务字段（分数、状态、他人数据）
    会一并泄漏。宽松默认一旦被依赖，安全边界就名存实亡。
    """
    declared_set = set(declared) if declared is not None else None
    projected: Dict[str, Any] = {}
    all_fields: set = set()
    for key, value in names.items():
        if isinstance(value, _Projection):
            projected[key] = value
            continue
        if isinstance(value, _SAFE_SCALARS):
            projected[key] = value
            continue
        if isinstance(value, _SAFE_CONTAINERS):
            # 元素若是复杂对象，仍需投影，否则 list 里的 ORM 实例会漏出去
            if all(isinstance(v, _SAFE_SCALARS) for v in value):
                projected[key] = value
            else:
                # 只保留标量元素；容器里的复杂对象不投影给规则
                projected[key] = [v for v in value if isinstance(v, _SAFE_SCALARS)]
            continue
        if isinstance(value, dict):
            fields = tuple(
                k for k in value.keys()
                if isinstance(k, str)
                and k not in _SENSITIVE_FIELDS
                and (declared_set is None or k in declared_set)
            )
            # dict 的值也要递归投影：否则 `x['a']` 取出的若是嵌套 dict，
            # 再 `['b']` 就能读到未声明的字段（对抗测试抓到的穿透路径）。
            safe_values = {
                k: _project_scalar_or_dict(v, declared_set)
                for k, v in value.items()
                if k in fields
            }
            projected[key] = _Projection(safe_values, fields)
            all_fields.update(fields)
            continue
        # ORM 实例或其他对象：只取公开标量属性
        data: Dict[str, Any] = {}
        raw = getattr(value, "__dict__", {}) or {}
        for attr, attr_value in raw.items():
            if attr.startswith("_"):
                continue
            if attr in _SENSITIVE_FIELDS:
                continue
            # declared 为 None → 一律不放行（fail-closed，见 docstring）
            if declared_set is None or attr not in declared_set:
                continue
            if isinstance(attr_value, _SAFE_SCALARS):
                data[attr] = attr_value
        fields = tuple(data.keys())
        projected[key] = _Projection(data, fields)
        all_fields.update(fields)
    return projected, all_fields


def _project_scalar_or_dict(value: Any, declared_set: Optional[set]) -> Any:
    """dict 的值递归投影：嵌套 dict 只保留已声明的键。"""
    if isinstance(value, dict):
        fields = tuple(
            k for k in value.keys()
            if isinstance(k, str)
            and k not in _SENSITIVE_FIELDS
            and (declared_set is None or k in declared_set)
        )
        safe = {
            k: _project_scalar_or_dict(v, declared_set)
            for k, v in value.items() if k in fields
        }
        return _Projection(safe, fields)
    if isinstance(value, _SAFE_SCALARS):
        return value
    return None


_ALLOWED_FUNCTIONS: Dict[str, Callable[..., Any]] = {
    # 框架 M3 模板专用
    "isNumber": _is_number,
    # 数学
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sum": sum,
    "len": len,
    "int": int,
    "float": float,
    "bool": bool,
    # 字符串（受限白名单，不给 format/getattr）
    "str": str,
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    # 集合
    "any": any,
    "all": all,
    "sorted": sorted,
    "set": set,
    "list": list,
    "tuple": tuple,
    "dict": dict,
}

_FORBIDDEN_TOKENS = (
    "__",           # dunder / 属性穿透
)

# 禁用词必须按**独立单词**匹配，不能用子串包含。
# 第一版用 `"os" in expression` 判定，把 "ongoing"（考试进行中状态值）
# 里的 "os" 也命中了，导致 RULE-TUTOR-NO-ANSWER-DURING-EXAM 被误杀。
# 正确做法：切出标识符 token 后精确比对。
_FORBIDDEN_IDENTIFIERS = {
    "import", "lambda", "eval", "exec", "compile", "open",
    "getattr", "setattr", "delattr", "globals", "locals", "vars",
    "breakpoint", "subprocess", "os", "sys", "socket", "requests",
    "print", "input", "exit", "quit", "help", "dir",
}

# 字面量上允许调用的安全方法（字符串格式化等无害操作）。
_SAFE_LITERAL_METHODS = frozenset({
    "upper", "lower", "strip", "lstrip", "rstrip", "split", "join",
    "startswith", "endswith", "replace", "count", "find",
    "format",
})


class RuleExpressionError(ValueError):
    """表达式本身不合法（语法错误 / 越权 / 超限）。"""


class RuleViolation(Exception):
    """规则求值通过语法检查，但业务条件不满足。"""

    def __init__(self, rule_id: str, message: str):
        self.rule_id = rule_id
        self.message = message
        super().__init__(message)


def _assert_safe_expression(expression: str) -> None:
    """在送进求值器之前先做静态拒绝。"""
    if not isinstance(expression, str) or not expression.strip():
        raise RuleExpressionError("规则表达式为空")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise RuleExpressionError(
            f"规则表达式超长（>{MAX_EXPRESSION_LENGTH} 字符）")
    lowered = expression.lower()
    for token in _FORBIDDEN_TOKENS:
        if token in lowered:
            raise RuleExpressionError(f"规则表达式包含禁用片段：{token}")
    # 独立单词精确比对（子串匹配会把 "ongoing" 误判成含 "os"）
    for ident in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression):
        if ident.lower() in _FORBIDDEN_IDENTIFIERS:
            raise RuleExpressionError(f"规则表达式包含禁用标识符：{ident}")
    # 不允许对**字符串字面量**取属性（"x".__class__ 这种钩子）。
    # 注意不能一刀切禁掉所有 "字面量." —— "'{}'.format(x)" 是无害且常用的。
    # 判据：字面量后跟的属性名必须是白名单里的安全方法。
    for lit_attr in re.findall(r"[\"']([^\"']*)[\"']\s*\.\s*([A-Za-z_][A-Za-z0-9_]*)",
                               expression):
        if lit_attr[1] not in _SAFE_LITERAL_METHODS:
            raise RuleExpressionError(
                f"规则表达式不允许对字面量取属性：.{lit_attr[1]}")


def evaluate_expression(expression: str, names: Dict[str, Any],
                        declared: Optional[Iterable[str]] = None) -> Any:
    """受限求值：只暴露白名单函数，属性访问按规则声明放行。

    `declared` 是规则显式声明可读的字段名；为 None 时 fail-closed
    （对象字段一律不可读），只放行标量与显式传入的 dict 键。
    """
    _assert_safe_expression(expression)
    expression = _to_python_dialect(expression)
    projected, allowed = _project_names(names, declared=declared)
    evaluator = SimpleEval(
        functions=dict(_ALLOWED_FUNCTIONS),
        names=projected,
        # 按类型白名单：只有 _Projection 实例的**声明字段**可被点号访问，
        # 其余一切属性（含 __class__ / __dict__ / ORM 的内部属性）一律拒绝。
        # simpleeval 自带 DISALLOW_PREFIXES（_ 与 func_）做第二道防线。
        #
        # 两层白名单必须一致：_Projection.__getattr__ 放行字段 A，
        # 但 simpleeval 的 allowed_attrs 不含 A 时仍会在更外层拒绝
        # （对抗测试第一版踩过：投影放行了、simpleeval 没放行）。
        # 所以 allowed_attrs 用的是**同一份**字段集合。
        allowed_attrs={_Projection: allowed},
    )
    try:
        return evaluator.eval(expression)
    except RuleExpressionError:
        raise
    except Exception as exc:  # 求值期异常统一收敛
        raise RuleExpressionError(f"规则表达式求值失败：{exc}") from exc


# ══════════════════════════════════════════════════════════
# 规则模型与注册表
# ══════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    expression: str
    violation_message: str
    enforced_at: str = "ALWAYS"
    category: str = "FIELD"
    description: str = ""
    params: tuple = field(default_factory=tuple)
    # 规则**显式声明**可读的字段名。这是字段访问的安全边界：
    # 不声明 → 求值上下文里的对象字段一律不可读（fail-closed）。
    reads: tuple = field(default_factory=tuple)

    def check(self, names: Dict[str, Any]) -> None:
        """规则不满足时抛 RuleViolation。"""
        result = evaluate_expression(self.expression, names, declared=self.reads)
        if not result:
            raise RuleViolation(self.id, self.violation_message)


class RuleRegistry:
    """规则注册表。"""

    def __init__(self, rules: Optional[Iterable[Rule]] = None):
        self._rules: Dict[str, Rule] = {}
        for rule in rules or ():
            self.register(rule)

    def register(self, rule: Rule) -> None:
        if rule.id in self._rules:
            raise ValueError(f"规则 ID 重复：{rule.id}")
        # 注册即静态校验：语法错 / 越权的表达式在启动时就该炸，
        # 而不是等到某条业务数据触发它才炸。
        _assert_safe_expression(rule.expression)
        self._rules[rule.id] = rule

    def get(self, rule_id: str) -> Optional[Rule]:
        return self._rules.get(rule_id)

    def require(self, rule_id: str) -> Rule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise KeyError(f"规则不存在：{rule_id}")
        return rule

    def all(self) -> Dict[str, Rule]:
        return dict(self._rules)

    def check(self, rule_id: str, names: Dict[str, Any]) -> None:
        self.require(rule_id).check(names)

    def check_many(self, rule_ids: Iterable[str], names: Dict[str, Any]) -> None:
        for rule_id in rule_ids:
            self.check(rule_id, names)
