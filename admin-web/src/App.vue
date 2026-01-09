<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getGoogleAuthUrl, googleCallback, getAdminMe, setToken, clearToken, getToken } from './api'

const router = useRouter()
const isAuthenticated = ref(false)
const isLoading = ref(true)
const user = ref<{ username: string; email: string; avatar_url: string | null } | null>(null)
const error = ref<string | null>(null)

async function checkAuth() {
  const token = getToken()
  if (!token) {
    isLoading.value = false
    return
  }

  try {
    user.value = await getAdminMe()
    isAuthenticated.value = true
  } catch (e: any) {
    if (e.message.includes('403')) {
      error.value = 'Access denied. You are not an admin.'
    } else {
      clearToken()
    }
  }
  isLoading.value = false
}

async function handleOAuthCallback() {
  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')
  const state = localStorage.getItem('oauthState')

  if (code && state) {
    try {
      const redirectUri = `${window.location.origin}/admin/`
      const result = await googleCallback(code, state, redirectUri)
      if (result.success && result.token) {
        setToken(result.token)
        window.history.replaceState({}, '', '/admin/')
        await checkAuth()
      } else {
        error.value = result.error || 'Login failed'
      }
    } catch (e: any) {
      error.value = e.message
    }
    localStorage.removeItem('oauthState')
  }
}

async function login() {
  const redirectUri = `${window.location.origin}/admin/`
  const data = await getGoogleAuthUrl(redirectUri)
  localStorage.setItem('oauthState', data.state)
  window.location.href = data.auth_url
}

function logout() {
  clearToken()
  isAuthenticated.value = false
  user.value = null
  router.push('/')
}

onMounted(async () => {
  await handleOAuthCallback()
  if (!isAuthenticated.value) {
    await checkAuth()
  }
})
</script>

<template>
  <div class="app">
    <!-- Loading -->
    <div v-if="isLoading" class="login-container">
      <div class="spinner"></div>
    </div>

    <!-- Login -->
    <div v-else-if="!isAuthenticated && !error" class="login-container">
      <h1 class="login-title">Wordle TUI Admin</h1>
      <button class="google-btn" @click="login">
        <svg width="18" height="18" viewBox="0 0 18 18">
          <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"></path>
          <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 0 1-7.18-2.54H1.83v2.07A8 8 0 0 0 8.98 17z"></path>
          <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 0 1 0-3.04V5.41H1.83a8 8 0 0 0 0 7.18l2.67-2.07z"></path>
          <path fill="#EA4335" d="M8.98 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58A8 8 0 0 0 1.83 5.4l2.67 2.07A4.8 4.8 0 0 1 8.98 3.58z"></path>
        </svg>
        Sign in with Google
      </button>
      <p class="login-hint">Admin access only</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="login-container">
      <h1 class="login-title">Wordle TUI Admin</h1>
      <div class="message message-error">{{ error }}</div>
      <button class="btn btn-secondary" @click="error = null; clearToken()">Try Again</button>
    </div>

    <!-- Dashboard -->
    <div v-else class="dashboard">
      <header class="header">
        <h1 class="header-title">Wordle TUI Admin</h1>
        <div class="user-info">
          <img v-if="user?.avatar_url" :src="user.avatar_url" alt="avatar" class="avatar" />
          <span class="username">{{ user?.username }}</span>
          <button class="btn btn-secondary btn-sm" @click="logout">Logout</button>
        </div>
      </header>

      <nav class="nav">
        <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' || $route.path === '/admin/' }">
          Overview
        </router-link>
        <router-link to="/words" class="nav-link" :class="{ active: $route.path === '/words' }">
          Words
        </router-link>
        <router-link to="/users" class="nav-link" :class="{ active: $route.path === '/users' }">
          Users
        </router-link>
        <router-link to="/leaderboard" class="nav-link" :class="{ active: $route.path === '/leaderboard' }">
          Leaderboard
        </router-link>
      </nav>

      <main class="container">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
}

.login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 20px;
}

.login-title {
  font-size: 2rem;
  color: var(--correct);
}

.login-hint {
  color: var(--text-muted);
  font-size: 14px;
}

.google-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: white;
  color: #333;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.google-btn:hover {
  background: #f0f0f0;
}

.dashboard {
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
}

.header-title {
  font-size: 20px;
  color: var(--correct);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.username {
  font-size: 14px;
  color: var(--text-secondary);
}

.nav {
  display: flex;
  gap: 4px;
  padding: 0 24px;
  border-bottom: 1px solid var(--border);
}

.nav-link {
  padding: 12px 20px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.nav-link:hover {
  color: var(--text-primary);
}

.nav-link.active {
  color: var(--correct);
  border-bottom-color: var(--correct);
}
</style>
