<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <SeoHead title="API密钥管理" description="管理API密钥的创建、查看和撤销" />

      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese mb-3">
          API 密钥管理
        </h1>
        <p class="text-gold-500/50 text-sm">创建和管理您的 API 访问密钥</p>
        <div class="w-16 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent mx-auto mt-4"></div>
      </div>

      <!-- 概览卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <p class="text-gold-500/60 text-sm mb-1">总密钥数</p>
          <p class="text-2xl font-bold text-gold-500">{{ keys.length }}</p>
        </div>
        <div class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <p class="text-gold-500/60 text-sm mb-1">活跃密钥</p>
          <p class="text-2xl font-bold text-green-400">{{ activeKeysCount }}</p>
        </div>
        <div class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <p class="text-gold-500/60 text-sm mb-1">本月调用次数</p>
          <p class="text-2xl font-bold text-gold-500">{{ totalUsage.toLocaleString() }}</p>
        </div>
      </div>

      <!-- 操作栏 -->
      <div class="mb-6 flex items-center justify-between">
        <span class="text-gold-500/60 text-sm">管理您的 API 访问凭证</span>
        <Button variant="primary" @click="showCreateModal = true">
          创建密钥
        </Button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="mt-8">
        <LoadingSpinner text="加载密钥列表中..." />
      </div>

      <!-- 空状态 -->
      <div v-else-if="keys.length === 0" class="text-center py-12">
        <EmptyState
          icon="🔑"
          title="暂无API密钥"
          description="创建一个API密钥以开始调用API"
        >
          <Button variant="primary" @click="showCreateModal = true">
            创建密钥
          </Button>
        </EmptyState>
      </div>

      <!-- 密钥列表 -->
      <div v-else class="space-y-4">
        <div
          v-for="key in keys"
          :key="key.key_id"
          class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm hover:border-gold-500/40 transition-colors duration-200"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <h3 class="text-gold-500 font-medium">{{ key.name }}</h3>
                <Badge :variant="key.status === 'active' ? 'success' : 'error'">
                  {{ key.status === 'active' ? '活跃' : '已撤销' }}
                </Badge>
              </div>
              <div class="flex items-center gap-4 text-sm">
                <span class="text-gold-500/60">
                  密钥: <code class="font-mono bg-ink-800 px-2 py-0.5 rounded text-gold-500/80">{{ maskKey(key.key) }}</code>
                </span>
                <span class="text-gold-500/40">{{ formatDate(key.created_at) }}</span>
              </div>
              <!-- 使用量 -->
              <div class="mt-3 flex items-center gap-4">
                <div class="flex-1 max-w-xs">
                  <div class="flex items-center justify-between text-xs mb-1">
                    <span class="text-gold-500/60">本月使用量</span>
                    <span class="text-gold-500/80">{{ key.usage?.current || 0 }} / {{ key.usage?.limit || '无限' }}</span>
                  </div>
                  <ProgressBar
                    :value="getUsagePercent(key)"
                    :variant="getUsageVariant(key)"
                  />
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  @click="viewUsage(key)"
                >
                  详情
                </Button>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0 ml-4">
              <Button
                v-if="key.status === 'active'"
                variant="secondary"
                size="sm"
                @click="copyKey(key.key)"
              >
                复制
              </Button>
              <Button
                v-if="key.status === 'active'"
                variant="danger"
                size="sm"
                @click="confirmRevoke(key)"
              >
                撤销
              </Button>
            </div>
          </div>
        </div>
      </div>

      <!-- 创建密钥弹窗 -->
      <Modal
        :visible="showCreateModal"
        title="创建API密钥"
        size="md"
        @update:visible="showCreateModal = $event"
      >
        <div class="space-y-4">
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">密钥名称 *</label>
            <InputField
              v-model="createForm.name"
              placeholder="例如: 生产环境密钥"
              label="密钥名称"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">所属者ID</label>
            <InputField
              v-model="createForm.owner_id"
              placeholder="输入所有者标识"
              label="所属者ID"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">权限</label>
            <InputField
              v-model="createForm.permissions"
              placeholder="例如: read,write"
              label="权限"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">调用限制 (次/天)</label>
            <InputField
              v-model="createForm.rate_limit"
              type="number"
              placeholder="留空表示无限制"
              label="调用限制"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">过期天数</label>
            <InputField
              v-model="createForm.expires_in_days"
              type="number"
              placeholder="留空表示永不过期"
              label="过期天数"
            />
          </div>
        </div>

        <template #footer>
          <Button
            variant="secondary"
            @click="showCreateModal = false"
          >
            取消
          </Button>
          <Button
            variant="primary"
            :disabled="!createForm.name || creating"
            @click="createKey"
          >
            {{ creating ? '创建中...' : '创建' }}
          </Button>
        </template>
      </Modal>

      <!-- 创建成功弹窗 -->
      <Modal
        :visible="showSuccessModal"
        title="密钥创建成功"
        size="md"
        @update:visible="showSuccessModal = $event"
      >
        <div class="space-y-4">
          <div class="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
            <p class="text-green-400 text-sm font-medium mb-2">请立即复制并安全保存您的密钥</p>
            <p class="text-gold-500/60 text-xs">密钥只会显示一次，关闭后将无法再次查看完整密钥。</p>
          </div>
          <div class="p-3 bg-ink-800 rounded-lg">
            <code class="text-gold-500 font-mono text-sm break-all">{{ createdKey }}</code>
          </div>
        </div>

        <template #footer>
          <Button
            variant="primary"
            @click="copyAndClose"
          >
            复制并关闭
          </Button>
        </template>
      </Modal>

      <!-- 使用详情弹窗 -->
      <Modal
        :visible="showUsageModal"
        title="使用详情"
        size="lg"
        @update:visible="showUsageModal = $event"
      >
        <div v-if="usageData" class="space-y-4">
          <div class="grid grid-cols-3 gap-4">
            <div class="p-4 bg-ink-800 rounded-lg text-center">
              <p class="text-gold-500/60 text-xs mb-1">速率限制</p>
              <p class="text-xl font-bold text-gold-500">{{ usageData.limit || 0 }}</p>
            </div>
            <div class="p-4 bg-ink-800 rounded-lg text-center">
              <p class="text-gold-500/60 text-xs mb-1">剩余配额</p>
              <p class="text-xl font-bold text-green-400">{{ usageData.remaining || 0 }}</p>
            </div>
            <div class="p-4 bg-ink-800 rounded-lg text-center">
              <p class="text-gold-500/60 text-xs mb-1">重置时间</p>
              <p class="text-xl font-bold text-gold-500">{{ formatDate(usageData.reset_at) }}</p>
            </div>
          </div>
        </div>
      </Modal>

      <!-- 撤销确认弹窗 -->
      <Modal
        :visible="showRevokeModal"
        title="确认撤销密钥"
        size="sm"
        @update:visible="showRevokeModal = $event"
      >
        <div v-if="keyToRevoke" class="space-y-4">
          <p class="text-gold-500/80">
            确定要撤销密钥 <span class="text-gold-500 font-medium">"{{ keyToRevoke.name }}"</span> 吗？
          </p>
          <div class="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p class="text-red-400 text-sm">撤销后，使用此密钥的所有应用将立即失去访问权限。此操作不可撤销。</p>
          </div>
        </div>

        <template #footer>
          <Button
            variant="secondary"
            @click="showRevokeModal = false"
          >
            取消
          </Button>
          <Button
            variant="danger"
            :disabled="revoking"
            @click="revokeKey"
          >
            {{ revoking ? '撤销中...' : '确认撤销' }}
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
const keys = ref<any[]>([])
const creating = ref(false)
const revoking = ref(false)

