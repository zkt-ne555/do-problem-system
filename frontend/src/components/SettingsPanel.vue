<template>
  <el-card shadow="never" class="settings-card">
    <template #header>
      <div class="card-header">
        <span>大模型参数配置</span>
      </div>
    </template>
    
    <el-form label-width="120px" style="max-width: 600px;">
      <el-form-item label="快捷预设">
        <el-select v-model="selectedPreset" placeholder="选择预设模型" @change="applyPreset" style="width: 100%;">
          <el-option label="DeepSeek V3 (深度求索)" value="deepseek-chat" />
          <el-option label="DeepSeek R1 (深度思考)" value="deepseek-reasoner" />
          <el-option label="Kimi (月之暗面)" value="moonshot-v1-8k" />
          <el-option label="Doubao (火山引擎)" value="doubao" />
          <el-option label="Gemini 1.5 Pro" value="gemini-1.5-pro" />
          <el-option label="自定义 (Custom)" value="custom" />
        </el-select>
      </el-form-item>

      <el-form-item label="Base URL">
        <el-input v-model="settings.baseUrl" placeholder="例如: https://api.deepseek.com/v1" />
      </el-form-item>

      <el-form-item label="Model 名称">
        <el-input v-model="settings.model" placeholder="例如: deepseek-chat" />
        <div class="tip" v-if="selectedPreset === 'doubao'">
          * 豆包模型请在此处填写您在控制台创建的 Endpoint ID (例如: ep-20240101-xxx)
        </div>
      </el-form-item>

      <el-form-item label="API Key">
        <el-input v-model="settings.apiKey" type="password" show-password placeholder="输入对应模型的 API Key" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
        <span class="save-tip" v-if="lastSaved">上次保存: {{ lastSaved }}</span>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const presets = {
  'deepseek-chat': { url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  'deepseek-reasoner': { url: 'https://api.deepseek.com/v1', model: 'deepseek-reasoner' },
  'moonshot-v1-8k': { url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  'doubao': { url: 'https://ark.cn-beijing.volces.com/api/v3', model: 'ep-这里填写您的EndpointID' },
  'gemini-1.5-pro': { url: 'https://generativelanguage.googleapis.com/v1beta/openai/', model: 'gemini-1.5-pro' }
}

const selectedPreset = ref('')
const lastSaved = ref('')

const settings = reactive({
  baseUrl: '',
  model: '',
  apiKey: ''
})

onMounted(() => {
  const saved = localStorage.getItem('llm_settings')
  if (saved) {
    Object.assign(settings, JSON.parse(saved))
    // 尝试匹配预设
    const match = Object.keys(presets).find(k => presets[k].model === settings.model && presets[k].url === settings.baseUrl)
    selectedPreset.value = match || 'custom'
  }
})

const applyPreset = (presetKey) => {
  if (presetKey === 'custom') return
  const preset = presets[presetKey]
  if (preset) {
    settings.baseUrl = preset.url
    settings.model = preset.model
  }
}

const saveSettings = () => {
  if (!settings.apiKey) {
    ElMessage.warning('建议填写 API Key，否则可能调用失败')
  }
  localStorage.setItem('llm_settings', JSON.stringify(settings))
  lastSaved.value = new Date().toLocaleTimeString()
  ElMessage.success('设置已保存到本地。校对台将使用最新配置。')
}
</script>

<style scoped>
.settings-card {
  margin: 20px auto;
  max-width: 800px;
}
.card-header {
  font-weight: bold;
}
.tip {
  font-size: 12px;
  color: #E6A23C;
  line-height: 1.2;
  margin-top: 5px;
}
.save-tip {
  margin-left: 15px;
  font-size: 13px;
  color: var(--text-regular);
}
</style>
