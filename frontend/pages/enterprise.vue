<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <SeoHead title="企业管理" description="多租户管理与用户配置" />

      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese mb-3">
          企业管理
        </h1>
        <p class="text-gold-500/50 text-sm">租户管理与用户配置</p>
        <div class="w-16 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent mx-auto mt-4"></div>
      </div>

      <!-- 概览卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <p class="text-gold-500/60 text-sm mb-1">租户总数</p>
          <p class="text-2xl font-bold text-gold-500">{{ tenants.length }}</p>
        </div>
        <div class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <p class="text-gold-500/60 text-sm mb-1">活跃租户</p>
          <p class="text-2xl font-bold text-green-400">{{ activeTenantsCount }}</p>
        </div>
        <div class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <p class="text-gold-500/60 text-sm mb-1">总用户数</p>
          <p class="text-2xl font-bold text-gold-500">{{ totalUsers }}</p>
        </div>
        <div class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <p class="text-gold-500/60 text-sm mb-1">总配额使用</p>
          <p class="text-2xl font-bold text-gold-500">{{ totalQuotaUsage }}%</p>
        </div>
      </div>

      <!-- 操作栏 -->
      <div class="mb-6 flex items-center justify-between">
        <span class="text-gold-500/60 text-sm">管理企业租户和用户</span>
        <Button variant="primary" @click="showCreateModal = true">
          创建租户
        </Button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="mt-8">
        <LoadingSpinner text="加载租户列表中..." />
      </div>

      <!-- 空状态 -->
      <div v-else-if="tenants.length === 0" class="text-center py-12">
        <EmptyState
          icon="🏢"
          title="暂无租户"
          description="创建第一个企业租户开始使用"
        >
          <Button variant="primary" @click="showCreateModal = true">
            创建租户
          </Button>
        </EmptyState>
      </div>

      <!-- 租户列表 -->
      <div v-else class="space-y-4">
        <div
          v-for="tenant in tenants"
          :key="tenant.tenant_id"
          class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm hover:border-gold-500/40 transition-colors duration-200"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <div class="w-10 h-10 rounded-lg bg-gold-500/10 flex items-center justify-center">
                  <span class="text-gold-400 text-lg">🏢</span>
                </div>
                <div>
                  <h3 class="text-gold-500 font-medium">{{ tenant.name }}</h3>
                  <p class="text-gold-500/50 text-xs">ID: {{ tenant.tenant_id }}</p>
                </div>
                <Badge :variant="tenant.status === 'active' ? 'success' : tenant.status === 'suspended' ? 'error' : 'warning'">
                  {{ tenant.status === 'active' ? '活跃' : tenant.status === 'suspended' ? '已暂停' : '待激活' }}
                </Badge>
              </div>

              <!-- 配额使用 -->
              <div class="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <div class="flex items-center justify-between text-xs mb-1">
                    <span class="text-gold-500/60">用户配额</span>
                    <span class="text-gold-500/80">{{ tenant.users?.length || 0 }} / {{ tenant.quota?.users || '无限' }}</span>
                  </div>
                  <ProgressBar
                    :value="getUserQuotaPercent(tenant)"
                    :variant="getQuotaVariant(getUserQuotaPercent(tenant))"
                  />
                </div>
                <div>
                  <div class="flex items-center justify-between text-xs mb-1">
                    <span class="text-gold-500/60">API调用配额</span>
                    <span class="text-gold-500/80">{{ tenant.quota?.apiCalls?.used || 0 }} / {{ tenant.quota?.apiCalls?.limit || '无限' }}</span>
                  </div>
                  <ProgressBar
                    :value="getApiQuotaPercent(tenant)"
                    :variant="getQuotaVariant(getApiQuotaPercent(tenant))"
                  />
                </div>
                <div>
                  <div class="flex items-center justify-between text-xs mb-1">
                    <span class="text-gold-500/60">存储配额</span>
                    <span class="text-gold-500/80">{{ formatStorage(tenant.quota?.storage?.used || 0) }} / {{ formatStorage(tenant.quota?.storage?.limit || 0) }}</span>
                  </div>
                  <ProgressBar
                    :value="getStorageQuotaPercent(tenant)"
                    :variant="getQuotaVariant(getStorageQuotaPercent(tenant))"
                  />
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2 shrink-0 ml-4">
              <Button
                variant="secondary"
                size="sm"
                @click="viewTenant(tenant)"
              >
                详情
              </Button>
              <Button
                variant="primary"
                size="sm"
                @click="openAddUser(tenant)"
              >
                添加用户
              </Button>
            </div>
          </div>
        </div>
      </div>

      <!-- 创建租户弹窗 -->
      <Modal
        :visible="showCreateModal"
        title="创建租户"
        size="md"
        @update:visible="showCreateModal = $event"
      >
        <div class="space-y-4">
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">租户名称 *</label>
            <InputField
              v-model="createForm.name"
              placeholder="输入企业/组织名称"
              label="租户名称"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">最大用户数</label>
            <InputField
              v-model="createForm.max_users"
              type="number"
              placeholder="例如: 100"
              label="最大用户数"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">每日最大API调用次数</label>
            <InputField
              v-model="createForm.max_api_calls_per_day"
              type="number"
              placeholder="例如: 10000"
              label="每日最大API调用次数"
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
            @click="createTenant"
          >
            {{ creating ? '创建中...' : '创建' }}
          </Button>
        </template>
      </Modal>

      <!-- 租户详情弹窗 -->
      <Modal
        :visible="showDetailModal"
        title="租户详情"
        size="lg"
        @update:visible="showDetailModal = $event"
      >
        <div v-if="selectedTenant" class="space-y-6">
          <!-- 基本信息 -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-gold-500/60 text-xs mb-1">租户名称</p>
              <p class="text-gold-500 font-medium">{{ selectedTenant.name }}</p>
            </div>
            <div>
              <p class="text-gold-500/60 text-xs mb-1">状态</p>
              <Badge :variant="selectedTenant.status === 'active' ? 'success' : selectedTenant.status === 'suspended' ? 'error' : 'warning'">
                {{ selectedTenant.status === 'active' ? '活跃' : selectedTenant.status === 'suspended' ? '已暂停' : '待激活' }}
              </Badge>
            </div>
            <div>
              <p class="text-gold-500/60 text-xs mb-1">套餐</p>
              <p class="text-gold-500">{{ selectedTenant.plan || '免费版' }}</p>
            </div>
            <div>
              <p class="text-gold-500/60 text-xs mb-1">创建时间</p>
              <p class="text-gold-500/80 text-sm">{{ formatDate(selectedTenant.created_at) }}</p>
            </div>
          </div>

          <!-- 用户列表 -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h4 class="text-gold-500 font-medium">用户列表</h4>
              <Button
                variant="secondary"
                size="sm"
                @click="openAddUser(selectedTenant)"
              >
                添加用户
              </Button>
            </div>
            <div v-if="selectedTenant.users?.length" class="rounded-lg border border-gold-500/20 overflow-hidden">
              <DataTable
                :columns="userColumns"
                :data="selectedTenant.users"
              >
                <template #role="{ row }">
                  <Badge :variant="row.role === 'admin' ? 'warning' : row.role === 'analyst' ? 'info' : 'default'">
                    {{ row.role === 'admin' ? '管理员' : row.role === 'analyst' ? '分析师' : '查看者' }}
                  </Badge>
                </template>
                <template #status="{ row }">
                  <Badge :variant="row.status === 'active' ? 'success' : 'default'">
                    {{ row.status === 'active' ? '活跃' : '未激活' }}
                  </Badge>
                </template>
              </DataTable>
            </div>
            <div v-else class="text-center py-6 text-gold-500/60 text-sm">
              暂无用户
            </div>
          </div>
        </div>
      </Modal>

      <!-- 添加用户弹窗 -->
      <Modal
        :visible="showAddUserModal"
        title="添加用户"
        size="md"
        @update:visible="showAddUserModal = $event"
      >
        <div class="space-y-4">
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">用户ID *</label>
            <InputField
              v-model="addUserForm.user_id"
              placeholder="输入用户ID"
              label="用户ID"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">邮箱 *</label>
            <InputField
              v-model="addUserForm.email"
              type="email"
              placeholder="user@example.com"
              label="邮箱"
            />
          </div>
          <div>
            <label class="block text-gold-500/80 text-sm mb-2">角色</label>
            <Select
              v-model="addUserForm.role"
              :options="roleOptions"
            />
          </div>
        </div>

        <template #footer>
          <Button
            variant="secondary"
            @click="showAddUserModal = false"
          >
            取消
          </Button>
          <Button
            variant="primary"
            :disabled="!addUserForm.user_id || !addUserForm.email || addingUser"
            @click="addUser"
          >
            {{ addingUser ? '添加中...' : '添加' }}
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
const tenants = ref<any[]>([])
const creating = ref(false)
const addingUser = ref(false)

