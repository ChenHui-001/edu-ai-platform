<template>
  <div class="page-container">
    <!-- 顶部：标题 + 统计 + 操作 -->
    <div class="page-header pm-header">
      <div class="pm-title-wrap">
        <h2 class="page-title">试卷管理</h2>
        <div class="pm-stats" v-loading="statsLoading">
          <div v-for="c in statCards" :key="c.label" class="stat-card pm-stat">
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </div>
      </div>
      <div class="pm-actions">
        <el-button :icon="Refresh" @click="refreshAll">刷新</el-button>
        <el-button v-if="canWrite || canAI" :icon="DocumentCopy" @click="openAI">AI 智能组卷</el-button>
        <el-button v-if="canWrite" type="primary" :icon="Plus" @click="openDialog()">手动组卷</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:120px"
                     @change="onFilterGradeChange">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="query.subject_id" placeholder="先选年级" clearable
                     :disabled="!query.grade_id" style="width:120px">
            <el-option v-for="s in filterSubjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="query.source" placeholder="全部" clearable style="width:110px">
            <el-option label="手动组卷" value="manual" />
            <el-option label="AI 组卷" value="ai" />
          </el-select>
        </el-form-item>
        <el-form-item label="共享状态">
          <el-select v-model="query.shared" placeholder="全部" clearable style="width:110px">
            <el-option label="已共享" :value="true" />
            <el-option label="未共享" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="试卷名称" clearable style="width:170px"
                    @keyup.enter="search" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="search">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <div v-if="canWrite" class="batch-bar">
        <span class="muted">已选 {{ selection.length }} 份</span>
        <el-button size="small" :disabled="!selection.length" @click="batchCopy">批量复制</el-button>
        <el-button v-if="canShare" size="small" :disabled="!selection.length"
                   @click="openBatchShare">批量共享</el-button>
        <el-button size="small" type="danger" plain :disabled="!selection.length"
                   @click="batchDelete">批量删除</el-button>
      </div>

      <el-table v-loading="loading" :data="list" row-key="id" border stripe
                @selection-change="onSelectionChange">
        <el-table-column type="selection" width="44" />
        <el-table-column label="试卷名称" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" :underline="false" @click="openDetail(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="年级" width="100">
          <template #default="{ row }">{{ row.grade_name || gradeName(row.grade_id) }}</template>
        </el-table-column>
        <el-table-column label="学科" width="100">
          <template #default="{ row }">{{ row.subject_name || subjectName(row.subject_id) }}</template>
        </el-table-column>
        <el-table-column prop="item_count" label="题量" width="70" align="center" />
        <el-table-column prop="total_score" label="总分" width="80" align="center" />
        <el-table-column prop="duration" label="时长(分)" width="90" align="center" />
        <el-table-column label="来源" width="95" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.source === 'ai' ? 'success' : 'info'">
              {{ row.source === 'ai' ? 'AI 组卷' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="共享" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_shared ? 'warning' : 'info'" effect="plain">
              {{ row.is_shared ? '已共享' : '未共享' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="创建者" width="100" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="160" show-overflow-tooltip />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <div class="row-ops" @click.stop>
              <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
              <el-button v-if="canWrite" link type="primary" size="small"
                         @click="openDialog(row)">编辑</el-button>
              <el-button v-if="canWrite" link type="primary" size="small"
                         @click="copyPaper(row)">复制</el-button>
              <el-button v-if="canShare" link type="primary" size="small"
                         @click="openShare(row)">共享</el-button>
              <el-dropdown v-if="canExport" trigger="click" @command="(fmt) => exportPaper(row, fmt)">
                <el-button link type="warning" size="small">导出</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="excel">Excel</el-dropdown-item>
                    <el-dropdown-item command="word">Word</el-dropdown-item>
                    <el-dropdown-item command="pdf">PDF</el-dropdown-item>
                    <el-dropdown-item command="html">HTML</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button v-if="canWrite" link type="danger" size="small"
                         @click="removePaper(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page" v-model:page-size="query.page_size"
        :total="total" :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pm-pagination"
        @current-change="load" @size-change="search"
      />
    </el-card>

    <!-- 试卷详情抽屉 -->
    <el-drawer v-model="detailVisible" title="试卷详情" size="780px" destroy-on-close>
      <div v-loading="detailLoading">
        <template v-if="detailPaper">
          <div class="detail-head">
            <h3 class="detail-title">{{ detailPaper.name }}</h3>
            <div class="detail-tags">
              <el-tag size="small" :type="detailPaper.source === 'ai' ? 'success' : 'info'">
                {{ detailPaper.source === 'ai' ? 'AI 组卷' : '手动组卷' }}
              </el-tag>
              <el-tag v-if="detailPaper.is_shared" size="small" type="warning" effect="plain">已共享</el-tag>
              <span class="muted">
                {{ detailPaper.grade_name || gradeName(detailPaper.grade_id) }} ·
                {{ detailPaper.subject_name || subjectName(detailPaper.subject_id) }} ·
                总分 {{ detailPaper.total_score }} · 时长 {{ detailPaper.duration }} 分钟 ·
                共 {{ detailItems.length }} 题
              </span>
            </div>
          </div>

          <div class="ai-toolbar" v-if="canAI">
            <el-button size="small" :icon="MagicStick" :loading="aiAnalyzeLoading"
                       @click="runAiAnalyze">AI 分析</el-button>
            <el-button size="small" :icon="MagicStick" :loading="aiRecommendLoading"
                       @click="runAiRecommend">AI 推荐题目</el-button>
            <span class="muted">规则分析总会执行；无大模型时标记 is_fallback</span>
          </div>

          <!-- AI 分析结果 -->
          <div v-if="aiAnalysis" class="ai-panel">
            <el-alert v-if="aiAnalysis.is_fallback" type="warning" :closable="false" show-icon
                      class="mb8"
                      title="当前无可用大模型，以下为规则引擎分析结果（is_fallback=true）" />
            <el-alert v-else type="success" :closable="false" show-icon class="mb8"
                      title="AI 分析完成" />
            <div class="ai-metric-row">
              <span class="ai-metric-label">难度分布</span>
              <el-tag v-for="m in metricEntries(aiAnalysis.analysis?.difficulty_ratio)" :key="'d-' + m.label"
                      size="small" effect="plain">{{ m.label }}：{{ ratioText(m.value) }}</el-tag>
              <span v-if="!metricEntries(aiAnalysis.analysis?.difficulty_ratio).length" class="muted">-</span>
            </div>
            <div class="ai-metric-row">
              <span class="ai-metric-label">题型分布</span>
              <el-tag v-for="m in metricEntries(aiAnalysis.analysis?.type_distribution)" :key="'t-' + m.label"
                      size="small" type="success" effect="plain">{{ m.label }}：{{ stringifyMetric(m.value) }}</el-tag>
              <span v-if="!metricEntries(aiAnalysis.analysis?.type_distribution).length" class="muted">-</span>
            </div>
            <div class="ai-metric-row">
              <span class="ai-metric-label">知识点覆盖</span>
              <template v-if="aiCoverage.length">
                <el-tag v-for="c in aiCoverage" :key="c.knowledge_point_id ?? c.name"
                        size="small" type="info" effect="plain">
                  {{ c.name || ('#' + c.knowledge_point_id) }}：{{ c.count }} 题
                </el-tag>
              </template>
              <span v-else class="muted">-</span>
            </div>
            <div v-if="aiIssueList.length" class="ai-metric-row">
              <span class="ai-metric-label">问题</span>
              <div class="ai-issues">
                <div v-for="(issue, i) in aiIssueList" :key="i" class="ai-issue">
                  <el-tag size="small" :type="issueType(issue)">{{ issueLabel(issue) }}</el-tag>
                  <span>{{ issueText(issue) }}</span>
                </div>
              </div>
            </div>
            <div v-if="aiSuggestions.length" class="ai-metric-row">
              <span class="ai-metric-label">建议</span>
              <ul class="ai-suggestions">
                <li v-for="(s, i) in aiSuggestions" :key="i">{{ suggestText(s) }}</li>
              </ul>
            </div>
          </div>

          <!-- AI 推荐题目 -->
          <div v-if="aiRecommendItems.length" class="ai-panel">
            <el-alert v-if="aiRecommendFallback" type="warning" :closable="false" show-icon
                      class="mb8"
                      title="当前无可用大模型，推荐由规则引擎生成（is_fallback=true）" />
            <div class="ai-result-head">
              <b>AI 推荐题目</b>
              <span class="muted">共 {{ aiRecommendItems.length }} 题，已选 {{ aiRecommendSelected.length }} 题</span>
            </div>
            <el-table ref="aiRecommendTableRef" :data="aiRecommendItems" size="small" border
                      max-height="260" @selection-change="onAiRecommendSelectionChange">
              <el-table-column type="selection" width="42" />
              <el-table-column label="题型" width="90">
                <template #default="{ row }">{{ typeLabel(row.type) }}</template>
              </el-table-column>
              <el-table-column label="难度" width="80">
                <template #default="{ row }">
                  <el-tag size="small" :type="diffType(row.difficulty)">
                    {{ difficultyLabel(row.difficulty) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="score" label="分值" width="70" align="center" />
              <el-table-column label="题干" min-width="260">
                <template #default="{ row }">{{ stripHtml(row.stem).slice(0, 70) }}</template>
              </el-table-column>
              <el-table-column label="推荐理由" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">{{ row.reason || '-' }}</template>
              </el-table-column>
            </el-table>
            <div class="mt8">
              <el-button type="primary" size="small" :loading="aiApplyLoading"
                         :disabled="!canWrite || !aiRecommendSelected.length"
                         @click="applyRecommendations">
                加入选中（{{ aiRecommendSelected.length }}）
              </el-button>
              <span v-if="!canWrite" class="muted ml8">只读用户不能修改试卷</span>
            </div>
          </div>

          <!-- 题目列表 -->
          <div class="detail-items">
            <div v-for="(it, idx) in detailItems" :key="it.paper_item_id || it.question_id || idx" class="detail-item">
              <div class="item-head">
                <b>{{ idx + 1 }}.</b>
                <el-tag size="small" effect="plain">{{ it.type_label || typeLabel(it.type) }}</el-tag>
                <el-tag size="small" :type="diffType(it.difficulty)">{{ difficultyLabel(it.difficulty) }}</el-tag>
                <el-tag size="small" type="info" effect="plain">{{ it.score }} 分</el-tag>
                <el-tag v-if="it.knowledge_point_name" size="small" type="info" effect="plain">
                  {{ it.knowledge_point_name }}
                </el-tag>
              </div>
              <div class="item-stem" v-html="safeStem(it.stem)"></div>
              <div v-if="it.options?.length" class="item-options">
                <span v-for="o in it.options" :key="o.key" class="item-option">{{ o.key }}. {{ o.text }}</span>
              </div>
              <div class="item-meta muted">答案：{{ formatAnswer(it.answer) }}</div>
              <div v-if="it.analysis" class="item-meta muted">解析：{{ stripHtml(it.analysis).slice(0, 200) }}</div>
            </div>
          </div>
        </template>
        <el-empty v-else-if="!detailLoading" description="试卷详情加载失败" :image-size="70" />
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button v-if="canWrite && detailPaper" type="primary"
                   @click="openDialog(detailPaper)">编辑试卷</el-button>
      </template>
    </el-drawer>

    <!-- 手动组卷 / 编辑 -->
    <el-dialog v-model="dlg" :title="form.id ? '编辑试卷' : '手动组卷'" width="920px" top="5vh">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="试卷名称" required>
              <el-input v-model="form.name" maxlength="128" show-word-limit
                        placeholder="如：七年级数学期中卷" />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="时长(分)">
              <el-input-number v-model="form.duration" :min="1" :max="300" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="年级" required>
              <el-select v-model="form.grade_id" style="width:100%" @change="onFormGradeChange">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="学科" required>
              <el-select v-model="form.subject_id" :disabled="!form.grade_id"
                         style="width:100%" @change="loadPickerQuestions">
                <el-option v-for="s in formSubjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>

        <el-divider content-position="left">从题库选题</el-divider>
        <div class="picker-filters">
          <el-select v-model="qFilter.qtype" clearable placeholder="题型" size="small"
                     style="width:120px" @change="loadPickerQuestions">
            <el-option v-for="(label, key) in TYPE_LABEL" :key="key" :label="label" :value="key" />
          </el-select>
          <el-select v-model="qFilter.difficulty" clearable placeholder="难度" size="small"
                     style="width:110px" @change="loadPickerQuestions">
            <el-option v-for="(label, val) in DIFF" :key="val" :label="label" :value="val" />
          </el-select>
          <el-input v-model="qFilter.keyword" placeholder="题干关键字，回车搜索" clearable
                    size="small" style="width:200px" @keyup.enter="loadPickerQuestions"
                    @clear="loadPickerQuestions" />
          <el-button size="small" :icon="Refresh" :loading="pickerLoading"
                     @click="loadPickerQuestions">刷新题库</el-button>
          <span class="muted">题库按试卷年级/学科过滤；先选择题型再勾选</span>
        </div>

        <el-table ref="pickTableRef" v-loading="pickerLoading" :data="pickerQuestions"
                  size="small" border max-height="240" class="mt8"
                  @selection-change="onPickChange">
          <el-table-column type="selection" width="42" />
          <el-table-column label="题型" width="90">
            <template #default="{ row }">{{ row.type_label || typeLabel(row.type) }}</template>
          </el-table-column>
          <el-table-column label="难度" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="diffType(row.difficulty)">
                {{ difficultyLabel(row.difficulty) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="score" label="分值" width="70" align="center" />
          <el-table-column label="题干" min-width="260">
            <template #default="{ row }">{{ stripHtml(row.stem).slice(0, 60) }}</template>
          </el-table-column>
          <el-table-column label="知识点" width="130" show-overflow-tooltip>
            <template #default="{ row }">{{ row.knowledge_point_name || '未关联' }}</template>
          </el-table-column>
        </el-table>
        <div class="mt8">
          <el-button size="small" type="primary" :disabled="!pickSelection.length"
                     @click="addPicked">加入所选（{{ pickSelection.length }}）</el-button>
          <span class="muted ml8">已选 {{ paperItems.length }} 题，总分 {{ totalPaperScore }} 分</span>
        </div>

        <el-divider content-position="left">已选题目（{{ paperItems.length }}）</el-divider>
        <el-table :data="paperItems" size="small" border max-height="260" class="mt8">
          <el-table-column label="序号" width="60" align="center">
            <template #default="{ $index }">{{ $index + 1 }}</template>
          </el-table-column>
          <el-table-column label="题型" width="90">
            <template #default="{ row }">{{ row.type_label || typeLabel(row.type) }}</template>
          </el-table-column>
          <el-table-column label="难度" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="diffType(row.difficulty)">
                {{ difficultyLabel(row.difficulty) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="分值" width="110" align="center">
            <template #default="{ row }">
              <el-input-number v-model="row.score" :min="0" :max="1000" :precision="1"
                               size="small" controls-position="right" style="width:92px" />
            </template>
          </el-table-column>
          <el-table-column label="题干" min-width="260">
            <template #default="{ row }">{{ stripHtml(row.stem).slice(0, 60) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" align="center">
            <template #default="{ $index }">
              <el-button link type="primary" size="small" :disabled="$index === 0"
                         @click="moveItem($index, -1)">上移</el-button>
              <el-button link type="primary" size="small"
                         :disabled="$index === paperItems.length - 1"
                         @click="moveItem($index, 1)">下移</el-button>
              <el-button link type="danger" size="small"
                         @click="removePaperItem($index)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!paperItems.length" description="还没有选题，先从上方题库勾选并加入" :image-size="60" />
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">
          {{ form.id ? '保存修改' : '创建试卷' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- AI 智能组卷 -->
    <el-dialog v-model="aiDlg" title="AI 智能组卷" width="640px">
      <el-alert type="info" :closable="false" class="mb12"
                title="用自然语言描述需求，AI 自动解析并组卷。示例：生成七年级数学一元一次方程的试卷，10 题，难度中等偏难" />
      <el-form :model="aiForm" label-width="90px">
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="学科" required>
              <el-select v-model="aiForm.subject_id" style="width:100%" @change="onAiSubjectChange">
                <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id">
                  <span>{{ s.name }}</span>
                  <span v-if="s.grade_count > 1" class="ai-grade-count">{{ s.grade_count }} 个年级</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年级">
              <el-select v-model="aiForm.grade_id" clearable style="width:100%"
                         @change="onAiGradeChange">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="需求描述">
          <el-input v-model="aiReq" type="textarea" :rows="3"
                    placeholder="如：生成八年级物理期中试卷，选择填空，20 题，60 分钟" />
        </el-form-item>
        <el-form-item label="快捷模板">
          <el-button v-for="t in templates" :key="t" size="small" class="mr4"
                     @click="aiReq = t">{{ t.slice(0, 12) }}…</el-button>
        </el-form-item>
      </el-form>

      <div v-if="aiResult" class="ai-panel">
        <el-divider content-position="left">
          <b>组卷结果</b>
          <el-tag size="small" class="ml4" :type="aiResult.paper?.id ? 'success' : 'warning'">
            {{ aiResult.paper?.id ? '已入库' : '仅预览（未入库）' }}
          </el-tag>
        </el-divider>
        <p><b>试卷名称：</b>{{ aiResult.paper?.name }}</p>
        <p><b>题目数量：</b>{{ aiResult.paper?.item_count ?? '-' }}</p>
        <p><b>总分：</b>{{ aiResult.paper?.total_score ?? '-' }}</p>
        <p v-if="aiResult.difficulty_report || aiResult.analysis">
          <b>难度分析：</b>{{ aiResult.analysis || aiResult.difficulty_report }}
        </p>
        <p v-if="aiResult.knowledge_coverage"><b>知识点覆盖：</b>{{ aiResult.knowledge_coverage }}</p>
        <p v-if="aiResult.paper?.id" class="mt8">
          <el-button type="success" size="small" @click="useResult">使用该试卷</el-button>
        </p>
      </div>

      <template #footer>
        <el-button @click="aiDlg = false">关闭</el-button>
        <el-button type="primary" :loading="aiLoading" :icon="MagicStick" @click="runAI">开始组卷</el-button>
      </template>
    </el-dialog>

    <!-- 共享 -->
    <el-dialog v-model="shareDlg" title="共享试卷" width="500px">
      <el-form label-width="90px">
        <el-form-item label="共享对象">
          <el-select v-model="shareTargets" multiple filterable style="width:100%"
                     placeholder="选择教师（可多选）">
            <el-option v-for="t in teachers" :key="t.id"
                       :label="`${t.real_name || t.username}（${t.username}）`" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="shareIds.length === 1" label="备注">
          <el-input v-model="shareRemark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <div class="muted">
        将共享 {{ shareIds.length }} 份试卷{{ shareIds.length === 1 ? `：「${shareTitle}」` : '' }}；
        批量共享时非本人创建的试卷会进入 skipped
      </div>
      <template #footer>
        <el-button @click="shareDlg = false">取消</el-button>
        <el-button type="primary" :loading="sharingDialogBusy" @click="doShare">确认共享</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, DocumentCopy, MagicStick } from '@element-plus/icons-vue'
import { questionApi, eduApi, agentApi } from '@/api'
import { useUserStore } from '@/store/user'
import TYPE_LABEL from '@/constants/question'
import { sanitizeHtml } from '@/utils/sanitize'
import { downloadBlob } from '@/utils/download'

// 题干由教师/AI 录入，后端不做净化就落库，直接 v-html 会执行其中的脚本。
function safeStem(s) { return sanitizeHtml(s) }

const userStore = useUserStore()
const { can } = userStore
const canWrite = computed(() => can('paper:write'))
const canShare = computed(() => can('paper:share'))
const canExport = computed(() => can('paper:export'))
const canAI = computed(() => can('paper:ai'))

const DIFF = { easy: '简单', medium: '中等', hard: '困难' }

function diffType(d) { return { easy: 'success', medium: 'warning', hard: 'danger' }[d] || 'info' }
function difficultyLabel(v) { return DIFF[v] || v || '-' }
function typeLabel(t) { return TYPE_LABEL[t] || (t ? `其他题型(${t})` : '-') }
function stripHtml(s) { return String(s || '').replace(/<[^>]*>/g, '') }
function parseJson(v) {
  if (!v) return null
  if (Array.isArray(v)) return v
  try { return JSON.parse(v) } catch { return null }
}
function formatAnswer(answer) {
  const a = parseJson(answer) ?? answer
  if (Array.isArray(a)) return a.join('、')
  if (a === null || a === undefined || a === '') return '未填写'
  return String(a)
}
function stringifyMetric(v) {
  if (v === null || v === undefined || v === '') return '-'
  if (Array.isArray(v)) return v.join(' / ')
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}
// 难度/题型分布里的键是英文枚举，展示时转中文
function metricLabel(key) { return TYPE_LABEL[key] || DIFF[key] || key }
// 难度占比 0~1 → 百分比
function ratioText(v) {
  const n = Number(v)
  return Number.isFinite(n) && n >= 0 && n <= 1 ? `${(n * 100).toFixed(0)}%` : stringifyMetric(v)
}
function metricEntries(value) {
  if (!value) return []
  if (Array.isArray(value)) {
    return value.map((x, i) => ({
      label: x?.name || x?.key || `#${i + 1}`,
      value: x?.ratio ?? x?.value ?? x?.count ?? x
    }))
  }
  if (typeof value === 'object') {
    return Object.entries(value).map(([k, v]) => ({ label: metricLabel(k), value: v }))
  }
  return [{ label: '值', value }]
}
function issueType(issue) {
  const s = issue?.severity
  return { error: 'danger', warning: 'warning', info: 'info' }[s] || 'info'
}
function issueLabel(issue) {
  const s = issue?.severity
  return { error: '错误', warning: '警告', info: '提示' }[s] || '提示'
}
function issueText(issue) {
  if (typeof issue === 'string') return issue
  return issue?.message || issue?.code || stringifyMetric(issue)
}
function suggestText(s) {
  if (typeof s === 'string') return s
  return s?.message || s?.text || s?.content || stringifyMetric(s)
}

// ---------------- 基础数据 ----------------
const grades = ref([])
// AI 智能组卷用按名称去重的学科（带 same_name_ids 映射精确 subject_id）
const subjects = ref([])
const filterSubjects = ref([])
const formSubjects = ref([])
const teachers = ref([])

const query = reactive({
  page: 1, page_size: 20,
  grade_id: null, subject_id: null, source: null, shared: null, keyword: ''
})

const list = ref([])
const total = ref(0)
const loading = ref(false)
const selection = ref([])
const stats = ref({})
const statsLoading = ref(false)

function pickStat(...keys) {
  const d = stats.value || {}
  for (const key of keys) {
    const v = d[key]
    if (v !== undefined && v !== null) return v
  }
  return '-'
}

const statCards = computed(() => [
  { label: '试卷总数', value: pickStat('total', 'paper_total') },
  { label: '总题量', value: pickStat('item_total', 'total_items', 'item_count', 'question_total') },
  { label: '平均分', value: pickStat('avg_score', 'average_score', 'avg_total_score') },
  { label: '共享卷', value: pickStat('shared_count', 'shared', 'shared_papers') }
])

function gradeName(id) { return grades.value.find(g => g.id === id)?.name || '-' }
function subjectName(id) { return subjects.value.find(s => s.id === id)?.name || '-' }

function buildFilterParams() {
  const params = {}
  if (query.grade_id) params.grade_id = query.grade_id
  if (query.subject_id) params.subject_id = query.subject_id
  if (query.source) params.source = query.source
  if (query.shared !== null && query.shared !== '') params.shared = query.shared
  const keyword = query.keyword.trim()
  if (keyword) params.keyword = keyword
  return params
}

function buildListParams() {
  return { ...buildFilterParams(), page: query.page, page_size: query.page_size }
}

async function loadStats() {
  statsLoading.value = true
  try {
    const res = await questionApi.paperStats(buildFilterParams())
    stats.value = res.data || {}
  } catch {
    // 统计接口未就绪时保持占位，不阻断列表
  } finally {
    statsLoading.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const res = await questionApi.papers(buildListParams())
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
    selection.value = []
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  await Promise.all([load(), loadStats()])
}

function search() { query.page = 1; refreshAll() }

function reset() {
  Object.assign(query, {
    page: 1, grade_id: null, subject_id: null, source: null, shared: null, keyword: ''
  })
  filterSubjects.value = []
  refreshAll()
}

async function loadFilterSubjects(gradeId) {
  if (!gradeId) { filterSubjects.value = []; return }
  try {
    const res = await eduApi.subjects({ grade_id: gradeId })
    filterSubjects.value = res.data || []
  } catch { filterSubjects.value = [] }
}

function onFilterGradeChange() {
  query.subject_id = null
  loadFilterSubjects(query.grade_id)
}

function onSelectionChange(val) { selection.value = val || [] }

// ---------------- 导出 ----------------
const EXPORT_EXT = { excel: 'xlsx', word: 'doc', pdf: 'pdf', html: 'html' }
async function exportPaper(row, fmt = 'excel') {
  const ext = EXPORT_EXT[fmt] || 'xlsx'
  await downloadBlob(questionApi.exportPaper(row.id, fmt), `试卷-${row.name}.${ext}`)
}

// ---------------- 详情抽屉 ----------------
const detailVisible = ref(false)
const detailPaper = ref(null)
const detailItems = ref([])
const detailLoading = ref(false)
const aiAnalyzeLoading = ref(false)
const aiAnalysis = ref(null)
const aiRecommendLoading = ref(false)
const aiRecommendItems = ref([])
const aiRecommendSelected = ref([])
const aiRecommendFallback = ref(false)
const aiRecommendTableRef = ref(null)
const aiApplyLoading = ref(false)

const aiIssueList = computed(() => {
  const list2 = aiAnalysis.value?.analysis?.issues
  return Array.isArray(list2) ? list2 : []
})
const aiSuggestions = computed(() => {
  const list2 = aiAnalysis.value?.suggestions
  return Array.isArray(list2) ? list2 : []
})
// 知识点覆盖：[{knowledge_point_id,name,count,ratio}]
const aiCoverage = computed(() => {
  const list2 = aiAnalysis.value?.analysis?.knowledge_coverage
  return Array.isArray(list2) ? list2 : []
})

async function openDetail(row) {
  detailVisible.value = true
  detailPaper.value = row
  detailItems.value = []
  aiAnalysis.value = null
  aiRecommendItems.value = []
  aiRecommendSelected.value = []
  aiRecommendFallback.value = false
  detailLoading.value = true
  try {
    const res = await questionApi.paperDetail(row.id)
    const d = res.data || {}
    detailPaper.value = d
    detailItems.value = d.items || []
  } catch {
    detailPaper.value = row
    detailItems.value = []
  } finally {
    detailLoading.value = false
  }
}

async function runAiAnalyze() {
  if (!detailPaper.value?.id) return
  aiAnalyzeLoading.value = true
  try {
    const res = await questionApi.paperAiAnalyze(detailPaper.value.id)
    aiAnalysis.value = res.data || {}
  } finally {
    aiAnalyzeLoading.value = false
  }
}

async function runAiRecommend() {
  if (!detailPaper.value?.id) return
  aiRecommendLoading.value = true
  try {
    const res = await questionApi.paperAiRecommend(detailPaper.value.id)
    const d = res.data || {}
    aiRecommendItems.value = Array.isArray(d.items) ? d.items : []
    aiRecommendFallback.value = d.is_fallback === true
    aiRecommendSelected.value = []
    await nextTick()
    selectAllRows(aiRecommendTableRef.value, aiRecommendItems.value)
    if (!aiRecommendItems.value.length) ElMessage.info('暂无推荐题目')
  } finally {
    aiRecommendLoading.value = false
  }
}

function selectAllRows(table, rows) {
  if (!table || !rows?.length) return
  table.clearSelection?.()
  rows.forEach(r => table.toggleRowSelection(r, true))
}

function onAiRecommendSelectionChange(rows) { aiRecommendSelected.value = rows || [] }

async function applyRecommendations() {
  if (!canWrite.value) return ElMessage.warning('只读用户不能修改试卷')
  const paper = detailPaper.value
  if (!paper?.id) return
  const selected = aiRecommendSelected.value
  if (!selected.length) return ElMessage.warning('请勾选要加入的推荐题目')
  const baseItems = detailItems.value.map(it => ({
    question_id: it.question_id,
    score: it.score,
    ...(it.section_name ? { section_name: it.section_name } : {})
  }))
  for (const r of selected) {
    if (!r?.question_id || baseItems.some(x => x.question_id === r.question_id)) continue
    baseItems.push({ question_id: r.question_id, score: r.score ?? 5 })
  }
  if (baseItems.length === detailItems.value.length) {
    return ElMessage.info('所选推荐题目已在试卷中')
  }
  aiApplyLoading.value = true
  try {
    await questionApi.updatePaper(paper.id, { items: baseItems })
    ElMessage.success(`已加入 ${baseItems.length - detailItems.value.length} 道推荐题目`)
    await openDetail(paper)
    await refreshAll()
  } finally {
    aiApplyLoading.value = false
  }
}

// ---------------- 手动组卷 / 编辑 ----------------
const dlg = ref(false)
const saving = ref(false)
const form = reactive({
  id: null, name: '', grade_id: null, subject_id: null,
  duration: 60, description: ''
})
const paperItems = ref([])
const qFilter = reactive({ qtype: '', difficulty: '', keyword: '' })
const pickerQuestions = ref([])
const pickerLoading = ref(false)
const pickSelection = ref([])
const pickTableRef = ref(null)

const totalPaperScore = computed(() =>
  paperItems.value.reduce((sum, it) => sum + (Number(it.score) || 0), 0).toFixed(1))

async function loadFormSubjects(gradeId) {
  if (!gradeId) { formSubjects.value = []; return }
  const res = await eduApi.subjects({ grade_id: gradeId })
  formSubjects.value = res.data || []
}

async function loadPickerQuestions() {
  if (!form.grade_id || !form.subject_id) { pickerQuestions.value = []; return }
  pickerLoading.value = true
  pickSelection.value = []
  try {
    const res = await questionApi.list({
      grade_id: form.grade_id,
      subject_id: form.subject_id,
      qtype: qFilter.qtype || undefined,
      difficulty: qFilter.difficulty || undefined,
      keyword: qFilter.keyword || undefined,
      status: 'published',
      page_size: 200
    })
    pickerQuestions.value = res.data?.items || []
    // 恢复已选题目的勾选状态
    await nextTick()
    pickerQuestions.value.forEach(q => {
      if (paperItems.value.some(p => p.question_id === q.id)) {
        pickTableRef.value?.toggleRowSelection(q, true)
      }
    })
  } finally {
    pickerLoading.value = false
  }
}

function onPickChange(rows) { pickSelection.value = rows || [] }

function addPicked() {
  const fresh = pickSelection.value.filter(row => !paperItems.value.some(it => it.question_id === row.id))
  if (!fresh.length) return ElMessage.info('所选题目均已加入')
  paperItems.value.push(...fresh.map(row => ({
    question_id: row.id,
    score: row.score ?? 5,
    stem: row.stem,
    type: row.type,
    type_label: row.type_label,
    difficulty: row.difficulty,
    knowledge_point_name: row.knowledge_point_name
  })))
  ElMessage.success(`已加入 ${fresh.length} 题`)
  pickTableRef.value?.clearSelection()
}

function removePaperItem(index) { paperItems.value.splice(index, 1) }

function moveItem(index, delta) {
  const target = index + delta
  if (target < 0 || target >= paperItems.value.length) return
  const items = paperItems.value
  const [moved] = items.splice(index, 1)
  items.splice(target, 0, moved)
}

function onFormGradeChange() {
  form.subject_id = null
  formSubjects.value = []
  paperItems.value = []
  loadFormSubjects(form.grade_id)
}

async function openDialog(row) {
  dlg.value = true
  qFilter.qtype = ''
  qFilter.difficulty = ''
  qFilter.keyword = ''
  pickerQuestions.value = []
  pickSelection.value = []
  paperItems.value = []
  if (row?.id) {
    saving.value = false
    Object.assign(form, {
      id: row.id, name: row.name || '', grade_id: row.grade_id ?? null,
      subject_id: row.subject_id ?? null, duration: row.duration ?? 60,
      description: row.description || ''
    })
    await loadFormSubjects(form.grade_id)
    detailLoading.value = true
    try {
      const res = await questionApi.paperDetail(row.id)
      const d = res.data || {}
      detailPaper.value = d
      paperItems.value = (d.items || []).map(it => ({
        question_id: it.question_id,
        score: it.score ?? 5,
        stem: it.stem,
        type: it.type,
        type_label: it.type_label,
        difficulty: it.difficulty,
        knowledge_point_name: it.knowledge_point_name
      }))
    } catch {
      // 详情失败时保留列表行信息，仍可保存基本信息
      paperItems.value = []
    } finally {
      detailLoading.value = false
    }
  } else {
    Object.assign(form, {
      id: null, name: '', grade_id: query.grade_id, subject_id: query.subject_id,
      duration: 60, description: ''
    })
    await loadFormSubjects(form.grade_id)
  }
  if (form.grade_id) await loadPickerQuestions()
}

async function save() {
  if (!form.name.trim()) return ElMessage.warning('请输入试卷名称')
  if (!form.grade_id || !form.subject_id) return ElMessage.warning('请选择年级与学科')
  if (!paperItems.value.length) return ElMessage.warning('请至少选择一道题目')
  if (!form.duration) return ElMessage.warning('请填写考试时长')
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      grade_id: form.grade_id,
      subject_id: form.subject_id,
      duration: form.duration,
      description: form.description,
      items: paperItems.value.map(it => ({
        question_id: it.question_id,
        score: Number(it.score) || 0
      }))
    }
    if (form.id) await questionApi.updatePaper(form.id, payload)
    else await questionApi.createPaper(payload)
    ElMessage.success(form.id ? '试卷已更新' : '试卷创建成功')
    dlg.value = false
    await refreshAll()
    if (detailVisible.value && detailPaper.value?.id === form.id) {
      await openDetail({ id: form.id, ...detailPaper.value })
    }
  } finally {
    saving.value = false
  }
}

// ---------------- 单行操作 ----------------
async function copyPaper(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入新试卷名称', '复制试卷',
      { inputValue: `${row.name} - 副本` })
    await questionApi.copyPaper(row.id, { name: value })
    ElMessage.success('复制成功')
    await refreshAll()
  } catch {
    // 用户取消 / 请求失败由拦截器提示
  }
}

async function removePaper(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除试卷「${row.name}」？被作业/考试引用的试卷会被拒绝删除。`,
      '删除确认', { type: 'warning', confirmButtonText: '确认删除' })
  } catch { return }
  await questionApi.removePaper(row.id)
  ElMessage.success('已删除')
  if (detailPaper.value?.id === row.id) detailVisible.value = false
  await refreshAll()
}

// ---------------- 批量操作 ----------------
const batchRunning = ref(false)

function batchIds() { return selection.value.map(p => p.id) }

function ensureSelection() {
  if (!selection.value.length) {
    ElMessage.warning('请先勾选试卷')
    return false
  }
  return true
}

function reportBatchResult(data, prefix) {
  const d = data || {}
  const done = (d.done || []).length
  const skipped = d.skipped || []
  if (skipped.length) {
    const reasons = skipped.slice(0, 3)
      .map(s => `#${s.id} ${s.reason || s.message || '失败'}`).join('；')
    ElMessage.warning(`${prefix} ${done} 份，跳过 ${skipped.length} 份：${reasons}`)
  } else {
    ElMessage.success(`${prefix} ${done} 份试卷`)
  }
}

async function runPaperBatch(action, payload, confirmText) {
  if (!ensureSelection()) return false
  const ids = batchIds()
  try {
    await ElMessageBox.confirm(confirmText || `确认对 ${ids.length} 份试卷执行批量操作？`,
      '批量操作确认', { type: 'warning' })
  } catch { return false }
  batchRunning.value = true
  try {
    const res = await questionApi.paperBatch({ action, ids, payload: payload || {} })
    reportBatchResult(res.data, '已处理')
    await refreshAll()
    return true
  } finally {
    batchRunning.value = false
  }
}

function batchCopy() {
  runPaperBatch('copy', {}, `确认复制 ${selection.value.length} 份试卷？将创建为当前用户的副本。`)
}

function batchDelete() {
  runPaperBatch('delete', {},
    `确认删除 ${selection.value.length} 份试卷？被作业/考试引用的试卷会被跳过，删除不可恢复。`)
}

// ---------------- 共享 ----------------
const shareDlg = ref(false)
const sharingDialogBusy = ref(false)
const shareIds = ref([])
const shareTitle = ref('')
const shareTargets = ref([])
const shareRemark = ref('')

function openShare(row) {
  shareIds.value = [row.id]
  shareTitle.value = row.name
  shareTargets.value = []
  shareRemark.value = ''
  shareDlg.value = true
}

function openBatchShare() {
  if (!ensureSelection()) return
  shareIds.value = batchIds()
  shareTitle.value = ''
  shareTargets.value = []
  shareRemark.value = ''
  shareDlg.value = true
}

async function doShare() {
  if (!shareTargets.value.length) return ElMessage.warning('请选择共享对象')
  sharingDialogBusy.value = true
  try {
    if (shareIds.value.length === 1) {
      await questionApi.sharePaper(shareIds.value[0], {
        user_ids: shareTargets.value,
        remark: shareRemark.value
      })
      ElMessage.success('共享成功')
    } else {
      const res = await questionApi.paperBatch({
        action: 'share', ids: shareIds.value,
        payload: { user_ids: shareTargets.value }
      })
      reportBatchResult(res.data, '已共享')
    }
    shareDlg.value = false
    await refreshAll()
  } finally {
    sharingDialogBusy.value = false
  }
}

// ---------------- AI 智能组卷（保留旧逻辑） ----------------
const aiDlg = ref(false)
const aiLoading = ref(false)
const aiResult = ref(null)
const aiReq = ref('')
const aiForm = reactive({ subject_id: null, grade_id: null })

const templates = [
  '生成七年级数学一元一次方程专项练习卷，10 题，难度中等',
  '生成八年级物理期中试卷，包含选择填空，20 题，60 分钟',
  '生成九年级英语完形填空专项卷，15 题，难度偏难',
  '生成七年级生物细胞单元测试卷，20 题，基础难度'
]

function openAI() {
  aiResult.value = null
  aiReq.value = templates[0]
  aiForm.grade_id = query.grade_id || null
  aiForm.subject_id = query.subject_id || null
  syncAiSubjectByGrade()
  aiDlg.value = true
}

// subjects 是 distinct 后的去重列表（带 same_name_grade_ids），
// 后端入库要精确到年级的 subject_id，切换年级时必须同步换。
function syncAiSubjectByGrade() {
  if (!aiForm.subject_id) return
  const s = subjects.value.find(x =>
    x.id === aiForm.subject_id || (x.same_name_ids || []).includes(aiForm.subject_id))
  if (!s) return
  if (!aiForm.grade_id) { aiForm.subject_id = s.id; return }
  const idx = (s.same_name_grade_ids || []).indexOf(aiForm.grade_id)
  if (idx >= 0) aiForm.subject_id = s.same_name_ids[idx]
}

function onAiGradeChange() { syncAiSubjectByGrade() }
function onAiSubjectChange() { /* 学科变了不动年级 */ }

async function runAI() {
  if (!aiReq.value) return ElMessage.warning('请输入组卷需求')
  if (!aiForm.subject_id) return ElMessage.warning('请选择学科')
  syncAiSubjectByGrade()
  aiLoading.value = true
  try {
    const res = await agentApi.paperComposer({
      request: aiReq.value, save: true,
      subject_id: aiForm.subject_id, grade_id: aiForm.grade_id
    })
    const envelope = res?.data || {}
    const payload = envelope.data || {}
    if (!envelope.success) {
      ElMessage.error(envelope.message || '组卷请求失败')
    } else if (!payload.paper?.id) {
      ElMessage.warning(payload.tip || envelope.message
        || '未生成试卷：题库可用题目不足，请先补充题目')
    } else {
      ElMessage.success(payload.tip || envelope.message || '组卷完成')
    }
    aiResult.value = payload
    await refreshAll()
  } catch (e) {
    ElMessage.error('组卷请求异常：' + (e?.message || e))
  } finally {
    aiLoading.value = false
  }
}

function useResult() {
  aiDlg.value = false
  const p = aiResult.value?.paper || {}
  ElMessage.success(
    p.id
      ? `已创建试卷「${p.name}」（${p.item_count} 题 / ${p.total_score} 分），可在列表查看`
      : '本次仅生成预览，题库可用题目不足，未创建试卷'
  )
}

onMounted(async () => {
  const [g, s, t] = await Promise.all([
    eduApi.grades(),
    eduApi.subjects({ distinct: true }),
    eduApi.peopleBrief({ identity: 'teacher' })
  ])
  grades.value = g.data || []
  subjects.value = s.data || []
  teachers.value = t.data?.items || []
  await refreshAll()
})
</script>

<style scoped>
.pm-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.pm-title-wrap { display: flex; flex-direction: column; gap: 10px; }
.pm-stats { display: flex; gap: 12px; flex-wrap: wrap; }
.pm-stat { min-width: 110px; padding: 10px 14px; }
.pm-stat .stat-label { font-size: 12px; margin-top: 2px; }
.pm-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.pm-actions :deep(.el-button + .el-button) { margin-left: 0; }

.batch-bar {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 8px 0 12px;
}
.batch-bar :deep(.el-button + .el-button) { margin-left: 0; }
.row-ops { display: flex; align-items: center; gap: 2px; flex-wrap: wrap; }
.row-ops :deep(.el-button + .el-button) { margin-left: 0; }
.pm-pagination { margin-top: 16px; justify-content: flex-end; }

.detail-head { margin-bottom: 12px; }
.detail-title { margin: 0 0 8px; }
.detail-tags { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

.ai-toolbar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.ai-toolbar :deep(.el-button + .el-button) { margin-left: 0; }
.ai-panel {
  background: #f7f9fc;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 14px;
}
.ai-metric-row { display: flex; align-items: flex-start; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }
.ai-metric-label { min-width: 76px; color: var(--el-text-color-secondary); font-size: 13px; }
.ai-issues { display: flex; flex-direction: column; gap: 4px; }
.ai-issue { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.ai-suggestions { margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.8; }
.ai-result-head {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; margin-bottom: 8px;
}

.detail-items { margin-top: 12px; }
.detail-item { padding: 10px 0; border-bottom: 1px dashed var(--el-border-color-lighter); }
.detail-item:last-child { border-bottom: none; }
.item-head { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.item-stem { line-height: 1.7; margin: 6px 0; }
.item-options { margin: 4px 0; font-size: 13px; }
.item-option { display: inline-block; margin-right: 16px; }
.item-meta { font-size: 12px; line-height: 1.7; }

.picker-filters { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ai-grade-count { float: right; color: var(--el-text-color-secondary); font-size: 12px; }

.muted { color: var(--el-text-color-secondary); font-size: 12px; }
.ml4 { margin-left: 4px; }
.ml8 { margin-left: 8px; }
.mr4 { margin-right: 4px; }
.mt8 { margin-top: 8px; }
.mb8 { margin-bottom: 8px; }
.mb12 { margin-bottom: 12px; }
</style>
