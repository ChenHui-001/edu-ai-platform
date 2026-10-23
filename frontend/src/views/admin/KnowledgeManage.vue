<template>
  <div class="page-container">
    <!-- 顶部：标题 + 统计 + 操作 -->
    <div class="page-header kp-header">
      <div class="kp-title-wrap">
        <h2 class="page-title">知识点管理</h2>
        <div class="kp-stats" v-loading="statsLoading">
          <div v-for="s in statCards" :key="s.label" class="stat-card kp-stat">
            <div class="stat-value">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
      </div>
      <div class="kp-actions">
        <el-button :icon="Refresh" @click="refreshAll">刷新</el-button>
        <el-button v-if="canWrite" :icon="Plus" type="primary" @click="openCreateRoot">新增根节点</el-button>
        <el-button v-if="canWrite" :icon="Upload" @click="openImport">导入</el-button>
        <el-button :icon="Download" @click="exportExcel">导出</el-button>
        <el-button v-if="canWrite" :icon="Cpu" @click="openAiGenerate">AI 生成</el-button>
        <el-popover placement="bottom" :width="300" trigger="hover">
          <template #reference>
            <el-tag size="small" class="rag-tag" :type="ragTagType">{{ ragText }}</el-tag>
          </template>
          <div class="rag-pop">
            <div class="rag-row"><span>库内知识点</span><b>{{ ragStatusData?.db_total ?? '-' }}</b></div>
            <div class="rag-row"><span>已建索引</span><b>{{ ragStatusData?.index_count ?? '-' }}</b></div>
            <div class="rag-row"><span>覆盖率</span><b>{{ ragCoverageText }}</b></div>
            <div class="rag-row"><span>向量库</span>
              <b>{{ ragStatusData?.chroma_available ? '可用' : '不可用/降级' }}</b>
            </div>
            <div class="muted">重建索引后自动刷新状态</div>
          </div>
        </el-popover>
        <el-button v-if="canWrite" :icon="MagicStick" :loading="reindexing" @click="reindex">
          重建索引
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable
                     style="width:130px" @change="onGradeChange">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <!-- 学科按年级配置（同一学科名每个年级各一条），必须先选年级，
               否则拿代表 id 过滤会把其他年级的知识点漏掉 -->
          <el-select v-model="query.subject_id" placeholder="先选年级" clearable
                     :disabled="!query.grade_id" style="width:130px" @change="loadData">
            <el-option v-for="s in subjectOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学期">
          <el-select v-model="query.term" placeholder="全部" clearable style="width:110px" @change="loadData">
            <el-option v-for="t in TERM_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" style="width:120px" :disabled="!isSysAdmin" @change="loadData">
            <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="名称 / 关键词 / 编码" clearable
                    style="width:180px" @keyup.enter="loadData" @clear="loadData" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
          <el-radio-group v-model="viewMode" class="view-switch" @change="onViewModeChange">
            <el-radio-button value="tree">树视图</el-radio-button>
            <el-radio-button value="list">列表视图</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <!-- 语义搜索：走 RAG 向量检索，与上方年级/学科筛选条件组合 -->
      <div class="semantic-row">
        <span class="semantic-label">语义搜索</span>
        <el-input v-model="semanticQuery" placeholder="用自然语言描述要查找的知识点，如：二次函数图像性质"
                  clearable style="width:380px" @keyup.enter="runSemanticSearch">
          <template #append>
            <el-button :icon="Search" :loading="semanticLoading" @click="runSemanticSearch">搜索</el-button>
          </template>
        </el-input>
        <span class="muted">调用 RAG 向量检索（结果低分条目已被阈值过滤）</span>
      </div>
    </el-card>

    <!-- 树视图：左树 + 右详情 -->
    <el-row v-if="viewMode === 'tree'" :gutter="16">
      <el-col :xs="24" :md="9" :lg="8">
        <el-card shadow="never" class="tree-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <b>知识点树</b>
              <span class="muted">{{ treeData.length }} 个根节点</span>
            </div>
          </template>
          <el-input v-model="treeSearch" size="small" placeholder="在当前树内过滤" clearable
                    :prefix-icon="Search" class="tree-search" />
          <el-tree
            ref="treeRef"
            :data="treeData"
            node-key="id"
            default-expand-all
            :default-expanded-keys="allTreeKeys"
            :expand-on-click-node="false"
            highlight-current
            :filter-node-method="filterNode"
            :props="{ label: 'name', children: 'children' }"
            @node-click="onNodeClick"
          >
            <template #default="{ data }">
              <span class="tree-node">
                <span class="tree-name" :title="data.name">{{ data.name }}</span>
                <el-tag size="small" effect="plain" class="tree-level">L{{ data.level }}</el-tag>
                <el-tag v-if="data.question_count" size="small" type="warning" effect="plain">
                  {{ data.question_count }} 题
                </el-tag>
                <el-tag v-if="data.status && data.status !== 'published'" size="small"
                        :type="statusTagType(data.status)">
                  {{ statusLabel(data.status) }}
                </el-tag>
                <span v-if="canWrite" class="tree-ops" @click.stop>
                  <el-button link type="primary" size="small" @click="openCreateChild(data)">子级</el-button>
                  <el-button link type="primary" size="small" @click="editNode(data)">编辑</el-button>
                </span>
              </span>
            </template>
          </el-tree>
          <el-empty v-if="!loading && !treeData.length" description="暂无知识点" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :xs="24" :md="15" :lg="16">
        <el-card shadow="never" class="detail-card" v-loading="detailLoading">
          <template #header>
            <div class="card-header">
              <b>{{ detail ? detail.name : '节点详情' }}</b>
              <div v-if="detail && canWrite" class="detail-head-actions">
                <el-button link type="primary" @click="openCreateChild(detail)">新增子级</el-button>
                <el-button link type="danger" @click="removeNode(detail)">删除</el-button>
              </div>
            </div>
          </template>

          <template v-if="detail">
            <el-breadcrumb separator="/" class="kp-breadcrumb">
              <el-breadcrumb-item v-for="b in breadcrumb" :key="b.id">{{ b.name }}</el-breadcrumb-item>
            </el-breadcrumb>

            <el-descriptions :column="3" border size="small" class="mt12">
              <el-descriptions-item label="年级">{{ detail.grade_name || gradeName(detail.grade_id) }}</el-descriptions-item>
              <el-descriptions-item label="学科">{{ detail.subject_name || subjectName(detail.subject_id) }}</el-descriptions-item>
              <el-descriptions-item label="题目数">{{ detail.question_count ?? 0 }}</el-descriptions-item>
              <el-descriptions-item label="层级">L{{ detail.level }}</el-descriptions-item>
              <el-descriptions-item label="子节点">{{ detail.child_count ?? (detail.children?.length || 0) }}</el-descriptions-item>
              <el-descriptions-item label="来源">{{ sourceLabel(detail.source) }}</el-descriptions-item>
              <el-descriptions-item label="路径">{{ detail.path || '-' }}</el-descriptions-item>
              <el-descriptions-item label="教材版本">{{ detail.textbook_version || '-' }}</el-descriptions-item>
              <el-descriptions-item label="编码">{{ detail.code || '-' }}</el-descriptions-item>
            </el-descriptions>

            <el-form :model="detailForm" label-width="92px" class="mt12">
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="名称">
                    <el-input v-model="detailForm.name" maxlength="128" show-word-limit
                              :disabled="!canWrite" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="状态">
                    <el-select v-model="detailForm.status" style="width:100%" :disabled="!canWrite">
                      <el-option v-for="s in nodeStatusOptions" :key="s.value" :label="s.label" :value="s.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="难度">
                    <el-select v-model="detailForm.difficulty" style="width:100%" :disabled="!canWrite">
                      <el-option v-for="d in DIFFICULTY_OPTIONS" :key="d.value" :label="d.label" :value="d.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="学期">
                    <el-select v-model="detailForm.term" style="width:100%" :disabled="!canWrite">
                      <el-option v-for="t in TERM_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="排序">
                    <el-input-number v-model="detailForm.sort" :min="0" :max="9999"
                                     style="width:100%" :disabled="!canWrite" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="教材版本">
                    <el-input v-model="detailForm.textbook_version" placeholder="如：人教版"
                              :disabled="!canWrite" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="编码">
                    <el-input v-model="detailForm.code" placeholder="如：MATH-FUNC-01"
                              :disabled="!canWrite" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="关键词">
                    <el-input v-model="detailForm.keywords" placeholder="逗号分隔，用于检索"
                              :disabled="!canWrite" />
                  </el-form-item>
                </el-col>
                <el-col :span="24">
                  <el-form-item label="说明">
                    <el-input v-model="detailForm.description" type="textarea" :rows="3"
                              :disabled="!canWrite" />
                  </el-form-item>
                </el-col>
              </el-row>
              <div v-if="canWrite" class="form-actions">
                <el-button type="primary" :loading="savingDetail" @click="saveDetail">保存</el-button>
                <el-button @click="resetDetailForm">重置</el-button>
                <el-button :icon="Cpu" @click="openAiEnrich([detail])">AI 补全</el-button>
                <el-button v-if="isSysAdmin" type="warning" plain @click="openMoveDialog([detail])">
                  移动到其他年级/学科
                </el-button>
              </div>
            </el-form>
          </template>
          <el-empty v-else description="请在左侧选择一个知识点查看详情" :image-size="70" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 列表视图 -->
    <el-card v-else shadow="never">
      <div v-if="canWrite" class="batch-bar">
        <span class="muted">已选 {{ selection.length }} 项</span>
        <el-button size="small" :disabled="!selection.length" @click="batchStatus('publish')">批量发布</el-button>
        <el-button size="small" :disabled="!selection.length" @click="batchStatus('archive')">批量归档</el-button>
        <el-button size="small" :disabled="!selection.length" @click="openMoveDialog(selection)">批量移动</el-button>
        <el-button size="small" :icon="Cpu" :disabled="!selection.length"
                   @click="openAiEnrich(selection)">AI 补全</el-button>
        <el-button size="small" type="danger" plain :disabled="!selection.length"
                   @click="batchDelete">批量删除</el-button>
      </div>

      <el-table v-loading="loading" :data="listData" row-key="id" border stripe
                @selection-change="onSelectionChange">
        <el-table-column type="selection" width="44" />
        <el-table-column prop="name" label="名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="层级" width="70" align="center">
          <template #default="{ row }">L{{ row.level }}</template>
        </el-table-column>
        <el-table-column label="年级" width="100">
          <template #default="{ row }">{{ row.grade_name || gradeName(row.grade_id) }}</template>
        </el-table-column>
        <el-table-column label="学科" width="100">
          <template #default="{ row }">{{ row.subject_name || subjectName(row.subject_id) }}</template>
        </el-table-column>
        <el-table-column label="学期" width="80" align="center">
          <template #default="{ row }">{{ termLabel(row.term) }}</template>
        </el-table-column>
        <el-table-column label="难度" width="80" align="center">
          <template #default="{ row }">{{ difficultyLabel(row.difficulty) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="question_count" label="题目数" width="90" align="center" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewNode(row)">详情</el-button>
            <el-button v-if="canWrite" link type="primary" @click="editNode(row)">编辑</el-button>
            <el-button v-if="canWrite" link type="danger" @click="removeNode(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增 / 编辑对话框（根节点、子级、列表编辑共用） -->
    <el-dialog v-model="editDlg" :title="editForm.id ? '编辑知识点' : '新增知识点'" width="640px">
      <el-form :model="editForm" label-width="96px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="所属年级" required>
              <el-select v-model="editForm.grade_id" :disabled="!!editForm.id"
                         style="width:100%" @change="onEditGradeChange">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属学科" required>
              <el-select v-model="editForm.subject_id" :disabled="!!editForm.id"
                         placeholder="请选择学科" style="width:100%" @change="loadEditParentTree">
                <el-option v-for="s in editSubjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="名称" required>
              <el-input v-model="editForm.name" maxlength="128" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="上级节点">
              <el-tree-select
                v-model="editForm.parent_id"
                :data="editParentTree"
                node-key="id"
                :props="{ label: 'name', children: 'children' }"
                check-strictly
                clearable
                filterable
                placeholder="不选则为根节点"
                style="width:100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学期">
              <el-select v-model="editForm.term" style="width:100%">
                <el-option v-for="t in TERM_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="难度">
              <el-select v-model="editForm.difficulty" style="width:100%">
                <el-option v-for="d in DIFFICULTY_OPTIONS" :key="d.value" :label="d.label" :value="d.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="editForm.status" style="width:100%">
                <el-option v-for="s in nodeStatusOptions" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="editForm.sort" :min="0" :max="9999" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教材版本">
              <el-input v-model="editForm.textbook_version" placeholder="如：人教版" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="编码">
              <el-input v-model="editForm.code" placeholder="非空时不可重复" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="关键词">
              <el-input v-model="editForm.keywords" placeholder="逗号分隔" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="说明">
              <el-input v-model="editForm.description" type="textarea" :rows="3" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="editDlg = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 移动（契约无 copy，跨年级/学科仅管理员） -->
    <el-dialog v-model="moveDlg" title="移动知识点" width="560px">
      <el-alert type="warning" :closable="false" show-icon
                title="移动会改变所选节点及其所有子级的归属；契约暂未提供「复制」接口，跨年级/学科移动仅管理员可用" />
      <el-form label-width="96px" class="mt12">
        <el-form-item label="目标年级">
          <el-select v-model="moveForm.grade_id" :disabled="!isSysAdmin" style="width:100%"
                     @change="onMoveScopeChange">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标学科">
          <el-select v-model="moveForm.subject_id" :disabled="!isSysAdmin" style="width:100%"
                     placeholder="请选择学科" @change="onMoveScopeChange">
            <el-option v-for="s in moveSubjectOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标父节点">
          <el-tree-select
            v-model="moveForm.parent_id"
            :data="moveTree"
            node-key="id"
            :props="{ label: 'name', children: 'children' }"
            check-strictly
            clearable
            filterable
            placeholder="不选则移动到根节点"
            style="width:100%"
          />
        </el-form-item>
      </el-form>
      <div class="muted">已选中 {{ moveNodes.length }} 个节点</div>
      <template #footer>
        <el-button @click="moveDlg = false">取消</el-button>
        <el-button type="primary" :loading="moveLoading" @click="confirmMove">确认移动</el-button>
      </template>
    </el-dialog>

    <!-- 导入：模板 → 上传 → dry-run → 确认导入 → 结果汇总 -->
    <el-dialog v-model="importDlg" title="批量导入知识点" width="760px">
      <el-alert type="info" :closable="false" show-icon class="mb12">
        <template #title>
          先下载模板填写（年级、学科、教材版本、学期、单元、章节、知识点、难度、关键词、说明、编码）。
        </template>
        <el-link type="primary" :underline="false" @click="downloadTemplate">下载导入模板</el-link>
      </el-alert>
      <el-upload
        drag
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls,.csv"
        v-model:file-list="importFileList"
        :on-change="onImportFileChange"
        :on-remove="onImportFileRemove"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将 xlsx / csv 拖到此处，或 <em>点击选择文件</em></div>
      </el-upload>

      <div class="import-actions">
        <el-button :loading="importing" :disabled="!importFile" @click="runImport(true)">预检（dry-run）</el-button>
        <el-button type="primary" :loading="importing"
                   :disabled="!importFile || !importResult || !importResult.dry_run"
                   @click="runImport(false)">确认导入</el-button>
        <span class="muted">需先预检通过再导入；有错误的行不会写入，可按 errors 修正后重试</span>
      </div>

      <template v-if="importResult">
        <el-alert
          class="mt12"
          :type="importResult.errors.length ? 'warning' : 'success'"
          :closable="false"
          show-icon
          :title="importResult.dry_run
            ? `预检完成：新增 ${importResult.created}，更新 ${importResult.updated}，跳过 ${importResult.skipped.length}，错误 ${importResult.errors.length}`
            : `导入完成：新增 ${importResult.created}，更新 ${importResult.updated}，跳过 ${importResult.skipped.length}，错误 ${importResult.errors.length}`"
        />
        <el-table v-if="importResult.errors.length" :data="importResult.errors" size="small"
                  border max-height="180" class="mt8">
          <el-table-column prop="row" label="行号" width="80" />
          <el-table-column prop="message" label="错误原因" show-overflow-tooltip />
        </el-table>
        <el-table v-if="importResult.skipped.length" :data="importResult.skipped" size="small"
                  border max-height="180" class="mt8">
          <el-table-column prop="row" label="行号" width="80" />
          <el-table-column prop="reason" label="跳过原因" show-overflow-tooltip />
        </el-table>
      </template>

      <template #footer>
        <el-button @click="importDlg = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- AI 生成知识点：只返回预览，勾选后逐条创建到当前选中节点/根节点下 -->
    <el-dialog v-model="aiGenDlg" title="AI 生成知识点" width="900px" @opened="syncAiGenSelection">
      <el-form :model="aiGenForm" label-width="92px">
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="年级" required>
              <el-select v-model="aiGenForm.grade_id" style="width:100%" @change="onAiGenGradeChange">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学科" required>
              <el-select v-model="aiGenForm.subject_id" :disabled="!aiGenForm.grade_id"
                         placeholder="请选择学科" style="width:100%">
                <el-option v-for="s in aiGenSubjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="数量">
              <el-input-number v-model="aiGenForm.count" :min="3" :max="12" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单元名称">
              <el-input v-model="aiGenForm.unit_name" maxlength="64" placeholder="可选，如：二次函数" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="主题">
              <el-input v-model="aiGenForm.topic" maxlength="128" placeholder="可选，如：二次函数图像与性质" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="教材版本">
              <el-input v-model="aiGenForm.textbook_version" placeholder="如：人教版" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学期">
              <el-select v-model="aiGenForm.term" style="width:100%">
                <el-option v-for="t in TERM_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="创建位置">
              <el-input :model-value="aiTargetLabel" disabled />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <div class="ai-actions">
        <el-button type="primary" :loading="aiGenLoading" @click="runAiGenerate">生成预览</el-button>
        <span class="muted">只生成预览不落库；确认后勾选“创建选中”逐条写入</span>
      </div>

      <el-alert v-if="aiGenResult?.is_fallback" class="mt12" type="warning" :closable="false" show-icon
                title="当前无可用大模型，结果为规则引擎降级生成（is_fallback=true）" />

      <template v-if="aiGenResult && aiGenResult.points.length">
        <div class="ai-result-head">
          <b>{{ aiGenResult.unit_name || aiGenForm.unit_name || aiGenForm.topic || '生成结果' }}</b>
          <span class="muted">共 {{ aiGenResult.points.length }} 条，已选 {{ aiGenSelected.length }} 条</span>
        </div>
        <el-table ref="aiGenTableRef" :data="aiGenResult.points" size="small" border
                  max-height="320" @selection-change="onAiGenSelectionChange">
          <el-table-column type="selection" width="42" />
          <el-table-column prop="name" label="名称" width="180" show-overflow-tooltip />
          <el-table-column prop="description" label="说明" min-width="240" show-overflow-tooltip />
          <el-table-column prop="keywords" label="关键词" width="140" show-overflow-tooltip />
          <el-table-column label="难度" width="80" align="center">
            <template #default="{ row }">{{ difficultyLabel(row.difficulty) }}</template>
          </el-table-column>
        </el-table>
      </template>

      <template #footer>
        <el-button @click="aiGenDlg = false">关闭</el-button>
        <el-button type="primary" :loading="aiGenCreating" :disabled="!aiGenSelected.length"
                   @click="createAiPoints">
          创建选中（{{ aiGenSelected.length }}）
        </el-button>
      </template>
    </el-dialog>

    <!-- AI 补全：预览 description/keywords/difficulty，确认后逐条 PUT -->
    <el-dialog v-model="aiEnrichDlg" title="AI 补全知识点" width="920px" @opened="syncAiEnrichSelection">
      <el-alert v-if="aiEnrichFallback" class="mb12" type="warning" :closable="false" show-icon
                title="当前无可用大模型，建议为规则引擎降级结果（is_fallback=true）" />
      <div class="ai-result-head">
        <b>补全建议</b>
        <span class="muted">
          共 {{ aiEnrichItems.length }} 条，已选 {{ aiEnrichSelected.length }} 条；应用时仅更新说明/关键词/难度
        </span>
      </div>
      <el-table ref="aiEnrichTableRef" v-loading="aiEnrichLoading" :data="aiEnrichItems"
                size="small" border max-height="380" @selection-change="onAiEnrichSelectionChange">
        <el-table-column type="selection" width="42" />
        <el-table-column prop="name" label="名称" width="170" show-overflow-tooltip />
        <el-table-column prop="description" label="建议说明" min-width="280" show-overflow-tooltip />
        <el-table-column prop="keywords" label="建议关键词" width="160" show-overflow-tooltip />
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

    <!-- 语义搜索结果：点击定位到树节点 -->
    <el-dialog v-model="semanticDlg" title="语义搜索结果" width="780px">
      <div class="muted mb8">查询：{{ semanticQuery }}</div>
      <el-table :data="semanticResults" size="small" border max-height="440">
        <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="path" label="路径" width="130" show-overflow-tooltip />
        <el-table-column label="得分" width="90" align="center">
          <template #default="{ row }">{{ formatScore(row.score) }}</template>
        </el-table-column>
        <el-table-column prop="question_count" label="题目数" width="90" align="center" />
        <el-table-column label="操作" width="90" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="locateFromSearch(row)">定位</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!semanticResults.length" description="未检索到相关知识点" :image-size="70" />
      <template #footer>
        <el-button @click="semanticDlg = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Plus, Upload, Download, Search, MagicStick, UploadFilled, Cpu
} from '@element-plus/icons-vue'
import { eduApi, knowledgeApi } from '@/api'
import { useUserStore } from '@/store/user'
import { downloadBlob } from '@/utils/download'
import { formatLocalDate } from '@/utils/date'

