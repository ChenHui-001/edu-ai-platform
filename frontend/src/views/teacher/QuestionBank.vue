<template>
  <div class="page-container">
    <!-- 顶部：标题 + 统计 + 操作 -->
    <div class="page-header qb-header">
      <div class="qb-title-wrap">
        <h2 class="page-title">题库管理</h2>
        <div class="qb-stats" v-loading="statsLoading">
          <div v-for="c in statCards" :key="c.label" class="stat-card qb-stat">
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </div>
      </div>
      <div class="qb-actions">
        <el-button v-if="canImport" :icon="Download" @click="downloadTemplate">下载模板</el-button>
        <el-button v-if="canImport" :icon="Upload" @click="importVisible = true">批量导入</el-button>
        <el-button v-if="canExport" :icon="Download" @click="exportExcel">导出</el-button>
        <el-button v-if="canWrite" :icon="MagicStick" type="warning" @click="openAiDlg">
          AI 智能出题
        </el-button>
        <el-button v-if="canWrite" type="primary" :icon="Plus" @click="openDialog()">新增题目</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:120px"
                     @change="onGradeChange">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="query.subject_id" placeholder="先选年级" clearable
                     :disabled="!query.grade_id" style="width:120px" @change="onFilterSubjectChange">
            <el-option v-for="s in filterSubjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="知识点">
          <el-select v-model="query.knowledge_point_id" placeholder="全部" clearable filterable
                     :disabled="!query.grade_id || !query.subject_id" style="width:170px">
            <el-option v-for="k in knowledgePoints" :key="k.id" :label="k.name" :value="k.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="题型">
          <el-select v-model="query.qtype" placeholder="全部" clearable style="width:120px">
            <el-option v-for="(label, val) in TYPE_LABEL" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="query.difficulty" placeholder="全部" clearable style="width:100px">
            <el-option v-for="(label, val) in DIFFICULTY_LABEL" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:110px">
            <el-option v-for="(label, val) in STATUS_LABEL" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item label="题库">
          <el-select v-model="query.bank_type" placeholder="全部" clearable style="width:110px">
            <el-option label="我的题库" value="private" />
            <el-option label="公共题库" value="public" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="query.source" placeholder="全部" clearable style="width:110px">
            <el-option v-for="(label, val) in SOURCE_LABEL" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="题干/解析" clearable style="width:160px"
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
      <!-- 批量栏：写权限（审核员对公共题的审核走行内状态开关） -->
      <div v-if="canWrite" class="batch-bar">
        <span class="muted">已选 {{ selection.length }} 题</span>
        <el-button size="small" :disabled="!selection.length" @click="batchStatus('publish')">
          发布/上架
        </el-button>
        <el-button size="small" :disabled="!selection.length" @click="batchStatus('offline')">下架</el-button>
        <el-button size="small" :disabled="!selection.length" @click="openMoveBank">移动题库</el-button>
        <el-button size="small" :disabled="!selection.length" @click="openAssignKp">分配知识点</el-button>
        <el-button size="small" :disabled="!selection.length" @click="openBatchDifficulty">修改难度</el-button>
        <el-button size="small" :icon="MagicStick" :disabled="!selection.length"
                   @click="openAiEnrich(selection)">AI 补全</el-button>
        <el-button size="small" :icon="Cpu" :disabled="!selection.length"
                   @click="openAiQuality(selection)">AI 质检</el-button>
        <el-button size="small" type="danger" plain :disabled="!selection.length"
                   @click="batchDelete">删除</el-button>
      </div>

      <el-table v-loading="loading" :data="list" row-key="id" border stripe
                @selection-change="onSelectionChange" @row-click="onRowClick">
        <el-table-column type="selection" width="44" />
        <el-table-column label="题干" min-width="340">
          <template #default="{ row }">
            <div class="stem-cell" @click.stop="openDetail(row)">
              <div class="stem-tags">
                <el-tag size="small" effect="plain">{{ typeLabel(row.type) }}</el-tag>
                <el-tag size="small" :type="diffType(row.difficulty)">
                  {{ row.difficulty_label || difficultyLabel(row.difficulty) }}
                </el-tag>
                <el-tag size="small" type="info" effect="plain">{{ row.score }} 分</el-tag>
                <el-tag v-if="row.type_label && row.type_label !== typeLabel(row.type)"
                        size="small" type="info" effect="plain">{{ row.type_label }}</el-tag>
              </div>
              <div class="stem-text">{{ stripHtml(row.stem).slice(0, 80) }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="知识点" width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.knowledge_point_name || '未关联' }}</template>
        </el-table-column>
        <el-table-column label="题库" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.bank_type === 'public' ? 'warning' : 'info'">
              {{ row.bank_type === 'public' ? '公共' : '私有' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <span class="status-cell" @click.stop>
              <el-tag size="small" :type="statusTagType(row.status)">
                {{ statusLabel(row.status) }}
              </el-tag>
              <el-switch v-if="canWrite || canAudit"
                         :model-value="row.status === 'published'" size="small"
                         @change="toggleStatus(row)" />
            </span>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="100" align="center">
          <template #default="{ row }">{{ sourceLabel(row.source) }}</template>
        </el-table-column>
        <el-table-column prop="usage_count" label="使用次数" width="90" align="center" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <div class="row-ops" @click.stop>
              <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
              <el-button v-if="canWrite" link type="primary" size="small"
                         @click="openDialog(row)">编辑</el-button>
              <el-button v-if="canWrite" link type="warning" size="small"
                         @click="openAiVariants(row)">AI 变式</el-button>
              <el-button link type="primary" size="small" @click="checkDupe(row)">查重</el-button>
              <el-button v-if="canWrite" link type="danger" size="small"
                         @click="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page" v-model:page-size="query.page_size"
        :total="total" :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="qb-pagination"
        @current-change="load" @size-change="search"
      />
    </el-card>

    <!-- 题目详情抽屉 -->
    <el-drawer v-model="detailVisible" title="题目详情" size="640px" destroy-on-close>
      <template v-if="detail">
        <div class="detail-tags">
          <el-tag>{{ typeLabel(detail.type) }}</el-tag>
          <el-tag :type="diffType(detail.difficulty)">{{ difficultyLabel(detail.difficulty) }}</el-tag>
          <el-tag type="info" effect="plain">{{ detail.score }} 分</el-tag>
          <el-tag :type="statusTagType(detail.status)">{{ statusLabel(detail.status) }}</el-tag>
          <el-tag type="info" effect="plain">{{ sourceLabel(detail.source) }}</el-tag>
          <el-tag :type="detail.bank_type === 'public' ? 'warning' : 'info'" effect="plain">
            {{ detail.bank_type === 'public' ? '公共题库' : '我的题库' }}
          </el-tag>
          <span class="muted">使用 {{ detail.usage_count || 0 }} 次</span>
        </div>

        <div class="detail-block">
          <div class="detail-label">题干</div>
          <div class="rich-stem" v-html="safeStem(detail.stem)"></div>
        </div>

        <div v-if="parseJson(detail.options)?.length" class="detail-block">
          <div class="detail-label">选项</div>
          <div v-for="o in parseJson(detail.options)" :key="o.key" class="detail-option">
            <b>{{ o.key }}.</b> <span>{{ o.text }}</span>
          </div>
        </div>

        <div class="detail-block">
          <div class="detail-label">标准答案</div>
          <div>{{ formatAnswer(detail.answer, detail.type) }}</div>
        </div>

        <div class="detail-block">
          <div class="detail-label">解析</div>
          <div class="detail-analysis">{{ detail.analysis || '暂无解析' }}</div>
        </div>

        <el-descriptions :column="2" border size="small" class="mt12">
          <el-descriptions-item label="知识点">{{ detail.knowledge_point_name || '未关联' }}</el-descriptions-item>
          <el-descriptions-item label="使用次数">{{ detail.usage_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detail.created_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ detail.updated_at || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button v-if="canWrite" type="primary" @click="openDialog(detail)">编辑</el-button>
        <el-button v-if="canWrite" type="warning" :icon="MagicStick"
                   @click="openAiVariants(detail)">AI 变式</el-button>
      </template>
    </el-drawer>

    <!-- 新增/编辑 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑题目' : '新增题目'" width="820px" top="5vh">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="年级" prop="grade_id">
              <el-select v-model="form.grade_id" style="width:100%" @change="onFormGradeChange">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学科" prop="subject_id">
              <el-select v-model="form.subject_id" style="width:100%" @change="onFormSubjectChange">
                <el-option v-for="s in formSubjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="题型" prop="type">
              <el-select v-model="form.type" style="width:100%">
                <el-option v-for="(label, val) in TYPE_LABEL" :key="val" :label="label" :value="val" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="题干" prop="stem">
          <el-input v-model="form.stem" type="textarea" :rows="3"
                    placeholder="支持 HTML 富文本、公式（LaTeX）、图片" />
        </el-form-item>

        <!-- 选择题/判断题选项 -->
        <el-form-item v-if="showOptions" label="选项">
          <div class="options-editor">
            <div v-for="(opt, i) in optionList" :key="i" class="option-row">
              <el-radio v-if="form.type === 'single'" v-model="form.answer" :value="opt.key">正确</el-radio>
              <el-checkbox v-else-if="form.type === 'multiple'" v-model="multiAnswer" :label="opt.key" />
              <span class="opt-key">{{ opt.key }}</span>
              <el-input v-model="opt.text" placeholder="选项内容" />
              <el-button v-if="form.type !== 'judge'" link type="danger" :icon="Delete"
                         @click="optionList.splice(i, 1)" />
            </div>
            <el-button v-if="form.type !== 'judge'" size="small" :icon="Plus" @click="addOption">
              添加选项
            </el-button>
          </div>
        </el-form-item>

        <el-form-item v-if="form.type === 'multiple'" label="多选答案">
          <el-tag v-for="a in multiAnswer" :key="a" closable
                  @close="multiAnswer.splice(multiAnswer.indexOf(a), 1)">
            {{ a }}
          </el-tag>
          <span v-if="multiAnswer.length === 0" class="err-tip">请勾选正确选项</span>
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="难度">
              <el-select v-model="form.difficulty" style="width:100%">
                <el-option v-for="(label, val) in DIFFICULTY_LABEL" :key="val"
                           :label="label" :value="val" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="分值">
              <el-input-number v-model="form.score" :min="1" :max="100" :precision="1"
                               style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="知识点">
              <el-select v-model="form.knowledge_point_id" filterable clearable style="width:100%">
                <el-option v-for="k in formKnowledge" :key="k.id" :label="k.name" :value="k.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="题库类型">
          <el-radio-group v-model="form.bank_type">
            <el-radio-button value="private">我的题库</el-radio-button>
            <el-radio-button value="public">公共题库</el-radio-button>
          </el-radio-group>
          <span v-if="form.bank_type === 'public'" class="muted ml12">
            公共题库上架需管理员审核
          </span>
        </el-form-item>

        <el-form-item label="解析">
          <el-input v-model="form.analysis" type="textarea" :rows="3" placeholder="解题思路与易错点" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入 -->
    <el-dialog v-model="importVisible" title="批量导入题目" width="560px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:14px">
        <template #title>请先下载模板，按模板格式填写后上传</template>
        <el-link type="primary" :underline="false" @click="downloadTemplate">下载 Excel 模板</el-link>
      </el-alert>
      <el-form label-width="90px">
        <el-form-item label="年级">
          <el-select v-model="importForm.grade_id" style="width:100%">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="importForm.subject_id" style="width:100%">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-upload drag :auto-upload="false" :limit="1" accept=".xlsx,.xls"
                 :on-change="onFileChange" :file-list="fileList">
        <el-icon size="40" color="#909399"><UploadFilled /></el-icon>
        <div>将 Excel 拖到此处，或<em>点击选择文件</em></div>
      </el-upload>
      <div v-if="importResult" class="import-result">
        <el-alert :type="importResult.created ? 'success' : 'warning'" :closable="false" show-icon
                  :title="`成功导入 ${importResult.created} 道题目`"
                  :description="importResult.skipped_count ? `跳过 ${importResult.skipped_count} 道（重复或格式错误）` : ''" />
        <el-table v-if="importResult.skipped?.length" :data="importResult.skipped"
                  size="small" max-height="180" style="margin-top:10px">
          <el-table-column prop="line" label="行号" width="70" />
          <el-table-column prop="stem" label="题干" show-overflow-tooltip />
          <el-table-column prop="reason" label="原因" width="120" />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="importVisible = false">关闭</el-button>
        <el-button type="primary" :loading="importing" :disabled="!file" @click="doImport">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- AI 智能出题：条件生成 → 直接入库（草稿态，审核后可用于组卷） -->
    <el-dialog v-model="aiDlg" title="AI 智能出题" width="640px" destroy-on-close>
      <el-form :model="aiForm" label-width="90px">
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="学科" required>
              <el-select v-model="aiForm.subject_id" style="width:100%" @change="loadAiKps">
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
        <el-row :gutter="10">
          <el-col :span="8">
            <el-form-item label="题型">
              <el-select v-model="aiForm.type" style="width:100%">
                <el-option v-for="(label, key) in TYPE_LABEL" :key="key" :label="label" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="难度">
              <el-select v-model="aiForm.difficulty" style="width:100%">
                <el-option v-for="(label, val) in DIFFICULTY_LABEL" :key="val"
                           :label="label" :value="val" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="数量">
              <el-input-number v-model="aiForm.count" :min="1" :max="20" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="知识点">
          <el-select v-model="aiForm.knowledge_point_id" clearable filterable
                     style="width:100%" placeholder="可选，AI 将紧扣该知识点出题">
            <el-option v-for="k in aiKps" :key="k.id" :label="k.name" :value="k.id" />
          </el-select>
        </el-form-item>
      </el-form>

      <div v-if="aiResult?.length" class="mb12">
        <el-alert type="success" :closable="false" show-icon
                  :title="`已生成 ${aiResult.length} 题并保存至题库（草稿状态）`"
                  description="草稿题审核通过后即可用于组卷；可在列表用「来源=AI」筛选查看" />
        <el-table :data="aiResult" size="small" border max-height="240" class="mt8">
          <el-table-column label="题型" width="76">
            <template #default="{ row }">{{ typeLabel(row.type) }}</template>
          </el-table-column>
          <el-table-column label="难度" width="58">
            <template #default="{ row }">{{ difficultyLabel(row.difficulty) }}</template>
          </el-table-column>
          <el-table-column prop="score" label="分值" width="52" />
          <el-table-column label="题干" min-width="300">
            <template #default="{ row }">{{ stripHtml(row.stem).slice(0, 70) }}</template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="aiDlg = false">关闭</el-button>
        <el-button type="primary" :loading="aiLoading" :disabled="!aiForm.subject_id"
                   @click="generateAi">生成并入库</el-button>
      </template>
    </el-dialog>

    <!-- AI 变式：预览勾选后创建（不落库直到确认） -->
    <el-dialog v-model="aiVarDlg" title="AI 变式" width="900px" @opened="syncAiVarSelection">
      <el-alert v-if="aiVarFallback" class="mb12" type="warning" :closable="false" show-icon
                title="当前无可用大模型，变式由规则引擎降级生成（is_fallback=true）" />
      <div class="ai-base">
        <span class="muted">原题：</span>
        <span>{{ aiVarBase ? stripHtml(aiVarBase.stem).slice(0, 80) : '-' }}</span>
      </div>
      <div class="ai-actions">
        <span class="muted">数量</span>
        <el-input-number v-model="aiVarForm.count" :min="1" :max="10" size="small" />
        <span class="muted">难度</span>
        <el-select v-model="aiVarForm.difficulty" clearable placeholder="跟随原题"
                   size="small" style="width:120px">
          <el-option v-for="(label, val) in DIFFICULTY_LABEL" :key="val"
                     :label="label" :value="val" />
        </el-select>
        <el-button type="primary" size="small" :loading="aiVarLoading" @click="generateVariants">
          生成变式
        </el-button>
        <span class="muted">只生成预览，勾选后才会创建（草稿状态）</span>
      </div>

      <template v-if="aiVarItems.length">
        <div class="ai-result-head">
          <b>变式预览</b>
          <span class="muted">共 {{ aiVarItems.length }} 条，已选 {{ aiVarSelected.length }} 条</span>
        </div>
        <el-table ref="aiVarTableRef" :data="aiVarItems" size="small" border max-height="320"
                  @selection-change="onAiVarSelectionChange">
          <el-table-column type="selection" width="42" />
          <el-table-column label="题型" width="90">
            <template #default="{ row }">{{ typeLabel(row.type || aiVarBase?.type) }}</template>
          </el-table-column>
          <el-table-column label="难度" width="80">
            <template #default="{ row }">{{ difficultyLabel(row.difficulty) }}</template>
          </el-table-column>
          <el-table-column prop="score" label="分值" width="70" />
          <el-table-column label="题干" min-width="280">
            <template #default="{ row }">{{ stripHtml(row.stem).slice(0, 90) }}</template>
          </el-table-column>
          <el-table-column label="解析" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">{{ stripHtml(row.analysis).slice(0, 60) || '-' }}</template>
          </el-table-column>
        </el-table>
      </template>

      <template #footer>
        <el-button @click="aiVarDlg = false">关闭</el-button>
        <el-button type="primary" :loading="aiVarCreating" :disabled="!aiVarSelected.length"
                   @click="createVariants">
          创建选中（{{ aiVarSelected.length }}）
        </el-button>
      </template>
    </el-dialog>

    <!-- AI 补全：预览后应用（analysis / knowledge_point / difficulty） -->
    <el-dialog v-model="aiEnrichDlg" title="AI 补全" width="900px" @opened="syncAiEnrichSelection">
      <el-alert v-if="aiEnrichFallback" class="mb12" type="warning" :closable="false" show-icon
                title="当前无可用大模型，补全建议由规则引擎降级生成（is_fallback=true）" />
      <div class="ai-result-head">
        <b>补全建议</b>
        <span class="muted">共 {{ aiEnrichItems.length }} 条，已选 {{ aiEnrichSelected.length }} 条；
          应用后仅更新解析/知识点/难度</span>
      </div>
      <el-table ref="aiEnrichTableRef" v-loading="aiEnrichLoading" :data="aiEnrichItems"
                size="small" border max-height="360" @selection-change="onAiEnrichSelectionChange">
        <el-table-column type="selection" width="42" />
        <el-table-column label="题目" min-width="220">
          <template #default="{ row }">
            <span class="muted">#{{ row.id }}</span> {{ stemOf(row.id) }}
          </template>
        </el-table-column>
        <el-table-column label="建议解析" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">{{ stripHtml(row.analysis).slice(0, 80) || '-' }}</template>
        </el-table-column>
        <el-table-column label="建议知识点" width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.knowledge_point_name || (row.knowledge_point_id ? `#${row.knowledge_point_id}` : '未关联') }}</template>
        </el-table-column>
        <el-table-column label="建议难度" width="90" align="center">
          <template #default="{ row }">{{ difficultyLabel(row.difficulty) }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="aiEnrichDlg = false">关闭</el-button>
        <el-button type="primary" :loading="aiEnrichApplying" :disabled="!aiEnrichSelected.length"
                   @click="applyAiEnrich">
          应用选中（{{ aiEnrichSelected.length }}）
        </el-button>
      </template>
    </el-dialog>

    <!-- AI 质检：展示问题列表，可定位题目 -->
    <el-dialog v-model="aiQualityDlg" title="AI 质检" width="820px">
      <el-alert v-if="aiQualityFallback" class="mb12" type="warning" :closable="false" show-icon
                title="当前无可用大模型，质检结果为规则引擎降级生成（is_fallback=true）" />
      <el-table v-loading="aiQualityLoading" :data="aiQualityItems" size="small" border max-height="420">
        <el-table-column label="题目" min-width="260">
          <template #default="{ row }">
            <span class="muted">#{{ row.id }}</span> {{ stemOf(row.id) }}
          </template>
        </el-table-column>
        <el-table-column label="问题" min-width="300">
          <template #default="{ row }">
            <div v-if="!row.issues?.length" class="muted">未发现问题</div>
            <div v-for="(issue, i) in (row.issues || [])" :key="i" class="quality-issue">
              <el-tag size="small" :type="severityType(issue.severity)">
                {{ severityLabel(issue.severity) }}
              </el-tag>
              <span>{{ issue.message || issue.code }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="locateQuestion(row.id)">定位</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="aiQualityDlg = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 批量：移动题库 -->
    <el-dialog v-model="bankDlg" title="移动题库" width="460px">
      <el-alert type="info" :closable="false" show-icon
                title="移动到公共题库后，上架需管理员审核；无审核权限时会被置为待审核。" />
      <el-radio-group v-model="bankForm.bank_type" class="mt12">
        <el-radio-button value="private">我的题库</el-radio-button>
        <el-radio-button value="public">公共题库</el-radio-button>
      </el-radio-group>
      <div class="muted mt8">已选中 {{ selection.length }} 道题</div>
      <template #footer>
        <el-button @click="bankDlg = false">取消</el-button>
        <el-button type="primary" :loading="batchRunning" @click="confirmMoveBank">确认移动</el-button>
      </template>
    </el-dialog>

    <!-- 批量：分配知识点 -->
    <el-dialog v-model="kpDlg" title="分配知识点" width="520px">
      <el-alert type="info" :closable="false" show-icon
                title="按目标知识点校验年级/学科；留空表示清空知识点关联。" />
      <el-form label-width="90px" class="mt12">
        <el-form-item label="年级">
          <el-select v-model="kpForm.grade_id" style="width:100%" @change="onKpGradeChange">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="kpForm.subject_id" :disabled="!kpForm.grade_id"
                     style="width:100%" @change="onKpSubjectChange">
            <el-option v-for="s in kpSubjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="知识点">
          <el-select v-model="kpForm.knowledge_point_id" filterable clearable
                     :disabled="!kpForm.subject_id" placeholder="留空则清空关联"
                     style="width:100%">
            <el-option v-for="k in kpOptions" :key="k.id" :label="k.name" :value="k.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <div class="muted">已选中 {{ selection.length }} 道题；跨年级/学科的题由后端逐条校验，不合规会进入 skipped</div>
      <template #footer>
        <el-button @click="kpDlg = false">取消</el-button>
        <el-button type="primary" :loading="batchRunning" @click="confirmAssignKp">确认分配</el-button>
      </template>
    </el-dialog>

    <!-- 批量：修改难度 -->
    <el-dialog v-model="diffDlg" title="批量修改难度" width="420px">
      <el-select v-model="diffForm.difficulty" placeholder="请选择难度" style="width:100%">
        <el-option v-for="(label, val) in DIFFICULTY_LABEL" :key="val" :label="label" :value="val" />
      </el-select>
      <div class="muted mt8">已选中 {{ selection.length }} 道题</div>
      <template #footer>
        <el-button @click="diffDlg = false">取消</el-button>
        <el-button type="primary" :loading="batchRunning" :disabled="!diffForm.difficulty"
                   @click="confirmBatchDifficulty">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Download, Plus, Refresh, Search, Upload, UploadFilled, Delete, MagicStick, Cpu
} from '@element-plus/icons-vue'
import { questionApi, eduApi, agentApi } from '@/api'
import { useUserStore } from '@/store/user'
import { sanitizeHtml } from '@/utils/sanitize'
import { downloadBlob } from '@/utils/download'

// 题干由教师/AI 录入，后端不做净化就落库，直接 v-html 会执行其中的脚本。
function safeStem(s) { return sanitizeHtml(s) }

const userStore = useUserStore()
const { can } = userStore
const canWrite = computed(() => can('question:bank:write'))
const canImport = computed(() => can('question:bank:import'))
const canExport = computed(() => can('question:bank:export'))
const canAudit = computed(() => can('question:bank:audit'))

// ---------------- 常量 / 展示映射 ----------------
const TYPE_LABEL = {
  single: '单选题', multiple: '多选题', judge: '判断题', blank: '填空题',
  short: '简答题', calc: '计算题', material: '材料分析题', composition: '作文题'
}
// 历史别名：早期后端未校验题型，库中可能存在 subjective 等非法值。
const TYPE_ALIAS = { subjective: 'short', essay: 'composition', fill: 'blank', calculate: 'calc' }
const DIFFICULTY_LABEL = { easy: '简单', medium: '中等', hard: '困难' }
const STATUS_LABEL = { draft: '待审核', published: '已上架', offline: '已下架' }
const STATUS_TYPE = { draft: 'warning', published: 'success', offline: 'info' }
const SOURCE_LABEL = { manual: '手工录入', import: '批量导入', ai: 'AI 生成', ai_import: 'AI 导入' }

function normalizeType(t) {
  const v = String(t || 'single').toLowerCase()
  const fixed = TYPE_ALIAS[v] || v
  return TYPE_LABEL[fixed] ? fixed : 'single'
}
function typeLabel(t) {
  const v = String(t || '')
  if (TYPE_LABEL[v]) return TYPE_LABEL[v]
  if (TYPE_ALIAS[v]) return TYPE_LABEL[TYPE_ALIAS[v]]
  return v ? `其他题型(${v})` : '-'
}
function difficultyLabel(v) { return DIFFICULTY_LABEL[v] || v || '-' }
function statusLabel(v) { return STATUS_LABEL[v] || v || '-' }
function statusTagType(v) { return STATUS_TYPE[v] || 'info' }
function sourceLabel(v) { return SOURCE_LABEL[v] || v || '手工录入' }
function diffType(d) { return { easy: 'success', medium: 'warning', hard: 'danger' }[d] || 'info' }
function severityType(s) { return { error: 'danger', warning: 'warning', info: 'info' }[s] || 'info' }
function severityLabel(s) { return { error: '错误', warning: '警告', info: '提示' }[s] || s || '提示' }

// ---------------- 基础数据 ----------------
const grades = ref([])
// AI 智能出题用「按名称去重」的学科（带 same_name_ids，用于年级切换时映射精确 subject_id）
const subjects = ref([])
// 筛选/批量分配用「当前年级精确学科」
const filterSubjects = ref([])
const knowledgePoints = ref([])
const formSubjects = ref([])
const formKnowledge = ref([])
const aiKps = ref([])

const query = reactive({
  page: 1, page_size: 20,
  grade_id: null, subject_id: null, knowledge_point_id: null,
  qtype: null, difficulty: null, status: null, bank_type: null,
  source: null, keyword: ''
})

const list = ref([])
const total = ref(0)
const loading = ref(false)
const selection = ref([])
const stats = ref({})
const statsLoading = ref(false)

const statCards = computed(() => {
  const d = stats.value || {}
  const published = d.by_status?.published ?? d.published
  return [
    { label: '题目总数', value: d.total ?? '-' },
    { label: '已发布', value: published ?? '-' },
    { label: '含解析', value: d.with_analysis ?? '-' },
    { label: '含知识点', value: d.with_knowledge ?? '-' }
  ]
})

function buildFilterParams() {
  const params = {}
  for (const key of ['grade_id', 'subject_id', 'knowledge_point_id',
    'qtype', 'difficulty', 'status', 'bank_type', 'source']) {
    if (query[key]) params[key] = query[key]
  }
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
    const res = await questionApi.stats(buildFilterParams())
    stats.value = res.data || {}
  } catch {
    // 统计接口失败不影响列表（例如后端 V2 尚未就绪）
  } finally {
    statsLoading.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const res = await questionApi.list(buildListParams())
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
    selection.value = []
    syncDetailFromList()
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
    page: 1, grade_id: null, subject_id: null, knowledge_point_id: null,
    qtype: null, difficulty: null, status: null, bank_type: null, source: null, keyword: ''
  })
  filterSubjects.value = []
  knowledgePoints.value = []
  refreshAll()
}

