"""N+1 查询与全表扫描静态扫描器。

检测四类问题（都只在运行时表现为"慢"，静态看代码完全正常）：

  A. 循环内逐条查库（N+1）
     for x in rows: db.get(Model, x.fk) / db.scalar(...) / db.execute(...)
     —— Session 的 identity map 是 weakref 的，循环里用完即弃的对象不会命中缓存，
        每一轮都会真实发一条 SQL。若被查实体还带 lazy="selectin" 关系，
        一条变三条（实测 /edu/subjects 60 行 → 178 条 SQL / 42ms）。

  B. 列表端点无分页（全表扫描）
     返回 .all() 且函数签名里没有 PageParams / limit / offset。

  C. 高频实体携带 selectin 关系
     lazy="selectin" 在每个父对象加载时都发一条额外查询；
     挂在 Grade 这种"每次下拉都要读"的小表上收益为负。

  D. 外键列无索引
     where/join 用到的列没有 index=True 也没有显式 Index()。

用法：
    python tools/check_n_plus_one.py            # 报告
    python tools/check_n_plus_one.py --strict   # 有 A 类即非零退出（CI 用）

退出码：--strict 下发现 A 类问题返回 1；--ratchet 下 A 类数量超过基线返回 1。
"""
import argparse
import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
API_DIR = ROOT / "backend" / "app" / "api"
MODEL_DIR = ROOT / "backend" / "app" / "models"

# A 类（循环内逐条查库）基线，**只许降不许升**。
#
# 为什么不用 `--strict` 直接卡死：存量 86 处一次性全部整改不现实，而
# 「装上去就红」的门禁一定会被注释掉（团队会为了交付把整行删了）。
# 棘轮的效果等价于冻结现状：新写的循环内查库立刻失败，存量逐批消化。
# 每修完一批，把这个数字下调到实测值。
BASELINE_A = 86

DB_CALLS = {"get", "scalar", "scalars", "execute", "query"}
DB_OBJ_HINT = re.compile(r"^(db|session|_db|sess)$", re.I)


def _call_name(node: ast.Call):
    """返回 ('db', 'get') 这类二元组；非 db 调用返回 None。"""
    f = node.func
    if not isinstance(f, ast.Attribute):
        return None
    base = f.value
    if isinstance(base, ast.Name) and DB_OBJ_HINT.match(base.id):
        return (base.id, f.attr)
    return None


def scan_n_plus_one():
    """A 类：循环体内的逐条查库。

    只报「循环源来自数据库结果」的情形 —— 这是 N+1 的定义。
    `for ref in ("a", "b")` 这种固定小循环即使内部查库也不是 N+1
    （最多 2 条，且与数据量无关），报出来只会淹没真问题。
    """
    hits = []
    for path in sorted(API_DIR.rglob("*.py")):
        try:
            src = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # 收集函数内「来自数据库」的变量名：x = db.scalars(...).all()
            db_vars = set()
            for node in ast.walk(fn):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                    seg = ast.get_source_segment(src, node.value) or ""
                    if re.search(r"\bdb\w*\.", seg) or ".all()" in seg:
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                db_vars.add(t.id)

            def from_db(iter_node):
                seg = ast.get_source_segment(src, iter_node) or ""
                if re.search(r"\bdb\w*\.", seg) or ".all()" in seg:
                    return True
                if isinstance(iter_node, ast.Name):
                    return iter_node.id in db_vars
                # for a, b in rows: / for x in (a or [])
                for sub in ast.walk(iter_node):
                    if isinstance(sub, ast.Name) and sub.id in db_vars:
                        return True
                return False

            for node in ast.walk(fn):
                bodies = []
                if isinstance(node, (ast.For, ast.AsyncFor)):
                    if from_db(node.iter):
                        bodies.append(node.body)
                elif isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                    it = node.generators[0].iter if node.generators else None
                    if it is not None and from_db(it):
                        bodies.append([node])
                for body in bodies:
                    for sub in body:
                        for c in ast.walk(sub):
                            if isinstance(c, ast.Call):
                                nm = _call_name(c)
                                if nm and nm[1] in DB_CALLS:
                                    hits.append((path, c.lineno, fn.name, f"{nm[0]}.{nm[1]}"))
    return hits


