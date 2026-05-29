<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <SeoHead title="插件管理" description="管理系统插件的注册、启用和禁用" />

      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese mb-3">
          插件管理
        </h1>
        <p class="text-gold-500/50 text-sm">注册、启用和管理系统插件</p>
        <div class="w-16 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent mx-auto mt-4"></div>
      </div>

      <!-- 操作栏 -->
      <div class="mb-6 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-gold-500/60 text-sm">共 {{ plugins.length }} 个插件</span>
          <Badge variant="success">{{ enabledCount }} 已启用</Badge>
          <Badge variant="default">{{ plugins.length - enabledCount }} 已禁用</Badge>
        </div>
        <Button variant="primary" @click="showRegisterModal = true">
          注册插件
        </Button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="mt-8">
        <LoadingSpinner text="加载插件列表中..." />
      </div>

      <!-- 空状态 -->
      <div v-else-if="plugins.length === 0" class="text-center py-12">
        <EmptyState
          icon="🧩"
          title="暂无插件"
          description="点击注册插件按钮添加新插件"
        >
          <Button variant="primary" @click="showRegisterModal = true">
            注册插件
          </Button>
        </EmptyState>
      </div>

      <!-- 插件列表 -->
      <div v-else class="rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm overflow-hidden">
        <DataTable
          :columns="columns"
          :data="plugins"
        >
          <template #name="{ row }">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-gold-500/10 flex items-center justify-center">
                <span class="text-gold-400 text-sm">{{ getPluginIcon(row.plugin_type) }}</span>
              </div>
              <div>
                <p class="text-gold-500 font-medium">{{ row.name }}</p>
                <p class="text-gold-500/50 text-xs">{{ row.description || '无描述' }}</p>
              </div>
            </div>
          </template>

          <template #type="{ row }">
            <Badge :variant="getTypeVariant(row.plugin_type)">
              {{ row.plugin_type }}
            </Badge>
          </template>

          <template #status="{ row }">
            <div class="flex items-center gap-2">
              <Toggle
                :model-value="row.enabled"
                @update:model-value="togglePlugin(row)"
              />
              <span
                class="text-xs"
                :class="row.enabled ? 'text-green-400' : 'text-gold-500/40'"
              >
                {{ row.enabled ? '已启用' : '已禁用' }}
              </span>
            </div>
          </template>

          <template #version="{ row }">
            <span class="text-gold-500/70 text-sm font-mono">{{ row.version || '-' }}</span>
          </template>

          <template #actions="{ row }">
            <div class="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                @click="viewPlugin(row)"
              >
                详情
              </Button>
              <Button
                variant="danger"
                size="sm"
                @click="confirmDelete(row)"
              >
                删除
              </Button>
            </div>
          </template>
        </DataTable>
      </div>

      <!-- 注册插件弹窗 -->
      <Modal
        :visible="showRegisterModal"
        title="注册新插件"
        size="md"
        @update:visible="showRegisterModal = $event"
      >
        <div class="space-y-4">
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">插件名称 *</label>
            <InputField
              v-model="registerForm.name"
              placeholder="输入插件名称"
              label="插件名称"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">插件类型 *</label>
            <Select
              v-model="registerForm.plugin_type"
              :options="pluginTypeOptions"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">版本号</label>
            <InputField
              v-model="registerForm.version"
              placeholder="例如: 1.0.0"
              label="版本号"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">描述</label>
            <Textarea
              v-model="registerForm.description"
              placeholder="输入插件描述..."
              :rows="3"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">作者</label>
            <InputField
              v-model="registerForm.author"
              placeholder="输入作者名称"
              label="作者"
            />
          </div>
        </div>

        <template #footer>
          <Button
            variant="secondary"
            @click="showRegisterModal = false"
          >
            取消
          </Button>
          <Button
            variant="primary"
            :disabled="!registerForm.name || !registerForm.plugin_type || registering"
            @click="registerPlugin"
          >
            {{ registering ? '注册中...' : '注册' }}
          </Button>
        </template>
      </Modal>

      <!-- 插件详情弹窗 -->
      <Modal
        :visible="showDetailModal"
        title="插件详情"
        size="lg"
        @update:visible="showDetailModal = $event"
      >
        <div v-if="selectedPlugin" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-gold-500/60 text-xs mb-1">名称</p>
              <p class="text-gold-500 font-medium">{{ selectedPlugin.name }}</p>
            </div>
            <div>
              <p class="text-gold-500/60 text-xs mb-1">类型</p>
              <Badge :variant="getTypeVariant(selectedPlugin.plugin_type)">
                {{ selectedPlugin.plugin_type }}
              </Badge>
            </div>
            <div>
              <p class="text-gold-500/60 text-xs mb-1">版本</p>
              <p class="text-gold-500 font-mono">{{ selectedPlugin.version || '-' }}</p>
            </div>
            <div>
              <p class="text-gold-500/60 text-xs mb-1">状态</p>
              <Badge :variant="selectedPlugin.enabled ? 'success' : 'default'">
                {{ selectedPlugin.enabled ? '已启用' : '已禁用' }}
              </Badge>
            </div>
          </div>
          <div>
            <p class="text-gold-500/60 text-xs mb-1">描述</p>
            <p class="text-gold-500/80 text-sm">{{ selectedPlugin.description || '无描述' }}</p>
          </div>
          <div v-if="selectedPlugin.config">
            <p class="text-gold-500/60 text-xs mb-1">配置</p>
            <pre class="p-3 bg-ink-800 rounded-lg text-gold-500/70 text-xs overflow-x-auto">{{ formatJson(selectedPlugin.config) }}</pre>
          </div>
          <div>
            <p class="text-gold-500/60 text-xs mb-1">注册时间</p>
            <p class="text-gold-500/80 text-sm">{{ formatDate(selectedPlugin.createdAt) }}</p>
          </div>
        </div>
      </Modal>

      <!-- 删除确认弹窗 -->
      <Modal
        :visible="showDeleteModal"
        title="确认删除"
        size="sm"
        @update:visible="showDeleteModal = $event"
      >
        <div v-if="pluginToDelete" class="space-y-4">
          <p class="text-gold-500/80">
            确定要删除插件 <span class="text-gold-500 font-medium">"{{ pluginToDelete.name }}"</span> 吗？
          </p>
          <p class="text-red-400 text-sm">此操作不可撤销。</p>
        </div>

        <template #footer>
          <Button
            variant="secondary"
            @click="showDeleteModal = false"
          >
            取消
          </Button>
          <Button
            variant="danger"
            :disabled="deleting"
            @click="deletePlugin"
          >
            {{ deleting ? '删除中...' : '确认删除' }}
          </Button>
        </template>
      </Modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