const userStore = useUserStore()
const { can } = userStore
const canWrite = computed(() => can('resource:knowledge:write'))
const isSysAdmin = computed(() => userStore.isAdmin === true)

// ---------------- 常量 / 展示映射 ----------------
const TERM_OPTIONS = [
  { value: 1, label: '上册' },
  { value: 2, label: '下册' }
]
const DIFFICULTY_OPTIONS = [
  { value: 'easy', label: '简单' },
  { value: 'medium', label: '中等' },
  { value: 'hard', label: '困难' }
]
const STATUS_LABELS = { draft: '草稿', published: '已发布', archived: '已归档' }
const STATUS_TYPES = { draft: 'info', published: 'success', archived: 'warning' }
const SOURCE_LABELS = { manual: '手工创建', import: '批量导入', ai: 'AI 生成', seed: '系统预置' }

const statusOptions = computed(() => {
  const base = [{ value: 'published', label: '已发布' }]
  if (isSysAdmin.value) {
    base.push({ value: 'draft', label: '草稿' }, { value: 'archived', label: '已归档' },
      { value: 'all', label: '全部状态' })
  }
  return base
})
// 节点自身的 status 只能是 draft/published/archived（"全部状态"仅用于筛选）
const nodeStatusOptions = computed(() => statusOptions.value.filter(s => s.value !== 'all'))