async function loadFilterSubjects(gradeId) {
  if (!gradeId) { filterSubjects.value = []; return }
  try {
    const res = await eduApi.subjects({ grade_id: gradeId })
    filterSubjects.value = res.data || []
  } catch { filterSubjects.value = [] }
}

async function loadFilterKnowledge(gid, sid) {
  if (!gid || !sid) { knowledgePoints.value = []; return }
  try {
    const res = await eduApi.knowledgeList({ grade_id: gid, subject_id: sid, params_limit: 300 })
    knowledgePoints.value = Array.isArray(res.data) ? res.data : (res.data?.items || [])
  } catch { knowledgePoints.value = [] }
}

function onGradeChange() {
  query.subject_id = null
  query.knowledge_point_id = null
  knowledgePoints.value = []
  loadFilterSubjects(query.grade_id)
}

function onFilterSubjectChange() {
  query.knowledge_point_id = null
  loadFilterKnowledge(query.grade_id, query.subject_id)
}

// ---------------- 表格 / 详情 ----------------
function onSelectionChange(val) { selection.value = val || [] }

function onRowClick(row, column) {
  // 勾选列不触发详情，避免批量选择时反复弹抽屉
  if (column?.type === 'selection') return
  openDetail(row)
}

const detailVisible = ref(false)
const detail = ref(null)

