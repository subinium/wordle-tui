<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUsers, type User } from '../api'

const users = ref<User[]>([])
const isLoading = ref(true)
const offset = ref(0)
const limit = 50

async function loadUsers() {
  isLoading.value = true
  try {
    const data = await getUsers({ limit, offset: offset.value })
    users.value = data.users
  } catch (e) {
    console.error('Failed to load users', e)
  }
  isLoading.value = false
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

onMounted(loadUsers)
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">Users ({{ users.length }})</h3>
    </div>

    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
    </div>

    <table v-else>
      <thead>
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Email</th>
          <th>Games</th>
          <th>Wins</th>
          <th>Streak</th>
          <th>Joined</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>{{ user.email || '-' }}</td>
          <td>{{ user.total_games }}</td>
          <td>{{ user.total_wins }}</td>
          <td>{{ user.current_streak }}</td>
          <td>{{ formatDate(user.created_at) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