function statusLabel(v) { return STATUS_LABELS[v] || v || '-' }
function statusTagType(v) { return STATUS_TYPES[v] || 'info' }
function difficultyLabel(v) {
  return DIFFICULTY_OPTIONS.find(d => d.value === v)?.label || v || '-'
}
function termLabel(v) {
  return TERM_OPTIONS.find(t => t.value === Number(v))?.label || (v ? `第${v}学期` : '-')
}
function sourceLabel(v) { return SOURCE_LABELS[v] || v || '-' }

// ---------------- 基础数据 ----------------
const grades = ref([])
const subjects = ref([])
const query = reactive({ grade_id: null, subject_id: null, term: null, status: 'published', keyword: '' })
const viewMode = ref('tree')
const treeSearch = ref('')

const subjectOptions = computed(() => {
  if (!query.grade_id) return []
  return subjects.value.filter(s => s.grade_id === query.grade_id)
})

function normalizeArray(d) {
  if (Array.isArray(d)) return d
  return d?.items || d?.data || []
}

async function loadOptions() {
  try {
    const [g, s] = await Promise.all([eduApi.grades(), eduApi.subjects()])
    grades.value = normalizeArray(g.data)
    subjects.value = normalizeArray(s.data)
  } catch { /* 请求拦截器已统一提示 */ }
}