function openDetail(row) {
  if (!row) return
  detail.value = { ...row }
  detailVisible.value = true
}

function syncDetailFromList() {
  if (!detail.value?.id) return
  const row = list.value.find(q => q.id === detail.value.id)
  if (row) detail.value = { ...row }
}

function parseJson(v) {
  if (!v) return null
  if (Array.isArray(v)) return v
  try { return JSON.parse(v) } catch { return null }
}
function parseJsonLoose(v) {
  const parsed = parseJson(v)
  return parsed ?? v
}
function stripHtml(s) { return String(s || '').replace(/<[^>]*>/g, '') }
function formatAnswer(answer, type) {
  const a = parseJsonLoose(answer)
  if (Array.isArray(a)) return a.join('、')
  if (a === null || a === undefined || a === '') return '未填写'
  return String(a)
}
function stemOf(id) {
  const row = list.value.find(q => q.id === id)
  return row ? stripHtml(row.stem).slice(0, 40) : '（当前页未找到该题）'
}

// ---------------- 单题 CRUD / 状态 ----------------
const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null, type: 'single', stem: '', options: [], answer: '',
  analysis: '', score: 5, difficulty: 'medium', grade_id: null, subject_id: null,
  knowledge_point_id: null, bank_type: 'private'
})
const optionList = ref([])
const multiAnswer = ref([])
const showOptions = computed(() => ['single', 'multiple', 'judge'].includes(form.type))