// 弹窗状态
const showCreateModal = ref(false)
const showSuccessModal = ref(false)
const showUsageModal = ref(false)
const showRevokeModal = ref(false)
const createdKey = ref('')
const usageData = ref<any>(null)
const keyToRevoke = ref<any>(null)

// 创建表单
const createForm = ref({
  name: '',
  owner_id: '',
  permissions: '',
  rate_limit: '',
  expires_in_days: '',
})

const expiresOptions = [
  { value: 'never', label: '永不过期' },
  { value: '30d', label: '30天' },
  { value: '90d', label: '90天' },
  { value: '180d', label: '180天' },
  { value: '365d', label: '1年' },
]

const usageColumns = [
  { key: 'endpoint', title: '接口' },
  { key: 'method', title: '方法' },
  { key: 'timestamp', title: '时间' },
  { key: 'status', title: '状态' },
]

const activeKeysCount = computed(() => keys.value.filter(k => k.status === 'active').length)
const totalUsage = computed(() => keys.value.reduce((sum, k) => sum + (k.usage?.current || 0), 0))

// 获取密钥列表
async function fetchKeys() {
  loading.value = true
  try {
    const { data, error } = await request('/api/api-platform/keys')
    if (error) {
      notification.error('加载失败', error)
      return
    }
    keys.value = data?.keys || []
  } catch (err) {
    notification.error('加载失败', '网络请求失败')
  } finally {
    loading.value = false
  }
}

