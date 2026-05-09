<template>
  <div class="proofread-console">
    <!-- Top Section: Upload -->
    <el-card class="upload-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>试卷解析台</span>
        </div>
      </template>
      <el-upload
        class="upload-demo"
        drag
        action="/api/upload_and_read"
        :auto-upload="false"
        :on-change="handleFileChange"
        :show-file-list="false"
        accept=".pdf,.docx"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .docx 或 .pdf 文件
          </div>
        </template>
      </el-upload>

      <div v-if="selectedFile" class="file-actions">
        <span class="file-name">{{ selectedFile.name }}</span>
        <el-button type="primary" :loading="loading" @click="processFile">
          开始解析试卷
        </el-button>
      </div>

      <el-divider content-position="center">或</el-divider>

      <div class="import-json-area">
        <el-button type="success" icon="Upload" @click="triggerJsonImport">
          导入已有 JSON 题库文件
        </el-button>
        <span class="import-hint">直接加载之前导出的 .json 文件，无需调用 AI</span>
        <input ref="jsonFileInput" type="file" accept=".json" style="display:none" @change="handleJsonImport" />
      </div>
    </el-card>

    <!-- Main Workspace -->
    <el-row :gutter="20" class="workspace" v-if="rawText || questions.length > 0">
      <!-- Left Column: Raw Text Preview -->
      <el-col :span="10">
        <el-card shadow="never" class="raw-text-card">
          <template #header>
            <div class="card-header">
              <span>提取原始文本 (校对参考)</span>
            </div>
          </template>
          <el-scrollbar height="calc(100vh - 250px)">
            <div class="raw-text-content">
              <pre>{{ rawText || '暂无文本...' }}</pre>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>

      <!-- Right Column: JSON Questions Editor -->
      <el-col :span="14">
        <el-card shadow="never" class="json-editor-card">
          <template #header>
            <div class="card-header">
              <span>识别结果校对</span>
              <el-button type="primary" plain size="small" @click="addQuestion">添加题目</el-button>
            </div>
          </template>
          
          <el-scrollbar height="calc(100vh - 310px)">
            <div v-if="questions.length === 0 && !loading" class="empty-state">
              <el-empty description="暂无题目数据，请先上传解析" />
            </div>
            
            <div class="question-list">
              <el-card 
                v-for="(q, index) in paginatedQuestions" 
                :key="q.id || ((currentPage - 1) * pageSize + index)" 
                class="question-item-card" 
                shadow="hover"
              >
                <div class="question-header">
                  <span class="question-index">题目 {{ (currentPage - 1) * pageSize + index + 1 }}</span>
                  <el-button type="danger" link icon="Delete" @click="removeQuestion((currentPage - 1) * pageSize + index)">删除</el-button>
                </div>
                
                <el-form label-width="60px" size="small" label-position="left">
                  <el-form-item label="类型">
                    <el-select v-model="q.type" placeholder="选择题型">
                      <el-option label="单选题" value="single" />
                      <el-option label="多选题" value="multiple" />
                      <el-option label="判断题" value="judge" />
                      <el-option label="填空题" value="fill" />
                      <el-option label="简答题" value="essay" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="题干">
                    <el-input v-model="q.content" type="textarea" :autosize="{ minRows: 2 }" />
                  </el-form-item>
                  
                  <template v-if="['single', 'multiple', 'judge'].includes(q.type)">
                    <el-form-item label="选项">
                      <div class="options-container">
                        <div v-for="(opt, optIndex) in q.options" :key="optIndex" class="option-row">
                          <el-input v-model="q.options[optIndex]">
                            <template #prepend>{{ String.fromCharCode(65 + optIndex) }}</template>
                          </el-input>
                          <el-button type="danger" icon="Minus" circle @click="removeOption(q, optIndex)" />
                        </div>
                        <el-button type="primary" link icon="Plus" @click="addOption(q)">新增选项</el-button>
                      </div>
                    </el-form-item>
                  </template>

                  <el-form-item label="答案">
                    <el-input v-model="q.answer" />
                  </el-form-item>
                  
                  <el-form-item label="解析">
                    <el-input v-model="q.analysis" type="textarea" :autosize="{ minRows: 1 }" />
                  </el-form-item>
                </el-form>
              </el-card>
            </div>
            
            <div class="pagination-container" v-if="questions.length > 0">
              <el-pagination
                background
                layout="prev, pager, next, total"
                :total="questions.length"
                :page-size="pageSize"
                v-model:current-page="currentPage"
                @current-change="handleCurrentChange"
              />
            </div>
          </el-scrollbar>
          
          <div class="bottom-actions" v-if="questions.length > 0">
            <el-button type="primary" size="large" @click="finalizeJSON" style="width: 100%; margin-bottom: 10px;">
              生成最终 JSON 并进入做题
            </el-button>
            <div style="display: flex; gap: 10px;">
              <el-button type="success" icon="Download" @click="downloadJson" style="flex: 1;">
                导出为 JSON 文件
              </el-button>
              <el-button type="danger" icon="Delete" plain @click="clearDraft" style="flex: 1;">
                清空当前草稿
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const selectedFile = ref(null)
const loading = ref(false)
const rawText = ref('')
const questions = ref([])

// 分页状态
const currentPage = ref(1)
const pageSize = ref(10)

const paginatedQuestions = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return questions.value.slice(start, end)
})

