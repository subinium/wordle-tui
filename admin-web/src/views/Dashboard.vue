<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getStats, getDailyStats, getTodayLeaderboard, type TodayLeaderboardEntry } from '../api'

const stats = ref<Awaited<ReturnType<typeof getStats>> | null>(null)
const distribution = ref<Record<string, number>>({})
const todayLeaderboard = ref<TodayLeaderboardEntry[]>([])
const isLoading = ref(true)

async function loadData() {
  try {
    const [statsData, todayLbData] = await Promise.all([
      getStats(),
      getTodayLeaderboard(10)
    ])
    stats.value = statsData
    todayLeaderboard.value = todayLbData.leaderboard

    if (statsData.today.date) {
      const dailyData = await getDailyStats(statsData.today.date)
      distribution.value = dailyData.distribution || {}
    }
  } catch (e) {
    console.error('Failed to load data', e)
  }
  isLoading.value = false
}

function maxDistribution(): number {
  const values = Object.values(distribution.value)
  return Math.max(...values, 1)
}

function formatTime(seconds: number | null): string {
  if (seconds === null) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onMounted(loadData)
</script>

<template>
  <div>
    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
    </div>

    <template v-else-if="stats">
      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total Users</div>
          <div class="stat-value">{{ stats.total_users }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Games</div>
          <div class="stat-value">{{ stats.total_games }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Games Solved</div>
          <div class="stat-value">{{ stats.total_solved }}</div>
          <div class="stat-sub">{{ stats.solve_rate }}% solve rate</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Avg Attempts</div>
          <div class="stat-value">{{ stats.avg_attempts || '-' }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Active (7d)</div>
          <div class="stat-value">{{ stats.active_users_7d }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Today's Word</div>
          <div class="stat-value word-display">{{ stats.today.word || '-' }}</div>
          <div class="stat-sub">{{ stats.today.games }} games, {{ stats.today.solved }} solved</div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="charts-row">
        <!-- Distribution Chart -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Today's Attempts Distribution</h3>
          </div>
          <div class="distribution-chart">
            <div v-for="n in 6" :key="n" class="distribution-row">
              <span class="distribution-label">{{ n }}</span>
              <div class="distribution-bar-container">
                <div
                  class="distribution-bar"
                  :style="{ width: `${(distribution[String(n)] || 0) / maxDistribution() * 100}%` }"
                >
                  <span class="distribution-count">{{ distribution[String(n)] || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Today's Leaderboard -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Today's Leaderboard</h3>
          </div>
          <div v-if="todayLeaderboard.length === 0" class="empty-state">
            No games played today yet
          </div>
          <table v-else>
            <thead>
              <tr>
                <th>Rank</th>
                <th>User</th>
                <th>Result</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entry in todayLeaderboard" :key="entry.rank">
                <td>
                  <span class="rank" :class="{ 'rank-top': entry.rank <= 3 }">
                    #{{ entry.rank }}
                  </span>
                </td>
                <td>{{ entry.username }}</td>
                <td>
                  <span v-if="entry.solved" class="result-solved">
                    {{ entry.attempts }}/6
                  </span>
                  <span v-else class="result-failed">X/6</span>
                </td>
                <td class="time-cell">{{ formatTime(entry.time_seconds) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.charts-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.distribution-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.distribution-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.distribution-label {
  width: 20px;
  text-align: center;
  font-weight: 600;
  color: var(--text-secondary);
}

.distribution-bar-container {
  flex: 1;
  height: 24px;
  background: var(--bg-primary);
  border-radius: 4px;
  overflow: hidden;
}

.distribution-bar {
  height: 100%;
  background: var(--correct);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
  min-width: 40px;
  transition: width 0.3s ease;
}

.distribution-count {
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.stat-value.word-display {
  font-size: 20px;
}

.empty-state {
  text-align: center;
  padding: 24px;
  color: var(--text-secondary);
}

.rank {
  font-weight: 600;
}

.rank-top {
  color: var(--present);
}

.result-solved {
  color: var(--correct);
  font-weight: 600;
}

.result-failed {
  color: var(--error);
  font-weight: 600;
}

.time-cell {
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  font-size: 13px;
  color: var(--text-secondary);
}
</style>