function gradeName(id) { return grades.value.find(g => g.id === id)?.name || '-' }
function subjectName(id) { return subjects.value.find(s => s.id === id)?.name || '-' }

// ---------------- 统计 ----------------
const stats = ref({})
const statsLoading = ref(false)
const statCards = computed(() => {
  const d = stats.value || {}
  const cards = [
    { label: '知识点总数', value: d.total ?? '-' },
    { label: '已发布', value: d.published ?? '-' },
    { label: '关联题目数', value: d.with_questions ?? '-' }
  ]
  if (isSysAdmin.value) cards.push({ label: '草稿', value: d.draft ?? '-' })
  return cards
})

// ---------------- 筛选 / 加载 ----------------
function buildParams() {
  const params = {}
  if (query.grade_id) params.grade_id = query.grade_id
  if (query.subject_id) params.subject_id = query.subject_id
  if (query.term) params.term = query.term
  if (query.keyword.trim()) params.keyword = query.keyword.trim()
  if (query.status) params.status = query.status
  return params
}

const treeData = ref([])
const listData = ref([])
const loading = ref(false)
// 数据整体替换后 default-expand-all 不会重新生效，显式提供全部节点 key 保持展开
const allTreeKeys = computed(() => collectNodes(treeData.value).map(n => n.id))

async function loadStats(params) {
  statsLoading.value = true
  try {
    const res = await knowledgeApi.stats(params)
    stats.value = res.data || {}
  } catch {
    // 统计失败不影响主列表展示（例如后端该接口尚未上线）
  } finally {
    statsLoading.value = false
  }
}

async function loadTree(params) {
  const res = await knowledgeApi.tree(params)
  treeData.value = normalizeArray(res.data)
  // 服务端已按 keyword 过滤，这里再套一层 el-tree 本地过滤，保证输入即时生效
  await nextTick()
  if (query.keyword.trim()) treeRef.value?.filter(query.keyword.trim())
}

async function loadList(params) {
  const res = await knowledgeApi.list(params)
  listData.value = normalizeArray(res.data)
  selection.value = []
}

async function loadData() {
  loading.value = true
  try {
    const params = buildParams()
    const tasks = [loadStats(params)]
    if (viewMode.value === 'tree') tasks.push(loadTree(params))
    else tasks.push(loadList(params))
    await Promise.all(tasks)
    if (viewMode.value === 'tree' && selectedId.value) {
      const node = findNode(treeData.value, selectedId.value)
      if (node) {
        await loadDetail(selectedId.value, false)
        // 树数据整体替换后高亮会丢失，这里恢复当前选中节点
        await nextTick()
        treeRef.value?.setCurrentKey(selectedId.value)
      } else {
        clearSelection()
      }
    }
  } catch (e) {
    // 单接口失败时保持页面可用（请求拦截器已提示具体错误）
  } finally {
    loading.value = false
  }
}

function refreshAll() {
  loadData()
  loadRagStatus()
}

function resetQuery() {
  Object.assign(query, {
    grade_id: null, subject_id: null, term: null, status: 'published', keyword: ''
  })
  treeSearch.value = ''
  loadData()
}

function onGradeChange() {
  // 换年级后原学科 id 已不属于该年级，必须清空
  query.subject_id = null
  loadData()
}

async function onViewModeChange() {
  // 两种视图的取数接口不同（tree vs 平铺 list），切换后重新加载
  await loadData()
  await nextTick()
  if (viewMode.value === 'tree' && selectedId.value) {
    treeRef.value?.setCurrentKey(selectedId.value)
  }
}

// ---------------- 树 ----------------
const treeRef = ref(null)
const selectedId = ref(null)
const detail = ref(null)
const detailLoading = ref(false)
const savingDetail = ref(false)
const breadcrumb = ref([])
const detailForm = reactive({
  name: '', description: '', keywords: '', difficulty: 'medium',
  term: 1, sort: 0, status: 'published', textbook_version: '', code: ''
})

function filterNode(value, data) {
  const kw = String(value || '').trim().toLowerCase()
  if (!kw) return true
  return String(data.name || '').toLowerCase().includes(kw)
    || String(data.keywords || '').toLowerCase().includes(kw)
    || String(data.code || '').toLowerCase().includes(kw)
}

watch(treeSearch, (v) => treeRef.value?.filter(v))

function collectNodes(nodes, acc = []) {
  for (const n of nodes || []) {
    acc.push(n)
    if (n.children?.length) collectNodes(n.children, acc)
  }
  return acc
}