// 创建密钥
async function createKey() {
  if (!createForm.value.name) return

  creating.value = true
  try {
    const { data, error } = await request('/api/api-platform/keys', {
      method: 'POST',
      body: {
        name: createForm.value.name,
        owner_id: createForm.value.owner_id || undefined,
        permissions: createForm.value.permissions
          ? createForm.value.permissions.split(',').map((s: string) => s.trim())
          : undefined,
        rate_limit: createForm.value.rate_limit ? parseInt(createForm.value.rate_limit) : undefined,
        expires_in_days: createForm.value.expires_in_days ? parseInt(createForm.value.expires_in_days) : undefined,
      },
    })

    if (error) {
      notification.error('创建失败', error)
      return
    }

    createdKey.value = data?.key || ''
    showCreateModal.value = false
    showSuccessModal.value = true
    createForm.value = { name: '', owner_id: '', permissions: '', rate_limit: '', expires_in_days: '' }
    await fetchKeys()
  } catch (err) {
    notification.error('创建失败', '网络请求失败')
  } finally {
    creating.value = false
  }
}

// 查看使用详情
async function viewUsage(key: any) {
  try {
    const { data, error } = await request(`/api/api-platform/keys/${key.key_id}/usage`)
    if (error) {
      notification.error('加载失败', error)
      return
    }
    usageData.value = data
    showUsageModal.value = true
  } catch (err) {
    notification.error('加载失败', '网络请求失败')
  }
}

// 确认撤销
function confirmRevoke(key: any) {
  keyToRevoke.value = key
  showRevokeModal.value = true
}

// 撤销密钥
async function revokeKey() {
  if (!keyToRevoke.value) return

  revoking.value = true
  try {
    const { error } = await request(`/api/api-platform/keys/${keyToRevoke.value.key_id}`, {
      method: 'DELETE',
    })

    if (error) {
      notification.error('撤销失败', error)
      return
    }

    notification.success('撤销成功', `密钥 "${keyToRevoke.value.name}" 已撤销`)
    showRevokeModal.value = false
    keyToRevoke.value = null
    await fetchKeys()
  } catch (err) {
    notification.error('撤销失败', '网络请求失败')
  } finally {
    revoking.value = false
  }
}

// 复制密钥
function copyKey(key: string) {
  navigator.clipboard.writeText(key).then(() => {
    notification.success('复制成功', '密钥已复制到剪贴板')
  }).catch(() => {
    notification.error('复制失败', '请手动复制')
  })
}

// 复制并关闭
function copyAndClose() {
  copyKey(createdKey.value)
  showSuccessModal.value = false
}

// 辅助函数
function maskKey(key: string) {
  if (!key) return '****'
  if (key.length <= 8) return '****'
  return key.substring(0, 4) + '****' + key.substring(key.length - 4)
}

function getUsagePercent(key: any) {
  if (!key.usage?.limit) return 0
  return Math.min(100, (key.usage.current / key.usage.limit) * 100)
}

function getUsageVariant(key: any) {
  const percent = getUsagePercent(key)
  if (percent >= 90) return 'error'
  if (percent >= 70) return 'warning'
  return 'default'
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

onMounted(() => fetchKeys())
</script>
