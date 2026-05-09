<template>
  <div class="exam-mode">
    <!-- 无题目 -->
    <div v-if="!questions || questions.length === 0" class="no-data">
      <el-empty description="暂无题库，请先在「解析与校对台」提取题目，然后点击「进入做题」">
        <el-button type="primary" @click="$emit('go-back')">返回校对台</el-button>
      </el-empty>
    </div>

    <!-- ===== 组卷配置弹窗 ===== -->
    <div v-else-if="!examStarted" class="config-wrapper">
      <el-card class="config-card" shadow="hover">
        <template #header>
          <div class="config-title">
            <el-icon :size="22" color="#409eff"><Edit /></el-icon>
            <span>生成考试试卷</span>
          </div>
        </template>

        <div class="config-body">
          <p class="config-hint">当前题库共包含 <strong>{{ questions.length }}</strong> 道题目。请设置本次考试的出题数量：</p>

          <div class="config-row">
            <span class="config-label">出题数量</span>
            <el-input-number
              v-model="examConfig.questionCount"
              :min="1"
              :max="questions.length"
              :step="5"
              size="large"
            />
          </div>

          <div class="config-row">
            <span class="config-label">题目顺序</span>
            <el-radio-group v-model="examConfig.shuffle">
              <el-radio :value="true">随机打乱</el-radio>
              <el-radio :value="false">保持原序</el-radio>
            </el-radio-group>
          </div>

          <el-button type="primary" size="large" @click="startExam" style="width: 100%; margin-top: 24px;">
            开始考试
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- ===== 正式考试界面 ===== -->
    <div v-else class="exercise-layout">

      <!-- 左侧答题卡 -->
      <aside class="answer-card-panel">
        <div class="panel-title">考试答题卡</div>
        <div class="panel-stats">
          <span>共 <strong>{{ examQuestions.length }}</strong> 题</span>
          <span v-if="!submitted">已答 <strong>{{ answeredCount }}</strong></span>
          <span v-if="submitted" style="color:#67c23a">✓{{ correctCount }}</span>
          <span v-if="submitted" style="color:#f56c6c">✗{{ examQuestions.length - correctCount }}</span>
        </div>
        <div class="number-grid">
          <button
            v-for="(q, i) in examQuestions" :key="i"
            class="num-btn"
            :class="getNumClass(q, i)"
            @click="scrollToQuestion(i)"
          >{{ i + 1 }}</button>
        </div>
        <div class="panel-actions">
          <el-button v-if="!submitted" type="primary" @click="submitExam" style="width:100%">交卷</el-button>
          <el-button v-if="submitted" type="success" disabled style="width:100%">
            得分：{{ correctCount }}/{{ examQuestions.length }}
          </el-button>
          <el-button size="small" @click="backToConfig" style="width:100%">重新组卷</el-button>
          <el-button size="small" type="info" plain @click="$emit('go-back')" style="width:100%">返回校对台</el-button>
        </div>
      </aside>

      <!-- 右侧题目 -->
      <main class="exercise-main">
        <div class="exercise-header">
          <div class="header-left">
            <span class="paper-title">模拟考试</span>
            <el-tag type="info">{{ examQuestions.length }} 题</el-tag>
            <el-tag v-if="!submitted" type="warning">考试中</el-tag>
            <el-tag v-else :type="scoreTag">得分：{{ Math.round(correctCount / examQuestions.length * 100) }} 分</el-tag>
          </div>
        </div>

        <div
          v-for="(q, index) in examQuestions" :key="q.id || index"
          :ref="el => { if (el) questionRefs[index] = el }"
          class="question-block"
          :class="{ 'correct': submitted && isCorrect(q), 'wrong': submitted && !isCorrect(q) }"
        >
          <div class="q-header">
            <span class="q-index">{{ index + 1 }}.</span>
            <el-tag size="small" :type="typeTag(q.type)" class="q-type-tag">{{ typeLabel(q.type) }}</el-tag>
            <span class="q-content">{{ q.content }}</span>
          </div>

          <!-- 单选 -->
          <el-radio-group v-if="q.type === 'single'" v-model="q.userAnswer" class="option-group" :disabled="submitted">
            <el-radio v-for="(opt, oi) in q.options" :key="oi" :value="String.fromCharCode(65 + oi)" class="option-item" :class="submitted ? getOptionClass(q, String.fromCharCode(65 + oi)) : ''">{{ opt }}</el-radio>
          </el-radio-group>
          <!-- 多选 -->
          <el-checkbox-group v-else-if="q.type === 'multiple'" v-model="q.userAnswer" class="option-group" :disabled="submitted">
            <el-checkbox v-for="(opt, oi) in q.options" :key="oi" :value="String.fromCharCode(65 + oi)" class="option-item" :class="submitted ? getOptionClass(q, String.fromCharCode(65 + oi)) : ''">{{ opt }}</el-checkbox>
          </el-checkbox-group>
          <!-- 判断 -->
          <el-radio-group v-else-if="q.type === 'judge'" v-model="q.userAnswer" class="option-group judge-group" :disabled="submitted">
            <el-radio-button v-for="(opt, oi) in (q.options && q.options.length ? q.options : ['正确', '错误'])" :key="oi" :value="opt">{{ opt }}</el-radio-button>
          </el-radio-group>
          <!-- 填空/简答 -->
          <el-input v-else v-model="q.userAnswer" type="textarea" :autosize="{ minRows: 2, maxRows: 6 }" placeholder="请在此处填写答案..." class="fill-input" :disabled="submitted" />

          <!-- 阅卷结果（交卷后才显示） -->
          <div v-if="submitted" class="answer-reveal" :class="isCorrect(q) ? 'reveal-correct' : 'reveal-wrong'">
            <div class="reveal-header">
              <el-icon :color="isCorrect(q) ? '#67c23a' : '#f56c6c'" :size="18"><component :is="isCorrect(q) ? 'Select' : 'Close'" /></el-icon>
              <strong :style="{ color: isCorrect(q) ? '#67c23a' : '#f56c6c' }">{{ isCorrect(q) ? '回答正确 ✓' : '回答错误 ✗' }}</strong>
            </div>
            <div class="reveal-body">
              <div class="correct-answer"><span>正确答案：</span><strong class="answer-highlight">{{ q.answer || '（无标准答案）' }}</strong></div>
              <div v-if="q.analysis" class="analysis-text"><span>解析：</span>{{ q.analysis }}</div>
            </div>
          </div>
        </div>

        <!-- 底部交卷 -->
        <div class="exercise-footer" v-if="!submitted">
          <el-button type="primary" size="large" @click="submitExam">提交试卷</el-button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, nextTick } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Edit, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  questions: { type: Array, default: () => [] },
})
defineEmits(['go-back'])