const rules = {
  stem: [{ required: true, message: '请输入题干', trigger: 'blur' }],
  type: [{ required: true, message: '请选择题型', trigger: 'change' }],
  subject_id: [{ required: true, message: '请选择学科', trigger: 'change' }],
  grade_id: [{ required: true, message: '请选择年级', trigger: 'change' }]
}

function addOption() {
  const next = String.fromCharCode(65 + optionList.value.length)
  optionList.value.push({ key: next, text: '' })
}

async function loadFormSubjects(gid) {
  if (!gid) { formSubjects.value = []; return }
  const res = await eduApi.subjects({ grade_id: gid })
  formSubjects.value = res.data || []
}
async function loadFormKnowledge(gid, sid) {
  if (!gid || !sid) { formKnowledge.value = []; return }
  const res = await eduApi.knowledgeList({ grade_id: gid, subject_id: sid, params_limit: 300 })
  formKnowledge.value = Array.isArray(res.data) ? res.data : (res.data?.items || [])
}
async function onFormGradeChange() {
  form.subject_id = null
  form.knowledge_point_id = null
  formKnowledge.value = []
  await loadFormSubjects(form.grade_id)
}
async function onFormSubjectChange() {
  form.knowledge_point_id = null
  await loadFormKnowledge(form.grade_id, form.subject_id)
}