// 弹窗状态
const showCreateModal = ref(false)
const showDetailModal = ref(false)
const showAddUserModal = ref(false)
const selectedTenant = ref<any>(null)
const tenantForUser = ref<any>(null)

// 创建表单
const createForm = ref({
  name: '',
  max_users: '',
  max_api_calls_per_day: '',
})

// 添加用户表单
const addUserForm = ref({
  user_id: '',
  email: '',
  role: 'viewer',
})

const planOptions = [
  { value: 'free', label: '免费版' },
  { value: 'basic', label: '基础版' },
  { value: 'pro', label: '专业版' },
  { value: 'enterprise', label: '企业版' },
]

const roleOptions = [
  { value: 'admin', label: '管理员' },
  { value: 'analyst', label: '分析师' },
  { value: 'viewer', label: '查看者' },
]

const userColumns = [
  { key: 'username', title: '用户名' },
  { key: 'email', title: '邮箱' },
  { key: 'role', title: '角色' },
  { key: 'status', title: '状态' },
]

const activeTenantsCount = computed(() => tenants.value.filter(t => t.status === 'active').length)
const totalUsers = computed(() => tenants.value.reduce((sum, t) => sum + (t.users?.length || 0), 0))
const totalQuotaUsage = computed(() => {
  if (tenants.value.length === 0) return 0
  const total = tenants.value.reduce((sum, t) => sum + getUserQuotaPercent(t), 0)
  return Math.round(total / tenants.value.length)
})

