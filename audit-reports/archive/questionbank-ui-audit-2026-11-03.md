# 题库管理页功能排查与修复报告

- **日期**：2026-11-03
- **基线**：v2.2.20（`be857cb`）
- **范围**：`frontend/src/views/teacher/QuestionBank.vue`（1500 行）及其调用的 AI 出题接口
- **结论**：报告的 2 个缺陷已修复并反向验证；另发现 3 处同类缺陷（同一根因族）一并修复；15 项 UI 断言全通过

---

## 1. 缺陷 A：切换年级后学科显示为数字

### 现象
打开「AI 智能出题」，选学科 → 选年级 → 再切年级，学科下拉框显示 `33` 这类数字。

### 根因（三个条件同时成立才出现）

**① 学科下拉的数据源是「按名称去重」的列表**

```js
// onMounted
eduApi.subjects({ distinct: true })   // 每项带 same_name_ids / same_name_grade_ids
```

去重列表里每个学科只保留一条代表记录，`:value="s.id"` 是**代表 id**（`sort` 最小的那条，通常是一年级的记录）。而学科的真实唯一键是 `(grade_id, name)` —— `subject_id` 精确到年级。

**② 切换年级时把 v-model 改成了「该年级的精确 id」**

```js
function syncAiSubjectByGrade() {
  const s = subjects.value.find(x => x.id === aiForm.subject_id
    || (x.same_name_ids || []).includes(aiForm.subject_id))
  if (!s) return                                    // ← 静默失败 1
  const idx = (s.same_name_grade_ids || []).indexOf(aiForm.grade_id)
  if (idx >= 0) aiForm.subject_id = s.same_name_ids[idx]   // ← 写成精确 id
}
```

**③ 精确 id 不在 options 的 value 集合里**

el-select 找不到匹配的 option 时，会把原始 value 当文本回显 —— 用户看到的就是那个数字。

此外两处静默失败（`if (!s) return`、`if (idx >= 0)` 不成立时）会留下脏值：模型里存着一个列表里不存在的 id，界面显示数字，但按钮仍可点击（`:disabled="!aiForm.subject_id"` 为 false），请求会带着这个 id 发出去。

### 反向验证

把文件回退到修复前版本，用同一组断言跑：

```
切到七年级后 学科= "33"
>>> BUG 复现：学科显示为数字
```

修复后同一位置显示 `"先选年级"`。

### 修复

**改为「先年级、后学科」，学科列表按年级精确加载**，彻底删除 id 映射层：

```html
<el-col :span="12">
  <el-form-item label="年级" required>
    <el-select v-model="aiForm.grade_id" @change="onAiGradeChange">…</el-select>
  </el-form-item>
</el-col>
<el-col :span="12">
  <el-form-item label="学科" required>
    <el-select v-model="aiForm.subject_id" :disabled="!aiForm.grade_id"
               @change="onAiSubjectChange">
      <el-option v-for="s in aiSubjects" :key="s.id" :label="s.name" :value="s.id" />
    </el-select>
  </el-form-item>
</el-col>
```

```js
async function onAiGradeChange() {
  aiForm.subject_id = null          // 年级变了，学科必重选
  aiForm.knowledge_point_id = null
  aiKps.value = []
  resetAiResult()
  await loadAiSubjects(aiForm.grade_id)   // 精确列表，无映射
}
```

**为什么不是「保留去重列表 + 提交时映射」**：出题本来就依赖年级（知识点、难度分布都按年级取），年级未定时无法确定该用哪条 subject 记录。映射方案在 `same_name_grade_ids` 缺项时仍然会失败，属于把不确定性留在系统里。

---

## 2. 缺陷 B：题目生成后按钮仍显示「生成并入库」

### 现象
生成完成、结果表格已出现，但 footer 主按钮仍是 primary 的「生成并入库」，用户无法判断是否还要再点一次才保存。

### 根因

**① 按钮不随结果变化**

```html
<!-- 修复前 -->
<el-button type="primary" :loading="aiLoading" :disabled="!aiForm.subject_id"
           @click="generateAi">生成并入库</el-button>
```

无论有没有结果，文案、类型、可用性完全一样。生成成功后按钮仍可点，重复点击会再生成一批并重复入库。

**② 更严重：`saved` 被忽略，导致谎报成功**

后端 `QuestionGeneratorAgent` 有两条返回路径：

| 路径 | `questions` | `saved` | 实际结果 |
|---|---|---|---|
| 模型生成并落库 | N 条 | N | 真的入库了 |
| 题库复用 / 规则引擎降级 | N 条 | **0** | **一题都没写库** |

旧前端只看 `questions.length`：

```js
aiResult.value = d.questions || []
if (aiResult.value.length) {
  ElMessage.success(`已生成 ${aiResult.value.length} 题并保存至题库（草稿）`)  // ← saved=0 时是假的
}
```

复用的题本来就在库里，用户以为新增了一批，去列表按「来源=AI」筛选却发现没有新题。

### 修复

按钮按结果切换语义 + 按 `saved` 区分提示：