function openDialog(row) {
  Object.assign(form, {
    id: row?.id ?? null,
    type: normalizeType(row?.type),
    stem: row?.stem ?? '',
    analysis: row?.analysis ?? '',
    score: row?.score ?? 5,
    difficulty: row?.difficulty ?? 'medium',
    grade_id: row?.grade_id ?? query.grade_id,
    subject_id: row?.subject_id ?? query.subject_id,
    knowledge_point_id: row?.knowledge_point_id ?? null,
    bank_type: row?.bank_type ?? 'private',
    options: [], answer: ''
  })
  const opts = parseJson(row?.options) || []
  if (form.type === 'judge') {
    optionList.value = [{ key: 'A', text: '正确' }, { key: 'B', text: '错误' }]
    form.answer = typeof row?.answer === 'string' && /正确|true/i.test(row.answer) ? 'A' : ''
    multiAnswer.value = []
  } else {
    optionList.value = opts.length
      ? opts.map(o => ({ key: o.key, text: o.text }))
      : [{ key: 'A', text: '' }, { key: 'B', text: '' }, { key: 'C', text: '' }, { key: 'D', text: '' }]
    const ans = parseJsonLoose(row?.answer)
    form.answer = Array.isArray(ans) ? '' : String(ans ?? '')
    multiAnswer.value = Array.isArray(ans)
      ? ans
      : (form.type === 'multiple' && ans ? [String(ans)] : [])
  }
  if (form.grade_id) loadFormSubjects(form.grade_id)
  if (form.grade_id && form.subject_id) loadFormKnowledge(form.grade_id, form.subject_id)
  dialogVisible.value = true
}