// 获取租户列表
async function fetchTenants() {
  loading.value = true
  try {
    const { data, error } = await request('/api/enterprise/tenants')
    if (error) {
      notification.error('加载失败', error)
      return
    }
    tenants.value = data?.tenants || []
  } catch (err) {
    notification.error('加载失败', '网络请求失败')
  } finally {
    loading.value = false
  }
}

// 创建租户
async function createTenant() {
  if (!createForm.value.name) return

  creating.value = true
  try {
    const { error } = await request('/api/enterprise/tenants', {
      method: 'POST',
      body: {
        name: createForm.value.name,
        max_users: createForm.value.max_users ? parseInt(createForm.value.max_users) : undefined,
        max_api_calls_per_day: createForm.value.max_api_calls_per_day ? parseInt(createForm.value.max_api_calls_per_day) : undefined,
      },
    })

    if (error) {
      notification.error('创建失败', error)
      return
    }

    notification.success('创建成功', `租户 "${createForm.value.name}" 已创建`)
    showCreateModal.value = false
    createForm.value = { name: '', max_users: '', max_api_calls_per_day: '' }
    await fetchTenants()
  } catch (err) {
    notification.error('创建失败', '网络请求失败')
  } finally {
    creating.value = false
  }
}

// 查看租户详情
async function viewTenant(tenant: any) {
  try {
    const { data, error } = await request(`/api/enterprise/tenants/${tenant.tenant_id}`)
    if (error) {
      notification.error('加载失败', error)
      return
    }
    selectedTenant.value = data || tenant
    showDetailModal.value = true
  } catch (err) {
    selectedTenant.value = tenant
    showDetailModal.value = true
  }
}

// 打开添加用户弹窗
function openAddUser(tenant: any) {
  tenantForUser.value = tenant
  addUserForm.value = { user_id: '', email: '', role: 'viewer' }
  showAddUserModal.value = true
}

// 添加用户
async function addUser() {
  if (!tenantForUser.value || !addUserForm.value.user_id || !addUserForm.value.email) return

  addingUser.value = true
  try {
    const { error } = await request(`/api/enterprise/tenants/${tenantForUser.value.tenant_id}/users`, {
      method: 'POST',
      body: {
        user_id: addUserForm.value.user_id,
        email: addUserForm.value.email,
        role: addUserForm.value.role,
      },
    })

    if (error) {
      notification.error('添加失败', error)
      return
    }

    notification.success('添加成功', `用户 "${addUserForm.value.user_id}" 已添加`)
    showAddUserModal.value = false
    await fetchTenants()
    // 如果详情弹窗打开，刷新详情
    if (showDetailModal.value && selectedTenant.value) {
      await viewTenant(selectedTenant.value)
    }
  } catch (err) {
    notification.error('添加失败', '网络请求失败')
  } finally {
    addingUser.value = false
  }
}

// 辅助函数
function getUserQuotaPercent(tenant: any) {
  if (!tenant.quota?.users) return 0
  return Math.min(100, ((tenant.users?.length || 0) / tenant.quota.users) * 100)
}

function getApiQuotaPercent(tenant: any) {
  if (!tenant.quota?.apiCalls?.limit) return 0
  return Math.min(100, ((tenant.quota.apiCalls.used || 0) / tenant.quota.apiCalls.limit) * 100)
}

function getStorageQuotaPercent(tenant: any) {
  if (!tenant.quota?.storage?.limit) return 0
  return Math.min(100, ((tenant.quota.storage.used || 0) / tenant.quota.storage.limit) * 100)
}

function getQuotaVariant(percent: number) {
  if (percent >= 90) return 'error'
  if (percent >= 70) return 'warning'
  return 'default'
}

function formatStorage(bytes: number) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
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

onMounted(() => fetchTenants())
</script>
