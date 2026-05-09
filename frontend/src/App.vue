<template>
  <el-config-provider>
    <div class="app-layout">
      <!-- 统一的严肃学术风格顶部导航 -->
      <header class="app-header">
        <div class="logo">
          <el-icon :size="24" color="#409eff"><Reading /></el-icon>
          <span class="title">智能做题系统 - 教研管理台</span>
        </div>
        <div class="user-info">
          <span>教研员</span>
          <el-avatar :size="32" icon="UserFilled" class="avatar" />
        </div>
      </header>

      <!-- 主要内容区域 -->
      <main class="app-main">
        <el-tabs v-model="activeTab" class="main-tabs" type="border-card">
          <el-tab-pane label="解析与校对台" name="console">
            <ProofreadConsole @start-exercise="startExercise" />
          </el-tab-pane>
          <el-tab-pane label="练习模式" name="exercise">
            <ExerciseView :questions="exerciseQuestions" :paper-title="exerciseTitle" @go-back="activeTab = 'console'" />
          </el-tab-pane>
          <el-tab-pane label="考试模式" name="exam">
            <ExamMode :questions="exerciseQuestions" @go-back="activeTab = 'console'" />
          </el-tab-pane>
          <el-tab-pane label="大模型设置" name="settings">
            <SettingsPanel />
          </el-tab-pane>
        </el-tabs>
      </main>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref } from 'vue'
import { Reading, UserFilled } from '@element-plus/icons-vue'
import ProofreadConsole from './components/ProofreadConsole.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import ExerciseView from './components/ExerciseView.vue'
import ExamMode from './components/ExamMode.vue'

const activeTab = ref('console')
const exerciseQuestions = ref([])
const exerciseTitle = ref('提取试卷')

const startExercise = ({ questions, title }) => {
  exerciseQuestions.value = questions
  exerciseTitle.value = title || '提取试卷'
  activeTab.value = 'exercise'
}
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  height: 60px;
  background-color: #ffffff;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  z-index: 10;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 14px;
  color: var(--text-regular);
}

.avatar {
  background-color: var(--bg-color);
  color: var(--text-regular);
}

.app-main {
  flex: 1;
  background-color: var(--bg-color);
  overflow-y: auto;
}
</style>