function findNode(nodes, id) {
  if (!id) return null
  for (const n of nodes || []) {
    if (n.id === id) return n
    const hit = findNode(n.children || [], id)
    if (hit) return hit
  }
  return null
}

function buildBreadcrumb(node) {
  const map = new Map(collectNodes(treeData.value).map(n => [n.id, n]))
  const chain = []
  const seen = new Set()
  let cur = node
  while (cur && !seen.has(cur.id)) {
    seen.add(cur.id)
    chain.unshift({ id: cur.id, name: cur.name })
    cur = cur.parent_id ? map.get(cur.parent_id) : null
  }
  return chain
}

function applyDetail(node) {
  detail.value = node
  breadcrumb.value = Array.isArray(node?.breadcrumb) && node.breadcrumb.length
    ? node.breadcrumb
    : buildBreadcrumb(node)
  Object.assign(detailForm, {
    name: node?.name || '',
    description: node?.description || '',
    keywords: node?.keywords || '',
    difficulty: node?.difficulty || 'medium',
    term: node?.term ?? 1,
    sort: node?.sort ?? 0,
    status: node?.status || 'published',
    textbook_version: node?.textbook_version || '',
    code: node?.code || ''
  })
}

function clearSelection() {
  selectedId.value = null
  detail.value = null
  breadcrumb.value = []
}

async function loadDetail(id, withLoading = true) {
  if (withLoading) detailLoading.value = true
  try {
    const res = await knowledgeApi.get(id)
    applyDetail(res.data || {})
  } catch {
    // 详情接口不可用（或节点刚被删）时回退到树/列表里已有的节点数据
    const node = findNode(treeData.value, id) || listData.value.find(n => n.id === id)
    if (node) applyDetail(node)
    else clearSelection()
  } finally {
    if (withLoading) detailLoading.value = false
  }
}

async function onNodeClick(data) {
  selectedId.value = data.id
  await loadDetail(data.id)
}

function resetDetailForm() {
  if (detail.value) applyDetail(detail.value)
}

async function saveDetail() {
  if (!detail.value) return
  if (!detailForm.name.trim()) return ElMessage.warning('名称不能为空')
  savingDetail.value = true
  try {
    await knowledgeApi.update(detail.value.id, {
      name: detailForm.name.trim(),
      description: detailForm.description,
      keywords: detailForm.keywords,
      difficulty: detailForm.difficulty,
      term: detailForm.term,
      sort: detailForm.sort,
      status: detailForm.status,
      textbook_version: detailForm.textbook_version,
      code: detailForm.code
    })
    ElMessage.success('保存成功')
    await loadData()
    await loadDetail(detail.value.id, false)
  } finally {
    savingDetail.value = false
  }
}

// ---------------- 新增 / 编辑 ----------------
const editDlg = ref(false)
const editSaving = ref(false)
const editForm = reactive({
  id: null, name: '', grade_id: null, subject_id: null, parent_id: null,
  textbook_version: '', term: 1, description: '', difficulty: 'medium',
  keywords: '', code: '', sort: 0, status: 'published'
})
const editSubjects = computed(() => subjects.value.filter(s => s.grade_id === editForm.grade_id))

// 上级节点候选：按「目标年级+学科」实时拉取整棵树（不受当前筛选影响），
// 并排除被编辑节点自身及其后代，避免形成环。
const editParentTree = ref([])

async function loadEditParentTree() {
  if (!editForm.grade_id || !editForm.subject_id) {
    editParentTree.value = []
    return
  }
  try {
    const res = await knowledgeApi.tree({
      grade_id: editForm.grade_id,
      subject_id: editForm.subject_id,
      status: isSysAdmin.value ? 'all' : 'published'
    })
    const raw = normalizeArray(res.data)
    const exclude = new Set()
    if (editForm.id) {
      const self = findNode(raw, editForm.id)
      if (self) collectSubtree(self, exclude)
      else exclude.add(editForm.id)
    }
    editParentTree.value = pruneTree(raw, exclude)
  } catch {
    editParentTree.value = []
  }
}

function pruneTree(list, excludeIds) {
  return (list || [])
    .filter(n => !excludeIds.has(n.id))
    .map(n => ({ ...n, children: pruneTree(n.children || [], excludeIds) }))
}

function resetEditForm() {
  Object.assign(editForm, {
    id: null, name: '', grade_id: null, subject_id: null, parent_id: null,
    textbook_version: '', term: 1, description: '', difficulty: 'medium',
    keywords: '', code: '', sort: 0, status: 'published'
  })
}

function openCreateRoot() {
  if (!canWrite.value) return
  resetEditForm()
  editForm.grade_id = query.grade_id || null
  editForm.subject_id = query.subject_id || null
  editForm.term = query.term || 1
  editDlg.value = true
  loadEditParentTree()
}

function openCreateChild(parent) {
  if (!canWrite.value || !parent) return
  resetEditForm()
  editForm.grade_id = parent.grade_id
  editForm.subject_id = parent.subject_id
  editForm.parent_id = parent.id
  editForm.term = parent.term ?? 1
  editForm.status = parent.status || 'published'
  editForm.textbook_version = parent.textbook_version || ''
  editDlg.value = true
  loadEditParentTree()
}

function editNode(row) {
  if (!canWrite.value || !row) return
  Object.assign(editForm, {
    id: row.id,
    name: row.name || '',
    grade_id: row.grade_id ?? null,
    subject_id: row.subject_id ?? null,
    parent_id: row.parent_id ?? null,
    textbook_version: row.textbook_version || '',
    term: row.term ?? 1,
    description: row.description || '',
    difficulty: row.difficulty || 'medium',
    keywords: row.keywords || '',
    code: row.code || '',
    sort: row.sort ?? 0,
    status: row.status || 'published'
  })
  editDlg.value = true
  loadEditParentTree()
}

function onEditGradeChange() {
  editForm.subject_id = null
  editForm.parent_id = null
  // 学科未选前无法确定父节点候选范围
  editParentTree.value = []
}

async function saveEdit() {
  if (!editForm.name.trim()) return ElMessage.warning('请输入知识点名称')
  if (!editForm.grade_id || !editForm.subject_id) return ElMessage.warning('请选择年级与学科')
  editSaving.value = true
  try {
    let res
    if (editForm.id) {
      // grade/subject 不允许修改（契约：跨年级/学科走批量 move）
      res = await knowledgeApi.update(editForm.id, {
        name: editForm.name.trim(),
        parent_id: editForm.parent_id ?? null,
        textbook_version: editForm.textbook_version,
        term: editForm.term,
        description: editForm.description,
        difficulty: editForm.difficulty,
        keywords: editForm.keywords,
        code: editForm.code,
        sort: editForm.sort,
        status: editForm.status
      })
    } else {
      res = await knowledgeApi.create({
        name: editForm.name.trim(),
        grade_id: editForm.grade_id,
        subject_id: editForm.subject_id,
        parent_id: editForm.parent_id ?? null,
        textbook_version: editForm.textbook_version,
        term: editForm.term,
        description: editForm.description,
        difficulty: editForm.difficulty,
        keywords: editForm.keywords,
        code: editForm.code,
        sort: editForm.sort,
        status: editForm.status
      })
    }
    ElMessage.success(editForm.id ? '保存成功' : '创建成功')
    editDlg.value = false
    await loadData()
    const newId = res.data?.id || editForm.id
    if (newId) {
      selectedId.value = newId
      await loadDetail(newId, false)
      await nextTick()
      treeRef.value?.setCurrentKey(newId)
    }
  } finally {
    editSaving.value = false
  }
}