async function save() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = { ...form }
    if (showOptions.value) {
      payload.options = optionList.value.filter(o => o.text)
      payload.answer = form.type === 'multiple'
        ? multiAnswer.value
        : (form.type === 'judge' ? (form.answer === 'A' ? '正确' : '错误') : form.answer)
    }
    if (form.id) await questionApi.update(form.id, payload)
    else await questionApi.create(payload)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await refreshAll()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除题目「${stripHtml(row.stem).slice(0, 20)}...」吗？已被试卷引用时会删除失败。`,
      '删除确认', { type: 'warning', confirmButtonText: '确认删除' })
  } catch { return }
  await questionApi.remove(row.id)
  ElMessage.success('已删除')
  if (detail.value?.id === row.id) detailVisible.value = false
  await refreshAll()
}

async function toggleStatus(row) {
  const next = row.status === 'published' ? 'offline' : 'published'
  await questionApi.changeStatus(row.id, { status: next })
  ElMessage.success(next === 'published' ? '已上架' : '已下架')
  await refreshAll()
}

async function checkDupe(row) {
  const res = await questionApi.duplicates(row.id)
  const dupes = Array.isArray(res.data) ? res.data : []
  if (!dupes.length) return ElMessage.success('未发现重复题目')
  ElMessageBox.alert(
    dupes.map(d => `ID ${d.id}：${stripHtml(d.stem)}`).join('<br/>'),
    `发现 ${dupes.length} 道疑似重复题目`, { dangerouslyUseHTMLString: true }
  )
}

// ---------------- 导入 / 导出 ----------------
const importVisible = ref(false)
const importing = ref(false)
const file = ref(null)
const fileList = ref([])
const importResult = ref(null)
const importForm = reactive({ grade_id: null, subject_id: null })

async function downloadTemplate() {
  await downloadBlob(questionApi.downloadTemplate(), '题目导入模板.xlsx')
}

async function exportExcel() {
  const params = buildFilterParams()
  await downloadBlob(questionApi.exportExcel(params), '题库导出.xlsx')
}

function onFileChange(f) {
  file.value = f.raw
  fileList.value = [f]
  importResult.value = null
}

async function doImport() {
  if (!file.value) return ElMessage.warning('请选择文件')
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', file.value)
    if (importForm.grade_id) fd.append('grade_id', importForm.grade_id)
    if (importForm.subject_id) fd.append('subject_id', importForm.subject_id)
    const res = await questionApi.import(fd)
    importResult.value = res.data || {}
    ElMessage.success(res.message || '导入完成')
    await refreshAll()
  } finally {
    importing.value = false
  }
}

// ---------------- AI 智能出题（保留旧逻辑） ----------------
const aiDlg = ref(false)
const aiLoading = ref(false)
const aiResult = ref(null)
const aiForm = reactive({
  subject_id: null, grade_id: null, type: 'single',
  difficulty: 'medium', count: 5, knowledge_point_id: null
})

function openAiDlg() {
  Object.assign(aiForm, {
    subject_id: query.subject_id, grade_id: query.grade_id,
    type: 'single', difficulty: 'medium', count: 5, knowledge_point_id: null
  })
  syncAiSubjectByGrade()
  aiResult.value = null
  aiDlg.value = true
  if (aiForm.subject_id) loadAiKps()
}

// subjects 是按名称去重后的列表（同一条目带 same_name_grade_ids），
// 而 subject_id 精确到年级。切换年级时必须同步换成该年级对应的那条。
function syncAiSubjectByGrade() {
  if (!aiForm.subject_id) return
  const s = subjects.value.find((x) =>
    x.id === aiForm.subject_id || (x.same_name_ids || []).includes(aiForm.subject_id))
  if (!s) return
  if (!aiForm.grade_id) { aiForm.subject_id = s.id; return }
  const idx = (s.same_name_grade_ids || []).indexOf(aiForm.grade_id)
  if (idx >= 0) aiForm.subject_id = s.same_name_ids[idx]
}

function onAiGradeChange() {
  syncAiSubjectByGrade()
  aiForm.knowledge_point_id = null
  loadAiKps()
}

async function loadAiKps() {
  if (!aiForm.subject_id) { aiKps.value = []; return }
  try {
    const res = await eduApi.knowledge({ subject_id: aiForm.subject_id, params_limit: 200 })
    aiKps.value = res.data?.items || res.data || []
  } catch { aiKps.value = [] }
}

async function generateAi() {
  if (!aiForm.subject_id) return ElMessage.warning('请选择学科')
  syncAiSubjectByGrade()
  if (!aiForm.grade_id) {
    aiForm.grade_id = subjects.value.find((s) => s.id === aiForm.subject_id)?.grade_id ?? null
  }
  aiLoading.value = true
  try {
    const res = await agentApi.questionGenerator({ ...aiForm, save: true })
    const d = res.data || {}
    aiResult.value = d.questions || []
    if (aiResult.value.length) {
      ElMessage.success(`已生成 ${aiResult.value.length} 题并保存至题库（草稿）`)
      await refreshAll()
    } else {
      ElMessage.warning(d.tip || '未能生成题目，请调整条件后重试')
    }
  } finally {
    aiLoading.value = false
  }
}

// ---------------- 批量操作 ----------------
const batchRunning = ref(false)

function batchIds() { return selection.value.map(q => q.id) }

function ensureSelection() {
  if (!selection.value.length) {
    ElMessage.warning('请先勾选题目')
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
      .map(s => `#${s.id} ${s.reason || '失败'}`).join('；')
    ElMessage.warning(`${prefix} ${done} 道，跳过 ${skipped.length} 道：${reasons}`)
  } else {
    ElMessage.success(`${prefix} ${done} 道题目`)
  }
}

async function runBatch(action, payload, confirmText) {
  if (!ensureSelection()) return false
  const ids = batchIds()
  try {
    await ElMessageBox.confirm(confirmText || `确认对 ${ids.length} 道题执行批量操作？`,
      '批量操作确认', { type: 'warning' })
  } catch {
    return false
  }
  batchRunning.value = true
  try {
    const res = await questionApi.batch({ action, ids, payload: payload || {} })
    reportBatchResult(res.data, '已处理')
    await refreshAll()
    return true
  } finally {
    batchRunning.value = false
  }
}

function batchStatus(action) {
  const isPublish = action === 'publish'
  const ids = batchIds()
  if (!ensureSelection()) return
  const tip = isPublish
    ? `确认发布 ${ids.length} 道题？公共题库上架需要审核权限，无权题目会被跳过或整批拒绝。`
    : `确认下架 ${ids.length} 道题？下架后学生不可见。`
  runBatch(action, {}, tip)
}

