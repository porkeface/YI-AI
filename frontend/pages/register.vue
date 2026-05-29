<script setup lang="ts">
const { register, isAuthenticated, isLoading, error } = useAuth()
const router = useRouter()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const displayName = ref('')
const localError = ref('')

watch(isAuthenticated, (val) => {
  if (val) router.push('/')
})

async function handleRegister() {
  localError.value = ''
  if (password.value !== confirmPassword.value) {
    localError.value = '两次密码输入不一致'
    return
  }
  if (password.value.length < 8) {
    localError.value = '密码至少8个字符'
    return
  }
  await register(username.value, email.value, password.value, displayName.value || undefined)
}
</script>

<template>
  <div class="auth-page">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold gold-text">注册</h1>
        <p class="mt-2 subtitle-text">创建易学AI账号</p>
      </div>

      <div class="auth-card">
        <div v-if="error || localError" class="error-banner">
          {{ localError || error }}
        </div>

        <form @submit.prevent="handleRegister" class="space-y-4">
          <div>
            <label class="label-text">用户名 *</label>
            <input
              v-model="username"
              type="text"
              placeholder="3-50个字符，仅字母数字下划线"
              class="auth-input"
            />
          </div>

          <div>
            <label class="label-text">邮箱 *</label>
            <input
              v-model="email"
              type="email"
              placeholder="your@email.com"
              class="auth-input"
            />
          </div>

          <div>
            <label class="label-text">显示名称</label>
            <input
              v-model="displayName"
              type="text"
              placeholder="可选，默认为用户名"
              class="auth-input"
            />
          </div>

          <div>
            <label class="label-text">密码 *</label>
            <input
              v-model="password"
              type="password"
              placeholder="至少8个字符"
              class="auth-input"
            />
          </div>

          <div>
            <label class="label-text">确认密码 *</label>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="再次输入密码"
              class="auth-input"
            />
          </div>

          <button
            type="submit"
            :disabled="isLoading || !username || !email || !password || !confirmPassword"
            class="auth-btn"
          >
            {{ isLoading ? '注册中...' : '注册' }}
          </button>
        </form>

        <div class="mt-6 text-center text-sm footer-text">
          已有账号？
          <NuxtLink to="/login" class="link-text">立即登录</NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: linear-gradient(135deg, #0a0a0f 0%, #1a1520 50%, #0d0d14 100%);
}
.gold-text { color: #d4af37; }
.subtitle-text { color: #8b8b9e; }
.label-text { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem; color: #b0b0c0; }
.footer-text { color: #8b8b9e; }
.link-text { color: #d4af37; font-weight: 500; }
.link-text:hover { text-decoration: underline; }
.auth-card {
  border-radius: 0.75rem;
  padding: 2rem;
  background: rgba(26, 21, 32, 0.8);
  border: 1px solid rgba(212, 175, 55, 0.2);
  backdrop-filter: blur(12px);
}
.error-banner {
  margin-bottom: 1rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  background: rgba(220, 53, 69, 0.15);
  color: #ff6b6b;
  border: 1px solid rgba(220, 53, 69, 0.3);
}
.auth-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  color: white;
  outline: none;
  transition: border-color 0.3s;
  background: rgba(10, 10, 15, 0.6);
  border: 1px solid rgba(212, 175, 55, 0.15);
}
.auth-input:focus {
  border-color: rgba(212, 175, 55, 0.5);
}
.auth-btn {
  width: 100%;
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-weight: 500;
  color: black;
  transition: all 0.3s;
  background: linear-gradient(135deg, #d4af37, #f0d060);
}
.auth-btn:hover:not(:disabled) {
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
}
.auth-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