// ---------------- 删除 ----------------
async function removeNode(row) {
  if (!canWrite.value || !row) return
  const childCount = row.child_count ?? (row.children?.length || 0)
  const questionCount = row.question_count ?? 0
  const impact = []
  if (childCount) impact.push(`含 ${childCount} 个子节点`)
  if (questionCount) impact.push(`关联 ${questionCount} 道题目`)
  const tip = impact.length
    ? `${impact.join('，')}；后端会拒绝删除仍有子节点/被引用的知识点。`
    : '删除后不可恢复。'
  try {
    await ElMessageBox.confirm(`确认删除知识点「${row.name}」？${tip}`, '删除确认',
      { type: 'warning', confirmButtonText: '确认删除' })
  } catch { return }
  await knowledgeApi.remove(row.id)
  ElMessage.success('已删除')
  if (detail.value?.id === row.id) clearSelection()
  await loadData()
}

// ---------------- 批量 ----------------
const selection = ref([])
function onSelectionChange(val) { selection.value = val || [] }

async function batchStatus(action) {
  const ids = selection.value.map(n => n.id)
  if (!ids.length) return ElMessage.warning('请先勾选知识点')
  const label = action === 'publish' ? '发布' : '归档'
  try {
    const res = await knowledgeApi.batch({ action, ids, payload: {} })
    reportBatchResult(res.data, `已${label}`)
    selection.value = []
    await loadData()
  } catch { /* 拦截器已提示 */ }
}

async function batchDelete() {
  const ids = selection.value.map(n => n.id)
  if (!ids.length) return ElMessage.warning('请先勾选知识点')
  try {
    await ElMessageBox.confirm(
      `将尝试删除 ${ids.length} 个知识点；有子节点或被题目/掌握度引用的会被跳过（后端逐个校验），删除不可恢复。`,
      '批量删除确认', { type: 'warning', confirmButtonText: '确认删除' })
  } catch { return }
  try {
    const res = await knowledgeApi.batch({ action: 'delete', ids, payload: {} })
    reportBatchResult(res.data, '已删除')
    selection.value = []
    await loadData()
  } catch { /* 拦截器已提示 */ }
}

function reportBatchResult(data, prefix) {
  const d = data || {}
  const done = d.done?.length || 0
  const skipped = d.skipped || []
  if (skipped.length) {
    const reasons = skipped.slice(0, 3).map(s => s.reason || `#${s.id}`).join('；')
    ElMessage.warning(`${prefix} ${done} 个，跳过 ${skipped.length} 个：${reasons}`)
  } else {
    ElMessage.success(`${prefix} ${done} 个知识点`)
  }
}

// ---------------- 移动 ----------------
const moveDlg = ref(false)
const moveNodes = ref([])
const moveTree = ref([])
const moveLoading = ref(false)
const moveForm = reactive({ grade_id: null, subject_id: null, parent_id: null })
const moveSubjectOptions = computed(() => subjects.value.filter(s => s.grade_id === moveForm.grade_id))

function openMoveDialog(nodes) {
  if (!canWrite.value) return
  const list = (nodes || []).filter(Boolean)
  if (!list.length) return ElMessage.warning('请先选择要移动的知识点')
  const scopes = new Set(list.map(n => `${n.grade_id}:${n.subject_id}`))
  if (scopes.size > 1) return ElMessage.warning('批量移动仅支持同一「年级 + 学科」下的节点')
  moveNodes.value = list
  moveForm.grade_id = list[0].grade_id
  moveForm.subject_id = list[0].subject_id
  moveForm.parent_id = null
  moveDlg.value = true
  loadMoveTree()
}

function onMoveScopeChange() {
  moveForm.parent_id = null
  loadMoveTree()
}

async function loadMoveTree() {
  if (!moveForm.grade_id || !moveForm.subject_id) { moveTree.value = []; return }
  moveLoading.value = true
  try {
    const res = await knowledgeApi.tree({
      grade_id: moveForm.grade_id,
      subject_id: moveForm.subject_id,
      status: isSysAdmin.value ? 'all' : 'published'
    })
    const raw = normalizeArray(res.data)
    // 目标父节点不能是「被移动节点自身或其子级」，否则形成环
    const exclude = new Set()
    const mark = (nodes) => {
      for (const n of nodes || []) {
        if (moveNodes.value.some(m => m.id === n.id)) collectSubtree(n, exclude)
        else mark(n.children || [])
      }
    }
    mark(raw)
    moveTree.value = pruneTree(raw, exclude)
  } catch {
    moveTree.value = []
  } finally {
    moveLoading.value = false
  }
}

function collectSubtree(node, acc) {
  acc.add(node.id)
  for (const c of node.children || []) collectSubtree(c, acc)
}

async function confirmMove() {
  const ids = moveNodes.value.map(n => n.id)
  if (!ids.length) return
  const payload = { parent_id: moveForm.parent_id ?? null }
  if (isSysAdmin.value) {
    payload.grade_id = moveForm.grade_id
    payload.subject_id = moveForm.subject_id
  }
  // 移动会改变子树归属（契约暂无 copy），提交前再确认一次
  const target = `${gradeName(moveForm.grade_id) || '-'} / ${subjectName(moveForm.subject_id) || '-'}`
  try {
    await ElMessageBox.confirm(
      `确认将 ${ids.length} 个知识点及其所有子级移动到「${target}」${moveForm.parent_id ? '的目标父节点下' : '的根节点'}？此操作不会复制数据，且跨年级/学科移动不可自动回滚。`,
      '移动确认', { type: 'warning', confirmButtonText: '确认移动' })
  } catch { return }
  moveLoading.value = true
  try {
    const res = await knowledgeApi.batch({ action: 'move', ids, payload })
    reportBatchResult(res.data, '已移动')
    moveDlg.value = false
    selection.value = []
    if (selectedId.value && ids.includes(selectedId.value)) clearSelection()
    await loadData()
  } catch { /* 拦截器已提示 */ } finally {
    moveLoading.value = false
  }
}

// ---------------- 导入 / 导出 ----------------
const importDlg = ref(false)
const importFile = ref(null)
const importFileList = ref([])
const importing = ref(false)
const importResult = ref(null)

const reindexing = ref(false)

function openImport() {
  if (!canWrite.value) return
  importFile.value = null
  importFileList.value = []
  importResult.value = null
  importDlg.value = true
}

function onImportFileChange(file) {
  const name = String(file?.name || '').toLowerCase()
  if (!/\.(xlsx|xls|csv)$/.test(name)) {
    ElMessage.warning('仅支持 .xlsx / .xls / .csv 文件')
    importFile.value = null
    importFileList.value = []
    return
  }
  importFile.value = file.raw
  importFileList.value = [file]
  importResult.value = null
}

function onImportFileRemove() {
  importFile.value = null
  importFileList.value = []
}

async function downloadTemplate() {
  await downloadBlob(knowledgeApi.template(), '知识点导入模板.xlsx')
}

