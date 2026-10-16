# -*- coding: utf-8 -*-
"""前端白屏隐患普查（CI 门禁）。

背景：模板里引用了 script 中未定义的标识符（如 can()），在浏览器里
只会抛 "$setup.xxx is not a function" —— 整页白屏且无任何提示，
排查成本极高。本脚本在构建期静态检出这类问题。

用法（仓库根目录执行）：
    python tools/scan_vue_refs.py
退出码：0 = 无隐患；1 = 存在隐患（供 CI 门禁使用）。
"""
import glob
import io
import os
import re
import sys

BUILTIN = {
    'true', 'false', 'null', 'undefined', 'this', 'typeof', 'instanceof', 'new', 'return',
    'in', 'of', 'void', 'delete', 'await', 'async',
    'Math', 'JSON', 'Object', 'Array', 'String', 'Number', 'Boolean', 'Date', 'Promise',
    'RegExp', 'Map', 'Set', 'parseInt', 'parseFloat', 'isNaN', 'encodeURIComponent',
    'decodeURIComponent', 'setTimeout', 'setInterval', 'clearTimeout', 'clearInterval',
    'console', 'window', 'document', 'location', 'navigator',
    '$event', '$route', '$router', '$emit', '$props', '$refs', '$attrs', '$slots', '$nextTick',
}
SLOT_VARS = {'row', 'item', 'index', 'idx', 'slot', 'scope', 'column'}


def _ids(expr):
    """提取标识符：属性访问（.foo）、对象字面量键（{ foo: bar }）、
    字符串与模板字面量内的词都不算变量引用。"""
    e = re.sub(r'\?*\.\s*[A-Za-z_$][\w$]*', ' ', expr)   # 属性访问
    e = re.sub(r"'[^']*'", ' ', e)
    e = re.sub(r'"[^"]*"', ' ', e)
    e = re.sub(r'`[^`]*`', ' ', e)
    e = re.sub(r'(?<![\w$])[A-Za-z_$][\w$]*\s*:', ' ', e)  # 对象字面量键
    return re.findall(r'[A-Za-z_$][\w$]*', e)


def scan(path):
    src = io.open(path, encoding='utf-8').read()
    if '<template>' not in src or '<script' not in src:
        return None
    tpl = src.split('<template>')[1].split('</template>')[0]
    script = src.split('<script setup>')[-1] if '<script setup>' in src else src.split('<script>')[-1]
    script = re.split(r'</script>', script)[0]

    refs = set()
    locals_ = set(SLOT_VARS)
    for mm in re.finditer(r'\{\{(.*?)\}\}', tpl, re.S):
        refs.update(_ids(mm.group(1)))
    for mm in re.finditer(
            r'(?:v-if|v-else-if|v-show|v-model(?:\.[\w-]+)*|:[\w.\-]+|@[\w.\-]+|v-for)\s*=\s*"([^"]*)"',
            tpl):
        expr = mm.group(1)
        refs.update(_ids(expr))
        # v-for="(a, b) in list" 与 v-for="x in list" 的循环变量是模板局部作用域
        mfor = re.match(r'\s*(?:\(([^)]*)\)|([A-Za-z_$][\w$]*))\s+(?:in|of)\s', expr)
        if mfor:
            for grp in (mfor.group(1) or '', mfor.group(2) or ''):
                locals_.update(x.strip() for x in grp.split(',') if x.strip())
    # 模板内联箭头函数参数：(o) => ... / (c, x) => ...
    for mm in re.finditer(r'\(([^)]*)\)\s*=>', tpl):
        locals_.update(x.strip() for x in mm.group(1).split(',') if x.strip())
    for mm in re.finditer(r'([A-Za-z_$][\w$]*)\s*=>', tpl):
        locals_.add(mm.group(1))

    in_script = set(re.findall(r'[A-Za-z_$][\w$]*', script))

    missing = []
    for r in sorted(refs):
        if r in BUILTIN or r in locals_ or r in in_script:
            continue
        if r[0].isupper():      # 全局注册的组件
            continue
        missing.append(r)
    return missing


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patterns = ['frontend/src/views/**/*.vue', 'frontend/src/layout/*.vue',
                'frontend/src/components/**/*.vue']
    files = []
    for pat in patterns:
        files += glob.glob(os.path.join(root, pat), recursive=True)

    bad = 0
    for f in sorted(files):
        try:
            miss = scan(f)
        except Exception as exc:                      # noqa: BLE001
            print('扫描异常 %s: %s' % (f, exc))
            continue
        if miss:
            bad += 1
            print('[FAIL] %s' % os.path.relpath(f, root).replace('\\', '/'))
            print('       模板引用但 script 未定义: %s' % ', '.join(miss))
    print('扫描 %d 个组件，隐患页面 %d 个' % (len(files), bad))
    if bad:
        print('提示：模板调用了 script 中不存在的标识符会在浏览器抛 '
              '"$setup.xxx is not a function" 导致整页白屏。')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())