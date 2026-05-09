<template>
  <div class="exercise-view">
    <!-- 未开始 / 无题目 -->
    <div v-if="!localQuestions || localQuestions.length === 0" class="no-data">
      <el-empty description="暂无题目，请先在「解析与校对台」提取并进入做题">
        <el-button type="primary" @click="$emit('go-back')">返回校对台</el-button>
      </el-empty>
    </div>

    <!-- 答题中 -->
    <div v-else class="exercise-layout">

      <!-- ========== 左侧：答题卡导航面板 ========== -->
      <aside class="answer-card-panel">
        <div class="panel-title">答题卡</div>
        <div class="panel-stats">
          <span>已答 <strong>{{ completedCount }}</strong>/{{ localQuestions.length }}</span>
          <span v-if="completedCount > 0" style="color:#67c23a">✓{{ correctCount }}</span>
          <span v-if="completedCount > 0" style="color:#f56c6c">✗{{ completedCount - correctCount }}</span>
        </div>
        <div class="number-grid">
          <button
            v-for="(q, i) in localQuestions" :key="i"
            class="num-btn"
            :class="{ 'num-correct': q.isSubmitted && q.isCorrect, 'num-wrong': q.isSubmitted && !q.isCorrect, 'num-active': viewMode === 'single' && currentIndex === i }"
            @click="jumpTo(i)"
          >{{ i + 1 }}</button>
        </div>
        <div class="mode-switch">
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button value="scroll">整卷浏览</el-radio-button>
            <el-radio-button value="single">单题阅读</el-radio-button>
          </el-radio-group>
        </div>
        <div class="panel-actions">
          <el-button size="small" @click="resetExam" style="width:100%">全部重做</el-button>
          <el-button size="small" type="info" plain @click="$emit('go-back')" style="width:100%">返回校对台</el-button>
        </div>
      </aside>

      <!-- ========== 右侧：题目主体区域 ========== -->
      <main class="exercise-main">
        <div class="exercise-header">
          <div class="header-left">
            <span class="paper-title">{{ paperTitle }}</span>
            <el-tag type="info">共 {{ localQuestions.length }} 题</el-tag>
          </div>
          <div class="header-right">
            <el-tag type="success" v-if="completedCount > 0">
              正确：{{ correctCount }}/{{ completedCount }}（{{ Math.round(correctCount / completedCount * 100) }}%）
            </el-tag>
          </div>
        </div>

        <!-- ===== 整卷浏览模式 ===== -->
        <template v-if="viewMode === 'scroll'">
          <div
            v-for="(q, index) in localQuestions" :key="q.id || index"
            :ref="el => { if (el) questionRefs[index] = el }"
            class="question-block"
            :class="{ 'correct': q.isSubmitted && q.isCorrect, 'wrong': q.isSubmitted && !q.isCorrect }"
          >
            <!-- 题目渲染 -->
            <div class="q-header">
              <span class="q-index">{{ index + 1 }}.</span>
              <el-tag size="small" :type="typeTag(q.type)" class="q-type-tag">{{ typeLabel(q.type) }}</el-tag>
              <span class="q-content">{{ q.content }}</span>
            </div>
            <el-radio-group v-if="q.type === 'single'" v-model="q.userAnswer" class="option-group" :disabled="q.isSubmitted">
              <el-radio v-for="(opt, oi) in q.options" :key="oi" :value="String.fromCharCode(65 + oi)" class="option-item" :class="getOptionClass(q, String.fromCharCode(65 + oi))">{{ opt }}</el-radio>
            </el-radio-group>
            <el-checkbox-group v-else-if="q.type === 'multiple'" v-model="q.userAnswer" class="option-group" :disabled="q.isSubmitted">
              <el-checkbox v-for="(opt, oi) in q.options" :key="oi" :value="String.fromCharCode(65 + oi)" class="option-item" :class="getOptionClass(q, String.fromCharCode(65 + oi))">{{ opt }}</el-checkbox>
            </el-checkbox-group>
            <el-radio-group v-else-if="q.type === 'judge'" v-model="q.userAnswer" class="option-group judge-group" :disabled="q.isSubmitted">
              <el-radio-button v-for="(opt, oi) in (q.options && q.options.length ? q.options : ['正确', '错误'])" :key="oi" :value="opt">{{ opt }}</el-radio-button>
            </el-radio-group>
            <el-input v-else v-model="q.userAnswer" type="textarea" :autosize="{ minRows: 2, maxRows: 6 }" placeholder="请在此处填写答案..." class="fill-input" :disabled="q.isSubmitted" />
            <div class="check-btn-area" v-if="!q.isSubmitted">
              <el-button type="primary" size="small" :disabled="isAnswerEmpty(q)" @click="checkSingleAnswer(q)">核对答案</el-button>
            </div>
            <div v-if="q.isSubmitted" class="answer-reveal" :class="q.isCorrect ? 'reveal-correct' : 'reveal-wrong'">
              <div class="reveal-header">
                <el-icon :color="q.isCorrect ? '#67c23a' : '#f56c6c'" :size="18"><component :is="q.isCorrect ? 'Select' : 'Close'" /></el-icon>
                <strong :style="{ color: q.isCorrect ? '#67c23a' : '#f56c6c' }">{{ q.isCorrect ? '回答正确 ✓' : '回答错误 ✗' }}</strong>
                <el-button type="warning" link size="small" @click="retrySingle(q)" style="margin-left: auto;">重新作答此题</el-button>
              </div>
              <div class="reveal-body">
                <div v-if="!q.isCorrect" class="correct-answer"><span>正确答案：</span><strong class="answer-highlight">{{ q.answer }}</strong></div>
                <div v-if="q.analysis" class="analysis-text"><span>解析：</span>{{ q.analysis }}</div>
              </div>
            </div>
          </div>
        </template>

        <!-- ===== 单题阅读模式 ===== -->
        <template v-else>
          <div
            class="question-block"
            :class="{ 'correct': currentQ.isSubmitted && currentQ.isCorrect, 'wrong': currentQ.isSubmitted && !currentQ.isCorrect }"
          >
            <div class="q-header">
              <span class="q-index">{{ currentIndex + 1 }}.</span>
              <el-tag size="small" :type="typeTag(currentQ.type)" class="q-type-tag">{{ typeLabel(currentQ.type) }}</el-tag>
              <span class="q-content">{{ currentQ.content }}</span>
            </div>
            <el-radio-group v-if="currentQ.type === 'single'" v-model="currentQ.userAnswer" class="option-group" :disabled="currentQ.isSubmitted">
              <el-radio v-for="(opt, oi) in currentQ.options" :key="oi" :value="String.fromCharCode(65 + oi)" class="option-item" :class="getOptionClass(currentQ, String.fromCharCode(65 + oi))">{{ opt }}</el-radio>
            </el-radio-group>
            <el-checkbox-group v-else-if="currentQ.type === 'multiple'" v-model="currentQ.userAnswer" class="option-group" :disabled="currentQ.isSubmitted">
              <el-checkbox v-for="(opt, oi) in currentQ.options" :key="oi" :value="String.fromCharCode(65 + oi)" class="option-item" :class="getOptionClass(currentQ, String.fromCharCode(65 + oi))">{{ opt }}</el-checkbox>
            </el-checkbox-group>
            <el-radio-group v-else-if="currentQ.type === 'judge'" v-model="currentQ.userAnswer" class="option-group judge-group" :disabled="currentQ.isSubmitted">
              <el-radio-button v-for="(opt, oi) in (currentQ.options && currentQ.options.length ? currentQ.options : ['正确', '错误'])" :key="oi" :value="opt">{{ opt }}</el-radio-button>
            </el-radio-group>
            <el-input v-else v-model="currentQ.userAnswer" type="textarea" :autosize="{ minRows: 2, maxRows: 6 }" placeholder="请在此处填写答案..." class="fill-input" :disabled="currentQ.isSubmitted" />
            <div class="check-btn-area" v-if="!currentQ.isSubmitted">
              <el-button type="primary" size="small" :disabled="isAnswerEmpty(currentQ)" @click="checkSingleAnswer(currentQ)">核对答案</el-button>
            </div>
            <div v-if="currentQ.isSubmitted" class="answer-reveal" :class="currentQ.isCorrect ? 'reveal-correct' : 'reveal-wrong'">
              <div class="reveal-header">
                <el-icon :color="currentQ.isCorrect ? '#67c23a' : '#f56c6c'" :size="18"><component :is="currentQ.isCorrect ? 'Select' : 'Close'" /></el-icon>
                <strong :style="{ color: currentQ.isCorrect ? '#67c23a' : '#f56c6c' }">{{ currentQ.isCorrect ? '回答正确 ✓' : '回答错误 ✗' }}</strong>
                <el-button type="warning" link size="small" @click="retrySingle(currentQ)" style="margin-left: auto;">重新作答此题</el-button>
              </div>
              <div class="reveal-body">
                <div v-if="!currentQ.isCorrect" class="correct-answer"><span>正确答案：</span><strong class="answer-highlight">{{ currentQ.answer }}</strong></div>
                <div v-if="currentQ.analysis" class="analysis-text"><span>解析：</span>{{ currentQ.analysis }}</div>
              </div>
            </div>
          </div>
          <div class="single-nav">
            <el-button :disabled="currentIndex === 0" @click="currentIndex--" icon="ArrowLeft">上一题</el-button>
            <span class="nav-indicator">{{ currentIndex + 1 }} / {{ localQuestions.length }}</span>
            <el-button :disabled="currentIndex === localQuestions.length - 1" @click="currentIndex++">下一题<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  questions: { type: Array, default: () => [] },
  paperTitle: { type: String, default: '未命名试卷' }
})
defineEmits(['go-back'])