const handleCurrentChange = (val) => {
  currentPage.value = val
  const scrollContainer = document.querySelector('.el-scrollbar__wrap')
  if (scrollContainer) {
    scrollContainer.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

// 自定义防抖函数（替代 lodash-es）
function customDebounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

onMounted(() => {
  const draft = localStorage.getItem('draft_questions')
  if (draft) {
    try {
      questions.value = JSON.parse(draft)
      ElMessage.success('已自动恢复上次的未完成草稿')
    } catch (e) {
      console.error('解析草稿失败', e)
    }
  }
})

const saveDraft = customDebounce((newVal) => {
  localStorage.setItem('draft_questions', JSON.stringify(newVal))
}, 1000)

watch(questions, (newVal) => {
  saveDraft(newVal)
}, { deep: true })

const handleFileChange = (uploadFile) => {
  selectedFile.value = uploadFile.raw
}

const jsonFileInput = ref(null)

const triggerJsonImport = () => {
  jsonFileInput.value.click()
}

const handleJsonImport = (event) => {
  const file = event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result)
      const imported = data.questions || data
      if (!Array.isArray(imported)) {
        throw new Error('JSON 中未找到 questions 数组')
      }
      questions.value = imported
      currentPage.value = 1
      ElMessage.success(`成功导入 ${imported.length} 道题目！`)
    } catch (err) {
      console.error(err)
      ElMessage.error('JSON 文件解析失败：' + err.message)
    }
  }
  reader.readAsText(file)
  event.target.value = '' // 允许重复选同一文件
}

const processFile = async () => {
  if (!selectedFile.value) return
  
  loading.value = true
  rawText.value = ''
  questions.value = []
  
  try {
    // 1. Upload and read text
    ElMessage.info('正在提取文档文本...')
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    // In actual app, change to full URL if needed (e.g., http://localhost:8000/api/upload_and_read)
    // We assume proxy is set up or we're on the same origin.
    const readRes = await axios.post('/api/upload_and_read', formData)
    rawText.value = readRes.data.text
    
    // 2. Extract JSON via LLM
    ElMessage.info('长卷子智能分块提取中，这可能需要 1~2 分钟，请不要刷新页面...')
    
    // 从 localStorage 读取 LLM 配置
    const savedSettingsStr = localStorage.getItem('llm_settings')
    let llmConfig = {}
    if (savedSettingsStr) {
      const parsed = JSON.parse(savedSettingsStr)
      llmConfig = {
        api_key: parsed.apiKey || '',
        base_url: parsed.baseUrl || '',
        model: parsed.model || ''
      }
    } else {
      ElMessage.warning('检测到您未配置大模型参数，尝试使用后端默认环境变量进行抽取。建议先前往"大模型设置"页配置。')
    }

    const extractRes = await axios.post('/api/extract_to_json', {
      text: rawText.value,
      ...llmConfig
    })

    questions.value = extractRes.data.questions || []
    ElMessage.success('试卷解析完成！')
    
  } catch (error) {
    console.error(error)
    ElMessage.error(error.message || error.response?.data?.detail || '处理过程中出现错误')
  } finally {
    loading.value = false
  }
}

// Editor operations
const addQuestion = () => {
  questions.value.push({
    id: Date.now(),
    type: 'single',
    content: '',
    options: ['', '', '', ''],
    answer: '',
    analysis: ''
  })
}

const removeQuestion = (index) => {
  questions.value.splice(index, 1)
}

const addOption = (question) => {
  if (!question.options) question.options = []
  question.options.push('')
}

const removeOption = (question, optIndex) => {
  question.options.splice(optIndex, 1)
}

const emit = defineEmits(['start-exercise'])

const finalizeJSON = () => {
  if (questions.value.length === 0) {
    ElMessage.warning('当前没有题目数据，请先解析试卷')
    return
  }
  emit('start-exercise', {
    questions: questions.value,
    title: '提取试卷'
  })
}

const downloadJson = () => {
  const data = {
    paper_title: "提取试卷",
    questions: questions.value
  }
  const jsonStr = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  
  const a = document.createElement('a')
  a.href = url
  a.download = `提取题库_${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('JSON 文件已成功导出')
}

const clearDraft = () => {
  ElMessageBox.confirm(
    '此操作将永久清空当前校对台的所有题目数据以及本地草稿，确认继续？',
    '警告',
    {
      confirmButtonText: '确定清空',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    questions.value = []
    localStorage.removeItem('draft_questions')
    ElMessage.success('草稿已成功清空')
  }).catch(() => {
    // cancelled
  })
}
</script>

<style scoped>
.proofread-console {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  font-weight: bold;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-card {
  margin-bottom: 20px;
}

.file-actions {
  margin-top: 15px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.import-json-area {
  display: flex;
  align-items: center;
  gap: 12px;
}
.import-hint {
  font-size: 13px;
  color: #909399;
}

.file-name {
  color: var(--text-regular);
  font-size: 14px;
}

.workspace {
  margin-top: 20px;
}

.raw-text-card {
  height: calc(100vh - 160px);
}

.json-editor-card {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
}

.raw-text-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-regular);
  margin: 0;
  padding: 10px;
  background-color: #fafafa;
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding-right: 15px; /* for scrollbar */
}

.question-item-card {
  border: 1px solid var(--border-color);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px dashed var(--border-color);
}

.question-index {
  font-weight: bold;
  color: var(--primary-color);
}

.options-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.option-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.bottom-actions {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
  margin-top: 10px;
}

.streaming-terminal {
  background-color: #1e1e1e;
  color: #d4d4d4;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 20px;
  font-family: 'Courier New', Courier, monospace;
}
.terminal-header {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #4CAF50;
  margin-bottom: 10px;
  border-bottom: 1px solid #333;
  padding-bottom: 8px;
}
.pulse {
  display: inline-block;
  width: 8px;
  height: 8px;
  background-color: #4CAF50;
  border-radius: 50%;
  margin-right: 8px;
  animation: pulse 1s infinite;
}
@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.3; }
  100% { opacity: 1; }
}
.terminal-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.5;
}
</style>
