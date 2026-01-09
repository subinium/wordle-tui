<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getLeaderboard, type LeaderboardEntry } from '../api'

const leaderboard = ref<LeaderboardEntry[]>([])
const isLoading = ref(true)

async function loadLeaderboard() {
  isLoading.value = true
  try {
    const data = await getLeaderboard(50)
    leaderboard.value = data.leaderboard
  } catch (e) {
    console.error('Failed to load leaderboard', e)
  }
  isLoading.value = false
}

onMounted(loadLeaderboard)
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">Leaderboard</h3>
    </div>

    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
    </div>

    <table v-else>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Username</th>
          <th>Current Streak</th>
          <th>Longest Streak</th>
          <th>Games</th>
          <th>Wins</th>
          <th>Win Rate</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="entry in leaderboard" :key="entry.rank">
          <td>
            <span class="rank" :class="{ 'rank-top': entry.rank <= 3 }">
              #{{ entry.rank }}
            </span>
          </td>
          <td>{{ entry.username }}</td>
          <td>{{ entry.current_streak }}</td>
          <td>{{ entry.longest_streak }}</td>
          <td>{{ entry.total_games }}</td>
          <td>{{ entry.total_wins }}</td>
          <td>{{ entry.win_rate }}%</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.rank {
  font-weight: 600;
}

.rank-top {
  color: var(--present);
}
</style>