const examStarted = ref(false)
const submitted = ref(false)
const examQuestions = ref([])
const questionRefs = ref({})

const examConfig = reactive({
  questionCount: 10,
  shuffle: true
})

// Fisher-Yates 洗牌算法
const shuffleArray = (arr) => {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

const startExam = () => {
  let pool = props.questions.map(q => JSON.parse(JSON.stringify(q))) // 深拷贝
  if (examConfig.shuffle) pool = shuffleArray(pool)
  const selected = pool.slice(0, examConfig.questionCount)
  selected.forEach((q, i) => {
    q.id = i + 1
    q.userAnswer = q.type === 'multiple' ? [] : ''
  })
  examQuestions.value = selected
  submitted.value = false
  examStarted.value = true
}

const backToConfig = () => {
  examStarted.value = false
  submitted.value = false
  examQuestions.value = []
}

const scrollToQuestion = (i) => {
  nextTick(() => {
    const el = questionRefs.value[i]
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

// 判对错
const isCorrect = (q) => {
  const answer = (q.answer || '').trim()
  if (!answer) return true
  if (q.type === 'multiple') {
    return [...(q.userAnswer || [])].sort().join('') === answer.replace(/\s/g, '').split('').sort().join('')
  }
  return String(q.userAnswer || '').trim().toUpperCase() === answer.toUpperCase()
}

const getOptionClass = (q, letter) => {
  const answer = (q.answer || '').toUpperCase()
  if (answer.includes(letter)) return 'option-correct'
  const sel = q.type === 'multiple' ? (q.userAnswer || []).includes(letter) : q.userAnswer === letter
  if (sel) return 'option-wrong'
  return ''
}

const getNumClass = (q, i) => {
  if (submitted.value) {
    return isCorrect(q) ? 'num-correct' : 'num-wrong'
  }
  // 未交卷：已答 vs 未答
  const answered = q.type === 'multiple' ? (q.userAnswer && q.userAnswer.length > 0) : (q.userAnswer && String(q.userAnswer).trim() !== '')
  return answered ? 'num-answered' : ''
}

const answeredCount = computed(() => {
  return examQuestions.value.filter(q => {
    if (q.type === 'multiple') return q.userAnswer && q.userAnswer.length > 0
    return q.userAnswer && String(q.userAnswer).trim() !== ''
  }).length
})

const correctCount = computed(() => examQuestions.value.filter(q => isCorrect(q)).length)
const scoreTag = computed(() => {
  const pct = correctCount.value / examQuestions.value.length
  if (pct >= 0.9) return 'success'
  if (pct >= 0.6) return 'warning'
  return 'danger'
})

const submitExam = async () => {
  const unanswered = examQuestions.value.length - answeredCount.value
  const msg = unanswered > 0
    ? `您还有 ${unanswered} 道题尚未作答，确认提交？`
    : '确认提交试卷？提交后将自动阅卷显示答案。'
  await ElMessageBox.confirm(msg, '确认交卷', {
    confirmButtonText: '确认提交', cancelButtonText: '再检查一下', type: 'warning'
  })
  submitted.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const typeLabel = (type) => ({ single: '单选', multiple: '多选', judge: '判断', fill: '填空', essay: '简答' })[type] || '未知'
const typeTag = (type) => ({ single: 'primary', multiple: 'warning', judge: 'success', fill: 'info', essay: '' })[type] || 'info'
</script>

<style scoped>
.exam-mode { padding: 16px; }
.no-data { padding: 80px 0; text-align: center; }

/* ---- 配置弹窗 ---- */
.config-wrapper { display: flex; justify-content: center; padding: 60px 20px; }
.config-card { width: 500px; border-radius: 12px; }
.config-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 700; }
.config-body { padding: 8px 0; }
.config-hint { font-size: 15px; color: #606266; line-height: 1.8; margin-bottom: 24px; }
.config-row { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }
.config-label { font-weight: 600; color: var(--text-primary); min-width: 72px; }

/* ---- 双栏布局 ---- */
.exercise-layout { display: flex; gap: 20px; max-width: 1200px; margin: 0 auto; }
.answer-card-panel {
  width: 210px; flex-shrink: 0; position: sticky; top: 80px; align-self: flex-start;
  background: #fff; border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,.04);
}
.panel-title { font-weight: 700; font-size: 15px; text-align: center; margin-bottom: 10px; }
.panel-stats { display: flex; justify-content: center; gap: 10px; font-size: 13px; color: #606266; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border-color); }
.number-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin-bottom: 16px; max-height: 300px; overflow-y: auto; }
.num-btn { width: 100%; aspect-ratio: 1; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; font-size: 13px; cursor: pointer; transition: all .2s; color: #303133; font-weight: 500; }
.num-btn:hover { border-color: #409eff; color: #409eff; }
.num-btn.num-answered { background: #ecf5ff; border-color: #409eff; color: #409eff; }
.num-btn.num-correct { background: #67c23a; color: #fff; border-color: #67c23a; }
.num-btn.num-wrong { background: #f56c6c; color: #fff; border-color: #f56c6c; }
.panel-actions { display: flex; flex-direction: column; gap: 8px; }

.exercise-main { flex: 1; min-width: 0; }
.exercise-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 2px solid var(--border-color); }
.header-left { display: flex; align-items: center; gap: 12px; }
.paper-title { font-size: 20px; font-weight: 700; color: var(--text-primary); }

/* ---- 题目卡片 ---- */
.question-block { background: #fff; border: 1px solid var(--border-color); border-radius: 8px; padding: 20px 24px; margin-bottom: 16px; transition: all .3s; }
.question-block.correct { border-left: 4px solid #67c23a; background: #f0f9eb; }
.question-block.wrong { border-left: 4px solid #f56c6c; background: #fef0f0; }
.q-header { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 14px; line-height: 1.6; }
.q-index { font-weight: 700; flex-shrink: 0; }
.q-type-tag { flex-shrink: 0; margin-top: 2px; }
.q-content { font-size: 15px; }
.option-group { display: flex; flex-direction: column; gap: 10px; padding-left: 24px; }
.judge-group { flex-direction: row; }
.option-item { line-height: 1.5; }
.option-item.option-correct :deep(.el-radio__label), .option-item.option-correct :deep(.el-checkbox__label) { color: #67c23a; font-weight: 700; }
.option-item.option-wrong :deep(.el-radio__label), .option-item.option-wrong :deep(.el-checkbox__label) { color: #f56c6c; font-weight: 700; }
.fill-input { margin-top: 8px; }

.answer-reveal { margin-top: 16px; padding: 14px 16px; border-radius: 6px; font-size: 14px; }
.reveal-correct { background: #f0f9eb; border: 1px solid #c2e7b0; }
.reveal-wrong { background: #fef0f0; border: 1px solid #fbc4c4; }
.reveal-header { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.reveal-body { padding-left: 24px; color: #606266; line-height: 1.8; }
.correct-answer { margin-bottom: 4px; }
.answer-highlight { color: #e6a23c; font-size: 15px; }
.analysis-text { color: #909399; }

.exercise-footer { display: flex; justify-content: center; padding: 32px 0 16px; }
</style>