```html
<el-button @click="aiDlg = false">{{ aiResult?.length ? '完成' : '关闭' }}</el-button>
<el-button v-if="aiResult?.length" :loading="aiLoading" @click="generateAi">再生成一批</el-button>
<el-button v-else type="primary" :loading="aiLoading"
           :disabled="!aiForm.grade_id || !aiForm.subject_id"
           @click="generateAi">生成并入库</el-button>
```

```js
aiResultSaved.value = Number(d.saved || 0)
if (aiResultSaved.value > 0) {
  ElMessage.success(`已生成 ${aiResult.value.length} 题，${aiResultSaved.value} 题已入库（草稿）`)
} else {
  ElMessage.warning(d.tip || '已生成但未入库：题库中已有同类题被复用')
}
```

alert 同步分色：`saved>0` → success「已保存至题库」；`saved=0` → warning「均未入库」+ 后端 `tip`。

**顺带修**：切换年级/学科时清空上一批结果。旧行为下改完条件，表格里还挂着上一批题，会让人误以为「这批是按新条件生成的」。

---

## 3. 排查中发现的其他同类缺陷（已一并修复）

同一个页面有 5 处「年级 → 学科」联动，逐一对比后发现 3 处不一致：

| 位置 | 问题 | 后果 | 状态 |
|---|---|---|---|
| 筛选区（query） | 精确列表 + 切换清空 | ✅ 原本正确 | — |
| 新增/编辑弹窗（form） | 精确列表 + 切换清空 | ⚠️ 但编辑时若 `subject_id` 不属于当前年级无防御 | 已加防御 |
| **批量导入（importForm）** | **去重列表 + 年级切换无 @change** | **导入的题目挂到错误年级的学科上（静默错配）** | 已修 |
| **AI 出题（aiForm）** | 去重列表 + id 映射 | 显示数字（缺陷 A） | 已修 |
| 知识点弹窗（kpForm） | 精确列表 + 切换清空 | ✅ 原本正确 | — |

**导入表单的静默错配**比显示数字更危险：界面显示「语文」，提交的却是代表 id（一年级语文），导入的七年级题目被挂到一年级。没有报错，只有事后统计时才会发现。

**第四处修复：筛选切换不重置页码**

```js
function onGradeChange() {
  query.subject_id = null
  query.knowledge_point_id = null
  query.page = 1        // ← 新增
  ...
}
```

原来在第 3 页切换年级后点「查询」，会请求第 3 页，而新条件下只有 1 页 → 空列表，用户以为「这个年级没有题」。

---

## 4. 验证

### 方法
- **静态**：5 处联动点逐一对比「数据源 id 语义 / @change 处理 / disabled 条件」
- **动态**：Playwright + 系统 Chrome（`playwright-core`，不下载浏览器），真实点击操作
- **反向验证**：`git checkout` 回退到修复前版本，用同一组断言确认能复现

### 结果（15/15）

```
PASS  API 登录拿到令牌
PASS  已进入题库页
PASS  对话框已打开
PASS  选年级后回显正确                      实际="一年级"
PASS  选一年级+语文：学科显示文本            实际="语文"
PASS  切到七年级：学科不应显示数字            实际="先选年级"
PASS  切到七年级：学科应被清空               实际="先选年级"
PASS  选七年级+数学：学科显示文本            实际="数学"
PASS  生成成功后出现「完成」
PASS  生成成功后主按钮变「再生成一批」
PASS  生成成功后不再显示「生成并入库」
PASS  saved>0：提示已保存                    已生成 2 题，其中 2 题已保存至题库（草稿状态）
PASS  saved=0：不得声称已保存                 已生成 1 题，但均未入库
PASS  saved=0：应提示未入库                   已生成 1 题，但均未入库
PASS  无 JS 运行时错误
```

`npm run build` 通过（10.5s）。

> 说明：`saved>0` / `saved=0` 两条分支通过 `page.route` 拦截接口返回真实 mock，不依赖大模型。

---

## 5. 未修但建议关注

| 项 | 说明 | 建议 |
|---|---|---|
| AI 出题成功不自动关窗 | 让用户先看结果，是有意设计 | 保持 |
| `createVariants` 逐条创建 | N 条变式 = N 次串行请求，5 条以上明显变慢 | 后端补批量接口，或前端并发（限 3） |
| 导入无覆盖策略选项 | 同名/同题干重复导入的行为由后端决定，界面未暴露 | 确认后端语义后补「跳过/覆盖」开关 |
| 筛选变更不自动刷新 | 当前需点「查询」（已重置页码） | 若希望即时，可给 `@change` 加防抖 `search()` |

## 6. 改动文件

```
frontend/src/views/teacher/QuestionBank.vue
```

- AI 对话框：年级/学科换序、按年级精确加载、删除 `syncAiSubjectByGrade`
- AI footer：按结果切换「完成 / 再生成一批 / 生成并入库」
- AI alert：按 `saved` 分色 + 真实文案
- 新增 `aiSubjects` / `importSubjects` / `aiResultSaved` / `aiResultTip` / `resetAiResult` / `onAiSubjectChange` / `loadAiSubjects` / `loadImportSubjects` / `onImportGradeChange`
- 删除无用的 `subjects`（去重列表）及其启动请求
- `openDialog` 改为 async + subject 存在性校验
- `onGradeChange` / `onFilterSubjectChange` 重置页码