const localQuestions = ref([])
const viewMode = ref('scroll')
const currentIndex = ref(0)
const questionRefs = ref({})

const currentQ = computed(() => localQuestions.value[currentIndex.value] || {})

const initQuestions = (qs) => {
  localQuestions.value = qs.map(q => ({
    ...q,
    userAnswer: q.type === 'multiple' ? [] : '',
    isSubmitted: false,
    isCorrect: null
  }))
  currentIndex.value = 0
}
watch(() => props.questions, (qs) => { initQuestions(qs) }, { immediate: true })

const jumpTo = (i) => {
  if (viewMode.value === 'single') {
    currentIndex.value = i
  } else {
    nextTick(() => {
      const el = questionRefs.value[i]
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
  }
}

const typeLabel = (type) => ({ single: '单选', multiple: '多选', judge: '判断', fill: '填空', essay: '简答' })[type] || '未知'
const typeTag = (type) => ({ single: 'primary', multiple: 'warning', judge: 'success', fill: 'info', essay: '' })[type] || 'info'
const isAnswerEmpty = (q) => {
  if (q.type === 'multiple') return !q.userAnswer || q.userAnswer.length === 0
  return !q.userAnswer || String(q.userAnswer).trim() === ''
}

const checkSingleAnswer = (q) => {
  q.isSubmitted = true
  const answer = (q.answer || '').trim()
  if (!answer) { q.isCorrect = true; return }
  if (q.type === 'multiple') {
    q.isCorrect = [...(q.userAnswer || [])].sort().join('') === answer.replace(/\s/g, '').split('').sort().join('')
  } else {
    q.isCorrect = String(q.userAnswer || '').trim().toUpperCase() === answer.toUpperCase()
  }
}
const retrySingle = (q) => { q.userAnswer = q.type === 'multiple' ? [] : ''; q.isSubmitted = false; q.isCorrect = null }
const getOptionClass = (q, letter) => {
  if (!q.isSubmitted) return ''
  const answer = (q.answer || '').toUpperCase()
  if (answer.includes(letter)) return 'option-correct'
  const sel = q.type === 'multiple' ? (q.userAnswer || []).includes(letter) : q.userAnswer === letter
  if (sel) return 'option-wrong'
  return ''
}

const completedCount = computed(() => localQuestions.value.filter(q => q.isSubmitted).length)
const correctCount = computed(() => localQuestions.value.filter(q => q.isSubmitted && q.isCorrect).length)
const resetExam = () => { initQuestions(props.questions) }
</script>

<style scoped>
.exercise-view { padding: 16px; }
.no-data { padding: 80px 0; text-align: center; }

.exercise-layout { display: flex; gap: 20px; max-width: 1200px; margin: 0 auto; }

/* ---- 答题卡 ---- */
.answer-card-panel {
  width: 210px; flex-shrink: 0; position: sticky; top: 80px; align-self: flex-start;
  background: #fff; border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,.04);
}
.panel-title { font-weight: 700; font-size: 15px; text-align: center; margin-bottom: 10px; color: var(--text-primary); }
.panel-stats { display: flex; justify-content: center; gap: 10px; font-size: 13px; color: #606266; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border-color); }
.number-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin-bottom: 16px; max-height: 300px; overflow-y: auto; }
.num-btn {
  width: 100%; aspect-ratio: 1; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff;
  font-size: 13px; cursor: pointer; transition: all .2s; color: #303133; font-weight: 500;
}
.num-btn:hover { border-color: #409eff; color: #409eff; }
.num-btn.num-correct { background: #67c23a; color: #fff; border-color: #67c23a; }
.num-btn.num-wrong { background: #f56c6c; color: #fff; border-color: #f56c6c; }
.num-btn.num-active { border-color: #409eff; box-shadow: 0 0 0 2px rgba(64,158,255,.3); }
.mode-switch { display: flex; justify-content: center; margin-bottom: 14px; }
.panel-actions { display: flex; flex-direction: column; gap: 8px; }

/* ---- 主内容 ---- */
.exercise-main { flex: 1; min-width: 0; }
.exercise-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 2px solid var(--border-color); }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-right { display: flex; align-items: center; gap: 10px; }
.paper-title { font-size: 20px; font-weight: 700; color: var(--text-primary); }

/* ---- 题目卡片 ---- */
.question-block { background: #fff; border: 1px solid var(--border-color); border-radius: 8px; padding: 20px 24px; margin-bottom: 16px; transition: all .3s; }
.question-block.correct { border-left: 4px solid #67c23a; background: #f0f9eb; }
.question-block.wrong { border-left: 4px solid #f56c6c; background: #fef0f0; }
.q-header { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 14px; line-height: 1.6; }
.q-index { font-weight: 700; color: var(--text-primary); flex-shrink: 0; }
.q-type-tag { flex-shrink: 0; margin-top: 2px; }
.q-content { color: var(--text-primary); font-size: 15px; }
.option-group { display: flex; flex-direction: column; gap: 10px; padding-left: 24px; }
.judge-group { flex-direction: row; }
.option-item { line-height: 1.5; }
.option-item.option-correct :deep(.el-radio__label), .option-item.option-correct :deep(.el-checkbox__label) { color: #67c23a; font-weight: 700; }
.option-item.option-wrong :deep(.el-radio__label), .option-item.option-wrong :deep(.el-checkbox__label) { color: #f56c6c; font-weight: 700; }
.fill-input { margin-top: 8px; }
.check-btn-area { margin-top: 14px; padding-left: 24px; }

.answer-reveal { margin-top: 16px; padding: 14px 16px; border-radius: 6px; font-size: 14px; }
.reveal-correct { background: #f0f9eb; border: 1px solid #c2e7b0; }
.reveal-wrong { background: #fef0f0; border: 1px solid #fbc4c4; }
.reveal-header { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.reveal-body { padding-left: 24px; color: #606266; line-height: 1.8; }
.correct-answer { margin-bottom: 4px; }
.answer-highlight { color: #e6a23c; font-size: 15px; }
.analysis-text { color: #909399; }

/* ---- 单题模式导航 ---- */
.single-nav { display: flex; justify-content: center; align-items: center; gap: 24px; padding: 24px 0; }
.nav-indicator { font-size: 15px; font-weight: 600; color: var(--text-primary); }
</style>