PAGE_HINT = re.compile(r"PageParams|page\s*:|page_size|limit\s*:|offset\s*:")


def scan_unpaged_lists():
    """B 类：返回 .all() 但签名里没有分页参数的 GET 端点。"""
    hits = []
    for path in sorted(API_DIR.rglob("*.py")):
        src = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef):
                continue
            is_get = any(
                isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                and d.func.attr == "get"
                for d in fn.decorator_list
            )
            if not is_get:
                continue
            body_src = ast.get_source_segment(src, fn) or ""
            if ".all()" not in body_src:
                continue
            # 用 unparse 而非 get_source_segment：arguments 节点没有独立位置信息，
            # get_source_segment 返回 None，会把所有带分页的端点误报成"无分页"。
            try:
                args_src = ast.unparse(fn.args)
            except Exception:
                args_src = ""
            if PAGE_HINT.search(args_src):
                continue
            hits.append((path, fn.lineno, fn.name))
    return hits


def scan_selectin():
    """C 类：lazy="selectin" 的关系。"""
    hits = []
    for path in sorted(MODEL_DIR.glob("*.py")):
        src = path.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'(\w+):\s*Mapped\[[^\]]+\]\s*=\s*relationship\((.*?)\)\s*$', src, re.M):
            if 'lazy="selectin"' in m.group(2):
                hits.append((path, src[: m.start()].count("\n") + 1, m.group(1)))
    return hits


def scan_fk_no_index():
    """D 类：ForeignKey 列没有 index=True。"""
    hits = []
    for path in sorted(MODEL_DIR.glob("*.py")):
        src = path.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"(\w+):\s*Mapped\[[^\]]+\]\s*=\s*mapped_column\((.*?)\)\s*$", src, re.M):
            args = m.group(2)
            if "ForeignKey(" in args and "index=True" not in args and "primary_key" not in args:
                hits.append((path, src[: m.start()].count("\n") + 1, m.group(1)))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="发现 A 类问题即非零退出")
    ap.add_argument("--ratchet", action="store_true",
                    help=f"A 类数量超过基线（{BASELINE_A} 处）即非零退出；只许降不许升")
    args = ap.parse_args()

    a = scan_n_plus_one()
    b = scan_unpaged_lists()
    c = scan_selectin()
    d = scan_fk_no_index()

    print("=" * 78)
    print(f"A 类｜循环内逐条查库（N+1 高危）：{len(a)} 处")
    print("=" * 78)
    for path, line, fn, call in a:
        print(f"  {path.relative_to(ROOT)}:{line}  {fn}()  → {call}")
    if not a:
        print("  未发现")

    print()
    print("=" * 78)
    print(f"B 类｜GET 端点无分页返回 .all()：{len(b)} 处")
    print("=" * 78)
    for path, line, fn in b:
        print(f"  {path.relative_to(ROOT)}:{line}  {fn}()")
    if not b:
        print("  未发现")

    print()
    print("=" * 78)
    print(f"C 类｜lazy=selectin 关系：{len(c)} 处")
    print("=" * 78)
    for path, line, attr in c:
        print(f"  {path.relative_to(ROOT)}:{line}  .{attr}")
    if not c:
        print("  未发现")

    print()
    print("=" * 78)
    print(f"D 类｜外键列缺索引：{len(d)} 处")
    print("=" * 78)
    for path, line, col in d:
        print(f"  {path.relative_to(ROOT)}:{line}  {col}")
    if not d:
        print("  未发现")

    if args.strict and a:
        print(f"\n[FAIL] 存在 {len(a)} 处循环内查库，请改为批量预取。")
        return 1
    if args.ratchet:
        if len(a) > BASELINE_A:
            print(f"\n[FAIL] A 类由基线 {BASELINE_A} 处升到 {len(a)} 处 —— 新增了循环内查库。"
                  f"\n       请改为批量预取（in_ 查询 + 字典映射），或在明确接受代价时上调 BASELINE_A。")
            return 1
        if len(a) < BASELINE_A:
            print(f"\n[PASS] A 类 {len(a)} 处，优于基线 {BASELINE_A} 处。"
                  f"\n       ★ 请把 tools/check_n_plus_one.py 的 BASELINE_A 下调为 {len(a)}，锁定收益。")
        else:
            print(f"\n[PASS] A 类 {len(a)} 处，与基线一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