async function runImport(dryRun) {
  if (!importFile.value) return ElMessage.warning('请先选择文件')
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', importFile.value)
    fd.append('dry_run', String(dryRun))
    const res = await knowledgeApi.import(fd)
    const d = res.data || {}
    importResult.value = {
      dry_run: dryRun,
      created: d.created || 0,
      updated: d.updated || 0,
      skipped: d.skipped || [],
      errors: d.errors || []
    }
    if (dryRun) {
      if (importResult.value.errors.length) {
        ElMessage.warning(`预检完成：${importResult.value.errors.length} 行有错误，请修正后重新预检`)
      } else {
        ElMessage.success(`预检通过：将新增 ${importResult.value.created} 行、更新 ${importResult.value.updated} 行`)
      }
    } else {
      ElMessage.success(`导入完成：新增 ${importResult.value.created}，更新 ${importResult.value.updated}`)
      await loadData()
    }
  } finally {
    importing.value = false
  }
}

async function exportExcel() {
  const params = buildParams()
  const stamp = formatLocalDate(new Date()) || ''
  await downloadBlob(knowledgeApi.export(params), `知识点_${stamp}.xlsx`)
}

async function reindex() {
  try {
    await ElMessageBox.confirm(
      '将重建知识点向量索引，耗时取决于知识点数量，确认继续？', '重建向量索引', { type: 'info' })
  } catch { return }
  reindexing.value = true
  try {
    const res = await knowledgeApi.reindex()
    const d = res.data || {}
    const extra = d.index_count != null
      ? `（已索引 ${d.index_count} 条，覆盖率 ${d.coverage_percent ?? '-'}%）`
      : ''
    ElMessage.success((res.message || '向量索引重建完成') + extra)
    // 重建后立即刷新状态标签
    await loadRagStatus()
  } finally {
    reindexing.value = false
  }
}

// ---------------- RAG 索引状态 ----------------
const ragStatusData = ref(null)
const ragCoverageText = computed(() => {
  const v = ragStatusData.value?.coverage_percent
  if (v === null || v === undefined || v === '') return '-'
  const n = Number(v)
  return Number.isFinite(n) ? `${n.toFixed(1)}%` : String(v)
})
const ragTagType = computed(() => {
  const d = ragStatusData.value
  if (!d) return 'info'
  if (d.chroma_available === false) return 'warning'
  const n = Number(d.coverage_percent)
  return Number.isFinite(n) && n >= 99.9 ? 'success' : 'warning'
})
const ragText = computed(() => {
  const d = ragStatusData.value
  if (!d) return '索引状态未知'
  if (d.chroma_available === false) return '向量库不可用'
  return `索引 ${d.index_count ?? '-'}/${d.db_total ?? '-'}（${ragCoverageText.value}）`
})

async function loadRagStatus() {
  try {
    const res = await knowledgeApi.ragStatus()
    ragStatusData.value = res.data || null
  } catch {
    // 后端 RAG 接口未就绪时保持「未知」，不阻断页面
    ragStatusData.value = null
  }
}

// ---------------- 语义搜索（RAG） ----------------
const semanticQuery = ref('')
const semanticDlg = ref(false)
const semanticLoading = ref(false)
const semanticResults = ref([])

function formatScore(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n.toFixed(3) : '-'
}

async function runSemanticSearch() {
  const q = semanticQuery.value.trim()
  if (!q) return ElMessage.warning('请输入语义搜索内容')
  semanticLoading.value = true
  try {
    const params = { q, limit: 10 }
    if (query.grade_id) params.grade_id = query.grade_id
    if (query.subject_id) params.subject_id = query.subject_id
    const res = await knowledgeApi.search(params)
    semanticResults.value = normalizeArray(res.data)
    semanticDlg.value = true
    if (!semanticResults.value.length) ElMessage.info('未检索到相关知识点')
  } finally {
    semanticLoading.value = false
  }
}

/** 点击搜索结果定位到树节点：必要时切换筛选条件并展开/滚动到该节点。 */
async function locateFromSearch(item) {
  if (!item?.id) return
  semanticDlg.value = false
  viewMode.value = 'tree'
  // 命中节点可能被当前筛选条件隐藏：切到节点所属年级/学科并清空其余筛选
  query.grade_id = item.grade_id || null
  query.subject_id = item.subject_id || null
  query.term = null
  query.keyword = ''
  query.status = 'published'
  treeSearch.value = ''
  await loadData()
  let node = findNode(treeData.value, item.id)
  if (!node && isSysAdmin.value) {
    // RAG 只索引 published；管理员再按 all 兜底一次，避免节点刚好是草稿/归档时误报
    query.status = 'all'
    await loadData()
    node = findNode(treeData.value, item.id)
  }
  if (!node) {
    ElMessage.warning('树中未找到该节点：可能已被删除、无读取权限，或被筛选条件隐藏')
    return
  }
  selectedId.value = item.id
  await loadDetail(item.id)
  await nextTick()
  treeRef.value?.setCurrentKey(item.id, true)
  const treeNode = treeRef.value?.getNode(item.id)
  treeNode?.$el?.scrollIntoView({ block: 'center' })
}

// ---------------- AI 生成知识点 ----------------
const aiGenDlg = ref(false)
const aiGenLoading = ref(false)
const aiGenCreating = ref(false)
const aiGenResult = ref(null)
const aiGenSelected = ref([])
const aiGenTableRef = ref(null)
const aiGenForm = reactive({
  grade_id: null, subject_id: null, unit_name: '', topic: '',
  textbook_version: '', term: 1, count: 5
})
const aiGenSubjects = computed(() =>
  subjects.value.filter(s => s.grade_id === aiGenForm.grade_id))
// 生成结果创建到当前选中的同年级同学科节点下；否则落到根节点
const aiGenTargetNode = computed(() => {
  const node = detail.value
  if (!node) return null
  if (node.grade_id !== aiGenForm.grade_id || node.subject_id !== aiGenForm.subject_id) return null
  return node
})
const aiTargetLabel = computed(() => aiGenTargetNode.value
  ? `「${aiGenTargetNode.value.name}」节点下`
  : '根节点（顶级）')

function openAiGenerate() {
  if (!canWrite.value) return
  aiGenForm.grade_id = query.grade_id || null
  aiGenForm.subject_id = query.subject_id || null
  aiGenForm.unit_name = ''
  aiGenForm.topic = ''
  aiGenForm.textbook_version = ''
  aiGenForm.term = query.term || 1
  aiGenForm.count = 5
  aiGenResult.value = null
  aiGenSelected.value = []
  aiGenDlg.value = true
}

function onAiGenGradeChange() {
  aiGenForm.subject_id = null
}

function selectAllRows(table, rows) {
  if (!table || !rows?.length) return
  table.clearSelection?.()
  rows.forEach(r => table.toggleRowSelection(r, true))
}

function syncAiGenSelection() {
  const rows = aiGenResult.value?.points || []
  selectAllRows(aiGenTableRef.value, rows)
  aiGenSelected.value = rows.slice()
}

function onAiGenSelectionChange(rows) {
  aiGenSelected.value = rows || []
}

