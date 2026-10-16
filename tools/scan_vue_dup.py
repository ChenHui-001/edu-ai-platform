# -*- coding: utf-8 -*-
"""扫描 .vue 文件中的「复制粘贴残留」隐患。

背景：编辑时误用 replace_all、或用锚点脚本做插入，会把整块模板/脚本复制成
两份。页面表现是「两个同名按钮」「两个同开弹窗」，而 build 与 lint 全部通过。
纯文本块比对会漏报（两份拷贝常被后续微调改得不完全一致），因此这里改用
语义级特征检测：

  A. 同一 v-model 绑定了多个 el-dialog / el-drawer（点开一个弹两个）
  B. 同 (事件 handler + 可见文案) 的 el-button 出现多次
  C. script 顶层同名声明出现多次（ESM 下 const 重复会直接报错，
     function/const 混用则静默变成后者覆盖前者）

每条规则都可给出精确到行号的定位。
"""
from __future__ import annotations

import io
import os
import re
import sys
from collections import defaultdict

MODAL_TAGS = ('el-dialog', 'el-drawer')
BUTTON_TAGS = ('el-button', 'button')
# 这些变量在同文件里出现多处是正常的（每页各自一套筛选项）
LIST_VARS = ('subjects', 'grades', 'knowledgePoints', 'formSubjects', 'formKnowledge')


def _strip_tags(text):
    """把一段模板片段压成单行签名文本。"""
    return re.sub(r'\s+', ' ', text).strip()


def scan_template(tpl):
    problems = []

    # ---- A. 同 v-model 的弹窗 ----
    modals = defaultdict(list)
    for m in re.finditer(r'<(el-dialog|el-drawer)\b([^>]*)>', tpl, re.S):
        tag, attrs = m.group(1), m.group(2)
        vm = re.search(r'v-model="([^"]+)"', attrs)
        title = re.search(r'title="([^"]*)"', attrs)
        key = (tag, vm.group(1) if vm else '(无 v-model)')
        line = tpl[:m.start()].count('\n') + 1
        modals[key].append((line, title.group(1) if title else ''))
    for (tag, vm), items in sorted(modals.items()):
        if len(items) > 1:
            problems.append(('A 同开弹窗', '%s 绑定 %s 出现 %d 次（第 %s 行，标题：%s）'
                            % (tag, vm, len(items),
                               '、'.join(str(i[0]) for i in items),
                               ' / '.join(i[1] or '(无标题)' for i in items))))

    # ---- B. 同 (handler + 文案) 的按钮 ----
    # 仅在「同一父容器」内比较：列表行内的操作按钮与弹窗底部的操作按钮
    # 文案/handler 相同是正常设计（作用于不同对象），不是复制残留。
    btns = defaultdict(list)
    container_re = re.compile(
        r'<(el-dialog|el-drawer|el-table|el-card|el-col)\b[^>]*>', re.S)
    for m in re.finditer(r'<(?:el-button|button)\b([^>]*)>(.*?)</(?:el-button|button)>',
                         tpl, re.S):
        attrs, inner = m.group(1), m.group(2)
        ev = re.findall(r'@(?:click|dblclick|change)="([^"(]+)', attrs)
        label = _strip_tags(re.sub(r'<[^>]+>', ' ', inner))
        if not ev or not label:
            continue
        # 取最近一个容器标签作为归属键
        containers = list(container_re.finditer(tpl, 0, m.start()))
        owner = containers[-1].group(1) + '@' + str(containers[-1].start()) \
            if containers else 'root'
        line = tpl[:m.start()].count('\n') + 1
        btns[(owner, tuple(ev), label)].append(line)
    for (owner, ev, label), lines in sorted(btns.items()):
        if len(lines) > 1:
            problems.append(('B 重复按钮', '同容器内按钮「%s」(%s) 出现 %d 次（第 %s 行）'
                            % (label, '、'.join(ev), len(lines),
                               '、'.join(str(x) for x in lines))))

    return problems


def scan_script(script):
    problems = []
    # script 起始偏移用于行号换算
    decls = defaultdict(list)
    pat = re.compile(r'^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(', re.M)
    pat2 = re.compile(r'^(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=', re.M)
    for rx in (pat, pat2):
        for m in rx.finditer(script):
            name = m.group(1)
            decls[name].append(script[:m.start()].count('\n') + 1)

    for name, lines in sorted(decls.items()):
        if name in LIST_VARS or len(lines) < 2:
            continue
        # 顶层判断：上一非空行不是以 { 开头的块内语句
        real = []
        for ln in lines:
            prev = [l for l in script.split('\n')[:ln - 1] if l.strip()]
            if prev and prev[-1].rstrip().endswith('{'):
                continue
            real.append(ln)
        if len(real) > 1:
            problems.append(('C 重复声明', '顶层标识符 `%s` 重复声明 %d 次（第 %s 行）'
                            % (name, len(real), '、'.join(str(x) for x in real))))
    return problems


def _extract_template(src):
    """取顶层模板内容：从第一个 <template> 后到最后一个 </template> 前。"""
    start = src.find('<template>')
    end = src.rfind('</template>')
    if start < 0 or end < 0 or end <= start:
        return ''
    return src[start + len('<template>'):end]


def scan(path):
    src = io.open(path, encoding='utf-8').read()
    out = []
    tpl = _extract_template(src)
    if tpl:
        out += scan_template(tpl)
    m = re.search(r'<script[^>]*>(.*?)</script>', src, re.S)
    if m:
        out += scan_script(m.group(1))
    return out


def main():
    if len(sys.argv) > 1:
        root = sys.argv[1]
    else:
        root = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src')

    files = []
    for base, _dirs, names in os.walk(root):
        for n in names:
            if n.endswith('.vue'):
                files.append(os.path.join(base, n))

    bad = 0
    for f in sorted(files):
        try:
            hits = scan(f)
        except Exception as exc:                      # noqa: BLE001
            print('扫描异常 %s: %s' % (f, exc))
            continue
        if hits:
            bad += 1
            print('[FAIL] %s' % os.path.relpath(f, root).replace(os.sep, '/'))
            for kind, msg in hits:
                print('       [%s] %s' % (kind, msg))

    print('扫描 %d 个组件，隐患页面 %d 个' % (len(files), bad))
    if bad:
        print('提示：这些是复制粘贴残留，会在页面上出现重复按钮/同开弹窗，'
              '但 build 与 lint 均无法检出，需人工删除多余的一份。')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())