definePageMeta({ middleware: 'auth' })

const { request } = useApi()
const notification = useNotification()

const loading = ref(false)
const plugins = ref<any[]>([])
const registering = ref(false)
const deleting = ref(false)

// 弹窗状态
const showRegisterModal = ref(false)
const showDetailModal = ref(false)
const showDeleteModal = ref(false)
const selectedPlugin = ref<any>(null)
const pluginToDelete = ref<any>(null)

// 注册表单
const registerForm = ref({
  name: '',
  plugin_type: 'divination',
  version: '',
  description: '',
  author: '',
})

const columns = [
  { key: 'name', title: '插件名称' },
  { key: 'type', title: '类型' },
  { key: 'version', title: '版本' },
  { key: 'status', title: '状态' },
  { key: 'actions', title: '操作' },
]

const pluginTypeOptions = [
  { value: 'divination', label: '起卦插件' },
  { value: 'analysis', label: '分析插件' },
  { value: 'interpret', label: '解读插件' },
  { value: 'rag', label: 'RAG插件' },
  { value: 'export', label: '导出插件' },
]

const enabledCount = computed(() => plugins.value.filter(p => p.enabled).length)

// 获取插件列表
async function fetchPlugins() {
  loading.value = true
  try {
    const { data, error } = await request('/api/plugins/list')
    if (error) {
      notification.error('加载失败', error)
      return
    }
    plugins.value = data?.plugins || []
  } catch (err) {
    notification.error('加载失败', '网络请求失败')
  } finally {
    loading.value = false
  }
}

// 注册插件
async function registerPlugin() {
  if (!registerForm.value.name || !registerForm.value.plugin_type) return

  registering.value = true
  try {
    const { data, error } = await request('/api/plugins/register', {
      method: 'POST',
      body: {
        plugin_id: registerForm.value.name,
        name: registerForm.value.name,
        plugin_type: registerForm.value.plugin_type,
        version: registerForm.value.version || undefined,
        description: registerForm.value.description || undefined,
        author: registerForm.value.author || undefined,
        enabled: true,
      },
    })

    if (error) {
      notification.error('注册失败', error)
      return
    }

    notification.success('注册成功', `插件 "${registerForm.value.name}" 已注册`)
    showRegisterModal.value = false
    registerForm.value = { name: '', plugin_type: 'divination', version: '', description: '', author: '' }
    await fetchPlugins()
  } catch (err) {
    notification.error('注册失败', '网络请求失败')
  } finally {
    registering.value = false
  }
}

// 切换插件状态
async function togglePlugin(plugin: any) {
  try {
    const { error } = await request(`/api/plugins/${plugin.plugin_id}/toggle`, {
      method: 'PUT',
      body: { enabled: !plugin.enabled },
    })

    if (error) {
      notification.error('操作失败', error)
      return
    }

    plugin.enabled = !plugin.enabled
    notification.success(
      '操作成功',
      `插件 "${plugin.name}" 已${plugin.enabled ? '启用' : '禁用'}`
    )
  } catch (err) {
    notification.error('操作失败', '网络请求失败')
  }
}

// 查看插件详情
function viewPlugin(plugin: any) {
  selectedPlugin.value = plugin
  showDetailModal.value = true
}

// 确认删除
function confirmDelete(plugin: any) {
  pluginToDelete.value = plugin
  showDeleteModal.value = true
}

// 删除插件
async function deletePlugin() {
  if (!pluginToDelete.value) return

  deleting.value = true
  try {
    const { error } = await request(`/api/plugins/${pluginToDelete.value.plugin_id}`, {
      method: 'DELETE',
    })

    if (error) {
      notification.error('删除失败', error)
      return
    }

    notification.success('删除成功', `插件 "${pluginToDelete.value.name}" 已删除`)
    showDeleteModal.value = false
    pluginToDelete.value = null
    await fetchPlugins()
  } catch (err) {
    notification.error('删除失败', '网络请求失败')
  } finally {
    deleting.value = false
  }
}

// 辅助函数
function getPluginIcon(type: string) {
  const icons: Record<string, string> = {
    divination: '🔮',
    analysis: '📊',
    interpret: '📖',
    rag: '📚',
    export: '📤',
  }
  return icons[type] || '📦'
}

function getTypeVariant(type: string) {
  const variants: Record<string, string> = {
    divination: 'default',
    analysis: 'info',
    interpret: 'success',
    rag: 'warning',
    export: 'default',
  }
  return variants[type] || 'default'
}

function formatDate(iso: string) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatJson(obj: any) {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

onMounted(() => fetchPlugins())
</script>