function batchDelete() {
  const ids = batchIds()
  if (!ensureSelection()) return
  runBatch('delete', {},
    `确认删除 ${ids.length} 道题？已被试卷引用的题目会被跳过，删除不可恢复。`)
}

const bankDlg = ref(false)
const bankForm = reactive({ bank_type: 'private' })
function openMoveBank() {
  if (!ensureSelection()) return
  bankForm.bank_type = selection.value[0]?.bank_type === 'public' ? 'public' : 'private'
  bankDlg.value = true
}
function confirmMoveBank() {
  runBatch('move_bank', { bank_type: bankForm.bank_type },
    `确认将 ${selection.value.length} 道题移动到「${bankForm.bank_type === 'public' ? '公共题库' : '我的题库'}」？公共题库上架需审核。`)
    .then((ok) => { if (ok) bankDlg.value = false })
}

const diffDlg = ref(false)
const diffForm = reactive({ difficulty: null })
function openBatchDifficulty() {
  if (!ensureSelection()) return
  diffForm.difficulty = null
  diffDlg.value = true
}
function confirmBatchDifficulty() {
  return runBatch('set_difficulty', { difficulty: diffForm.difficulty },
    `确认将 ${selection.value.length} 道题难度改为「${difficultyLabel(diffForm.difficulty)}」？`)
    .then((ok) => {
      if (ok) diffDlg.value = false
      return ok
    })
}

const kpDlg = ref(false)
const kpForm = reactive({ grade_id: null, subject_id: null, knowledge_point_id: null })
const kpSubjects = ref([])
const kpOptions = ref([])

function openAssignKp() {
  if (!ensureSelection()) return
  const first = selection.value[0]
  kpForm.grade_id = query.grade_id || first?.grade_id || null
  kpForm.subject_id = query.subject_id || first?.subject_id || null
  kpForm.knowledge_point_id = null
  kpSubjects.value = []
  kpOptions.value = []
  kpDlg.value = true
  if (kpForm.grade_id) loadKpSubjects(kpForm.grade_id, kpForm.subject_id)
}

async function loadKpSubjects(gid, keepSubjectId) {
  if (!gid) return
  const res = await eduApi.subjects({ grade_id: gid })
  kpSubjects.value = res.data || []
  if (keepSubjectId && !kpSubjects.value.some(s => s.id === keepSubjectId)) {
    kpForm.subject_id = null
  }
  loadKpOptions()
}
async function loadKpOptions() {
  if (!kpForm.grade_id || !kpForm.subject_id) { kpOptions.value = []; return }
  const res = await eduApi.knowledgeList({
    grade_id: kpForm.grade_id, subject_id: kpForm.subject_id, params_limit: 300
  })
  kpOptions.value = Array.isArray(res.data) ? res.data : (res.data?.items || [])
}
function onKpGradeChange() {
  kpForm.subject_id = null
  kpForm.knowledge_point_id = null
  kpOptions.value = []
  loadKpSubjects(kpForm.grade_id)
}
function onKpSubjectChange() {
  kpForm.knowledge_point_id = null
  loadKpOptions()
}
function confirmAssignKp() {
  if (!kpForm.grade_id || !kpForm.subject_id) return ElMessage.warning('请选择目标年级与学科')
  runBatch('assign_knowledge', { knowledge_point_id: kpForm.knowledge_point_id ?? null },
    `确认将 ${selection.value.length} 道题的知识点分配到「${kpOptions.value.find(k => k.id === kpForm.knowledge_point_id)?.name || '清空关联'}」？`)
    .then((ok) => { if (ok) kpDlg.value = false })
}

// ---------------- AI 变式 ----------------
const aiVarDlg = ref(false)
const aiVarLoading = ref(false)
const aiVarCreating = ref(false)
const aiVarBase = ref(null)
const aiVarItems = ref([])
const aiVarSelected = ref([])
const aiVarFallback = ref(false)
const aiVarTableRef = ref(null)
const aiVarForm = reactive({ count: 3, difficulty: '' })

function openAiVariants(row) {
  if (!canWrite.value || !row) return
  aiVarBase.value = row
  aiVarItems.value = []
  aiVarSelected.value = []
  aiVarFallback.value = false
  aiVarForm.count = 3
  aiVarForm.difficulty = ''
  aiVarDlg.value = true
  generateVariants()
}

async function generateVariants() {
  if (!aiVarBase.value) return
  aiVarLoading.value = true
  try {
    const payload = { id: aiVarBase.value.id, count: aiVarForm.count }
    if (aiVarForm.difficulty) payload.difficulty = aiVarForm.difficulty
    const res = await questionApi.aiVariants(payload)
    const d = res.data || {}
    aiVarItems.value = Array.isArray(d.items) ? d.items : []
    aiVarFallback.value = d.is_fallback === true
    aiVarSelected.value = []
    await nextTick()
    syncAiVarSelection()
    if (!aiVarItems.value.length) ElMessage.warning('未生成变式题目')
  } finally {
    aiVarLoading.value = false
  }
}

function syncAiVarSelection() {
  selectAllRows(aiVarTableRef.value, aiVarItems.value)
  aiVarSelected.value = aiVarItems.value.slice()
}
function onAiVarSelectionChange(rows) { aiVarSelected.value = rows || [] }

async function createVariants() {
  if (!canWrite.value) return
  const rows = aiVarSelected.value
  const base = aiVarBase.value
  if (!rows.length || !base) return ElMessage.warning('请勾选要创建的变式题目')
  aiVarCreating.value = true
  let success = 0
  const failed = []
  try {
    for (const item of rows) {
      try {
        await questionApi.create({
          type: item.type || base.type,
          stem: item.stem,
          options: item.options ?? [],
          answer: item.answer,
          analysis: item.analysis || '',
          score: item.score ?? base.score,
          difficulty: item.difficulty || aiVarForm.difficulty || base.difficulty || 'medium',
          grade_id: base.grade_id,
          subject_id: base.subject_id,
          knowledge_point_id: item.knowledge_point_id ?? base.knowledge_point_id ?? null,
          bank_type: base.bank_type || 'private',
          status: 'draft'
        })
        success++
      } catch {
        failed.push(item.stem ? stripHtml(item.stem).slice(0, 20) : '未命名')
      }
    }
  } finally {
    aiVarCreating.value = false
  }
  if (success) {
    ElMessage.success(`已创建 ${success} 道变式题（草稿）${failed.length ? `，失败 ${failed.length} 道` : ''}`)
    aiVarDlg.value = false
    await refreshAll()
  } else if (failed.length) {
    ElMessage.error(`创建失败：${failed.slice(0, 3).join('、')}`)
  }
}