async function runAiGenerate() {
  if (!aiGenForm.grade_id || !aiGenForm.subject_id) {
    return ElMessage.warning('请选择年级与学科')
  }
  aiGenLoading.value = true
  try {
    const payload = {
      grade_id: aiGenForm.grade_id,
      subject_id: aiGenForm.subject_id,
      count: aiGenForm.count
    }
    if (aiGenForm.topic.trim()) payload.topic = aiGenForm.topic.trim()
    if (aiGenForm.unit_name.trim()) payload.unit_name = aiGenForm.unit_name.trim()
    if (aiGenForm.textbook_version.trim()) {
      payload.textbook_version = aiGenForm.textbook_version.trim()
    }
    if (aiGenForm.term) payload.term = aiGenForm.term
    const res = await knowledgeApi.aiGenerate(payload)
    const d = res.data || {}
    aiGenResult.value = {
      unit_name: d.unit_name || '',
      unit_description: d.unit_description || '',
      points: Array.isArray(d.points) ? d.points : [],
      is_fallback: d.is_fallback === true
    }
    aiGenSelected.value = []
    await nextTick()
    syncAiGenSelection()
  } finally {
    aiGenLoading.value = false
  }
}

async function createAiPoints() {
  const rows = aiGenSelected.value
  if (!rows.length) return ElMessage.warning('请勾选要创建的知识点')
  aiGenCreating.value = true
  const parentId = aiGenTargetNode.value?.id ?? null
  let success = 0
  const failed = []
  try {
    for (const p of rows) {
      try {
        await knowledgeApi.create({
          name: p.name,
          grade_id: aiGenForm.grade_id,
          subject_id: aiGenForm.subject_id,
          parent_id: parentId,
          description: p.description || '',
          keywords: p.keywords || '',
          difficulty: p.difficulty || 'medium',
          term: aiGenForm.term || 1,
          textbook_version: aiGenForm.textbook_version || '',
          status: 'published',
          source: 'ai'
        })
        success++
      } catch {
        failed.push(p.name || '未命名')
      }
    }
  } finally {
    aiGenCreating.value = false
  }
  if (success) {
    ElMessage.success(`已创建 ${success} 个知识点${failed.length ? `，失败 ${failed.length} 个` : ''}`)
    aiGenDlg.value = false
    await loadData()
    await loadRagStatus()
  } else if (failed.length) {
    ElMessage.error(`创建失败：${failed.slice(0, 3).join('、')}`)
  }
}

// ---------------- AI 补全（enrich） ----------------
const aiEnrichDlg = ref(false)
const aiEnrichLoading = ref(false)
const aiEnrichApplying = ref(false)
const aiEnrichItems = ref([])
const aiEnrichSelected = ref([])
const aiEnrichFallback = ref(false)
const aiEnrichTableRef = ref(null)

function syncAiEnrichSelection() {
  const rows = aiEnrichItems.value
  selectAllRows(aiEnrichTableRef.value, rows)
  aiEnrichSelected.value = rows.slice()
}

function onAiEnrichSelectionChange(rows) {
  aiEnrichSelected.value = rows || []
}

async function openAiEnrich(nodes) {
  if (!canWrite.value) return
  const list = (nodes || []).filter(Boolean)
  if (!list.length) return ElMessage.warning('请先选择要补全的知识点')
  const ids = list.map(n => n.id)
  if (ids.length > 50) return ElMessage.warning('AI 补全单次最多 50 个节点，请减少选择')
  aiEnrichDlg.value = true
  aiEnrichLoading.value = true
  aiEnrichItems.value = []
  aiEnrichSelected.value = []
  aiEnrichFallback.value = false
  try {
    const res = await knowledgeApi.aiEnrich(ids)
    const d = res.data || {}
    aiEnrichFallback.value = d.is_fallback === true
    aiEnrichItems.value = Array.isArray(d.items) ? d.items : []
    await nextTick()
    syncAiEnrichSelection()
  } catch {
    // 预览请求失败（接口未就绪/越权）时关闭弹窗，错误由拦截器提示
    aiEnrichDlg.value = false
  } finally {
    aiEnrichLoading.value = false
  }
}

async function applyAiEnrich() {
  const rows = aiEnrichSelected.value
  if (!rows.length) return ElMessage.warning('请勾选要应用的补全建议')
  aiEnrichApplying.value = true
  let success = 0
  const failed = []
  try {
    for (const item of rows) {
      try {
        // 契约：补全只应用 description/keywords/difficulty，不改其他字段
        await knowledgeApi.update(item.id, {
          description: item.description || '',
          keywords: item.keywords || '',
          difficulty: item.difficulty || 'medium'
        })
        success++
      } catch {
        failed.push(item.name || `#${item.id}`)
      }
    }
  } finally {
    aiEnrichApplying.value = false
  }
  if (success) {
    ElMessage.success(`已应用 ${success} 条补全建议${failed.length ? `，失败 ${failed.length} 条` : ''}`)
    aiEnrichDlg.value = false
    await loadData()
  } else if (failed.length) {
    ElMessage.error(`应用失败：${failed.slice(0, 3).join('、')}`)
  }
}

// ---------------- 列表详情跳转 ----------------
async function viewNode(row) {
  viewMode.value = 'tree'
  selectedId.value = row.id
  // loadData 会在树视图下按 selectedId 重新拉详情并恢复高亮
  await loadData()
  await nextTick()
  treeRef.value?.setCurrentKey(row.id)
}

onMounted(async () => {
  await loadOptions()
  await Promise.all([loadData(), loadRagStatus()])
})
</script>

<style scoped>
.kp-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.kp-title-wrap { display: flex; flex-direction: column; gap: 10px; }
.kp-stats { display: flex; gap: 12px; flex-wrap: wrap; }
.kp-stat { min-width: 110px; padding: 10px 14px; }
.kp-stat .stat-label { font-size: 12px; margin-top: 2px; }
.kp-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.kp-actions :deep(.el-button + .el-button) { margin-left: 0; }

.view-switch { margin-left: 12px; }
.tree-card { min-height: 520px; }
.tree-search { margin-bottom: 8px; }
.tree-node { display: flex; align-items: center; gap: 6px; width: 100%; min-width: 0; padding-right: 6px; }
.tree-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 220px; }
.tree-level { flex: none; }
.tree-ops { margin-left: auto; flex: none; display: none; }
.tree-node:hover .tree-ops { display: inline-flex; }
.tree-ops :deep(.el-button + .el-button) { margin-left: 4px; }

.detail-card { min-height: 520px; }
.detail-head-actions { display: flex; align-items: center; gap: 4px; }
.kp-breadcrumb { margin-bottom: 4px; }

.card-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.form-actions { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.form-actions :deep(.el-button + .el-button) { margin-left: 0; }

.batch-bar {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 8px 0 12px;
}
.batch-bar :deep(.el-button + .el-button) { margin-left: 0; }

.import-actions { display: flex; align-items: center; gap: 10px; margin-top: 12px; flex-wrap: wrap; }

.muted { color: var(--el-text-color-secondary); font-size: 12px; }
.mt8 { margin-top: 8px; }
.mt12 { margin-top: 12px; }
.mb8 { margin-bottom: 8px; }
.mb12 { margin-bottom: 12px; }

/* RAG 状态标签 + popover 明细 */
.rag-tag { cursor: pointer; }
.rag-pop { display: flex; flex-direction: column; gap: 4px; }
.rag-row { display: flex; justify-content: space-between; font-size: 12px; }
.rag-row b { font-weight: 600; }

/* 语义搜索行 */
.semantic-row {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding-top: 4px;
}
.semantic-label { font-size: 13px; color: var(--el-text-color-regular); }

/* AI 生成 / 补全弹窗 */
.ai-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 4px; }
.ai-result-head {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; margin: 12px 0 8px;
}
</style>