// ---------------- AI 补全 ----------------
const aiEnrichDlg = ref(false)
const aiEnrichLoading = ref(false)
const aiEnrichApplying = ref(false)
const aiEnrichItems = ref([])
const aiEnrichSelected = ref([])
const aiEnrichFallback = ref(false)
const aiEnrichTableRef = ref(null)

function selectAllRows(table, rows) {
  if (!table || !rows?.length) return
  table.clearSelection?.()
  rows.forEach(r => table.toggleRowSelection(r, true))
}

async function openAiEnrich(nodes) {
  if (!canWrite.value) return
  const ids = (nodes || []).filter(Boolean).map(q => q.id)
  if (!ids.length) return ElMessage.warning('请先勾选题目')
  if (ids.length > 50) return ElMessage.warning('AI 补全单次最多 50 道题')
  aiEnrichDlg.value = true
  aiEnrichLoading.value = true
  aiEnrichItems.value = []
  aiEnrichSelected.value = []
  aiEnrichFallback.value = false
  try {
    const res = await questionApi.aiEnrich(ids)
    const d = res.data || {}
    aiEnrichItems.value = Array.isArray(d.items) ? d.items : []
    aiEnrichFallback.value = d.is_fallback === true
    await nextTick()
    syncAiEnrichSelection()
  } catch {
    aiEnrichDlg.value = false
  } finally {
    aiEnrichLoading.value = false
  }
}

function syncAiEnrichSelection() {
  selectAllRows(aiEnrichTableRef.value, aiEnrichItems.value)
  aiEnrichSelected.value = aiEnrichItems.value.slice()
}
function onAiEnrichSelectionChange(rows) { aiEnrichSelected.value = rows || [] }

async function applyAiEnrich() {
  const rows = aiEnrichSelected.value
  if (!rows.length) return ElMessage.warning('请勾选要应用的补全建议')
  aiEnrichApplying.value = true
  let success = 0
  const failed = []
  try {
    for (const item of rows) {
      try {
        await questionApi.update(item.id, {
          analysis: item.analysis || '',
          knowledge_point_id: item.knowledge_point_id ?? undefined,
          difficulty: item.difficulty || undefined
        })
        success++
      } catch {
        failed.push(`#${item.id}`)
      }
    }
  } finally {
    aiEnrichApplying.value = false
  }
  if (success) {
    ElMessage.success(`已应用 ${success} 条补全建议${failed.length ? `，失败 ${failed.length} 条` : ''}`)
    aiEnrichDlg.value = false
    await refreshAll()
  } else if (failed.length) {
    ElMessage.error(`应用失败：${failed.slice(0, 3).join('、')}`)
  }
}

// ---------------- AI 质检 ----------------
const aiQualityDlg = ref(false)
const aiQualityLoading = ref(false)
const aiQualityItems = ref([])
const aiQualityFallback = ref(false)

async function openAiQuality(nodes) {
  if (!canWrite.value) return
  const ids = (nodes || []).filter(Boolean).map(q => q.id)
  if (!ids.length) return ElMessage.warning('请先勾选题目')
  if (ids.length > 50) return ElMessage.warning('AI 质检单次最多 50 道题')
  aiQualityDlg.value = true
  aiQualityLoading.value = true
  aiQualityItems.value = []
  aiQualityFallback.value = false
  try {
    const res = await questionApi.aiQuality(ids)
    const d = res.data || {}
    aiQualityItems.value = Array.isArray(d.items) ? d.items : []
    aiQualityFallback.value = d.is_fallback === true
    if (!aiQualityItems.value.length) ElMessage.info('未返回质检结果')
  } catch {
    aiQualityDlg.value = false
  } finally {
    aiQualityLoading.value = false
  }
}

function locateQuestion(id) {
  const row = list.value.find(q => q.id === id)
  if (!row) return ElMessage.warning('该题不在当前页，请调整筛选/翻页后再定位')
  aiQualityDlg.value = false
  openDetail(row)
}

onMounted(async () => {
  const [g, s] = await Promise.all([
    eduApi.grades(),
    eduApi.subjects({ distinct: true })
  ])
  grades.value = g.data || []
  subjects.value = s.data || []
  await refreshAll()
})
</script>

<style scoped>
.qb-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.qb-title-wrap { display: flex; flex-direction: column; gap: 10px; }
.qb-stats { display: flex; gap: 12px; flex-wrap: wrap; }
.qb-stat { min-width: 110px; padding: 10px 14px; }
.qb-stat .stat-label { font-size: 12px; margin-top: 2px; }
.qb-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.qb-actions :deep(.el-button + .el-button) { margin-left: 0; }

.stem-cell { cursor: pointer; }
.stem-tags { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-bottom: 4px; }
.stem-text { font-size: 13px; line-height: 1.5; color: var(--el-text-color-primary); }
.row-ops { display: flex; align-items: center; gap: 2px; flex-wrap: wrap; }
.row-ops :deep(.el-button + .el-button) { margin-left: 0; }
.status-cell { display: inline-flex; align-items: center; gap: 6px; }

.batch-bar {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 8px 0 12px;
}
.batch-bar :deep(.el-button + .el-button) { margin-left: 0; }
.qb-pagination { margin-top: 16px; justify-content: flex-end; }

.detail-tags { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }
.detail-block { margin-bottom: 14px; }
.detail-label { font-weight: 600; margin-bottom: 4px; color: var(--el-text-color-primary); }
.rich-stem { line-height: 1.8; }
.detail-option { line-height: 1.8; }
.detail-analysis { white-space: pre-wrap; line-height: 1.7; color: var(--el-text-color-regular); }

.options-editor { width: 100%; }
.option-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.opt-key {
  width: 24px; height: 24px; line-height: 24px; text-align: center;
  background: #f0f2f5; border-radius: 4px; font-size: 12px; flex-shrink: 0;
}
.err-tip { color: #f56c6c; font-size: 12px; }
.import-result { margin-top: 14px; }
.ai-grade-count { float: right; color: var(--el-text-color-secondary); font-size: 12px; }
.ai-base {
  display: flex; align-items: center; gap: 6px; margin-bottom: 10px;
  padding: 8px 10px; background: var(--el-fill-color-light); border-radius: 4px;
  font-size: 13px;
}
.ai-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
.ai-result-head {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; margin: 12px 0 8px;
}
.quality-issue { display: flex; align-items: center; gap: 6px; line-height: 1.8; }

.muted { color: var(--el-text-color-secondary); font-size: 12px; }
.ml12 { margin-left: 12px; }
.mt8 { margin-top: 8px; }
.mt12 { margin-top: 12px; }
.mb12 { margin-bottom: 12px; }
</style>
