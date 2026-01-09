<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getWords, updateWord, type Word } from '../api'

const words = ref<Word[]>([])
const total = ref(0)
const isLoading = ref(true)

// Filters
const currentYear = new Date().getFullYear()
const selectedYear = ref<number | null>(currentYear)
const selectedMonth = ref<number | null>(null)
const offset = ref(0)
const limit = 30

// Edit Modal
const showModal = ref(false)
const editingDate = ref('')
const editingWord = ref('')
const editingDifficulty = ref(5)
const editStatus = ref<{ type: 'success' | 'error'; message: string } | null>(null)
const isSaving = ref(false)
const isNewWord = ref(false)

const today = computed(() => new Date().toISOString().split('T')[0])

async function loadWords() {
  isLoading.value = true
  try {
    const data = await getWords({
      year: selectedYear.value || undefined,
      month: selectedMonth.value || undefined,
      limit,
      offset: offset.value,
    })
    words.value = data.words
    total.value = data.total
  } catch (e) {
    console.error('Failed to load words', e)
  }
  isLoading.value = false
}

function getDateBadgeClass(date: string): string {
  if (date === today.value) return 'badge-today'
  if (date > today.value) return 'badge-future'
  return 'badge-past'
}

function openEdit(word: Word) {
  editingDate.value = word.date
  editingWord.value = word.word
  editingDifficulty.value = word.difficulty_rank
  editStatus.value = null
  isNewWord.value = false
  showModal.value = true
}

function openNew() {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  editingDate.value = tomorrow.toISOString().split('T')[0]
  editingWord.value = ''
  editingDifficulty.value = 5
  editStatus.value = null
  isNewWord.value = true
  showModal.value = true
}

async function save() {
  const word = editingWord.value.toUpperCase().trim()

  if (word.length !== 5) {
    editStatus.value = { type: 'error', message: 'Word must be exactly 5 letters' }
    return
  }

  if (!/^[A-Z]+$/.test(word)) {
    editStatus.value = { type: 'error', message: 'Word must contain only letters' }
    return
  }

  isSaving.value = true
  try {
    const result = await updateWord(editingDate.value, word, editingDifficulty.value)
    editStatus.value = {
      type: 'success',
      message: result.created ? 'Word created!' : 'Word updated!'
    }
    setTimeout(() => {
      showModal.value = false
      loadWords()
    }, 500)
  } catch (e: any) {
    editStatus.value = { type: 'error', message: e.message }
  }
  isSaving.value = false
}

function prevPage() {
  offset.value = Math.max(0, offset.value - limit)
  loadWords()
}

function nextPage() {
  offset.value += limit
  loadWords()
}

function applyFilter() {
  offset.value = 0
  loadWords()
}

onMounted(loadWords)
</script>

<template>
  <div>
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Word Management</h3>
        <button class="btn btn-primary" @click="openNew">+ Add Word</button>
      </div>

      <!-- Filters -->
      <div class="form-row mb-4">
        <div class="form-group" style="width: 120px;">
          <label class="form-label">Year</label>
          <select v-model="selectedYear" class="form-select" @change="applyFilter">
            <option :value="null">All</option>
            <option v-for="y in [currentYear - 1, currentYear, currentYear + 1]" :key="y" :value="y">
              {{ y }}
            </option>
          </select>
        </div>
        <div class="form-group" style="width: 120px;">
          <label class="form-label">Month</label>
          <select v-model="selectedMonth" class="form-select" @change="applyFilter">
            <option :value="null">All</option>
            <option v-for="m in 12" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="loading">
        <div class="spinner"></div>
      </div>

      <!-- Table -->
      <template v-else>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Word</th>
              <th>Difficulty</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="word in words" :key="word.id">
              <td>
                <span class="badge" :class="getDateBadgeClass(word.date)">
                  {{ word.date }}
                </span>
              </td>
              <td><span class="word-display">{{ word.word }}</span></td>
              <td>{{ word.difficulty_rank }}</td>
              <td>
                <button class="btn btn-secondary btn-sm" @click="openEdit(word)">Edit</button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div class="pagination">
          <span class="pagination-info">
            Showing {{ offset + 1 }}-{{ Math.min(offset + limit, total) }} of {{ total }}
          </span>
          <div class="pagination-buttons">
            <button class="btn btn-secondary btn-sm" :disabled="offset === 0" @click="prevPage">
              Previous
            </button>
            <button class="btn btn-secondary btn-sm" :disabled="offset + limit >= total" @click="nextPage">
              Next
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="modal-title">{{ isNewWord ? 'Add Word' : 'Edit Word' }}</h3>
        </div>

        <div class="form-group">
          <label class="form-label">Date</label>
          <input
            v-model="editingDate"
            type="date"
            class="form-input"
            :readonly="!isNewWord"
            :style="{ background: isNewWord ? '' : 'var(--bg-secondary)' }"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Word (5 letters)</label>
          <input
            v-model="editingWord"
            type="text"
            class="form-input word-input"
            maxlength="5"
            placeholder="HELLO"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Difficulty (1-10)</label>
          <input
            v-model.number="editingDifficulty"
            type="number"
            class="form-input"
            min="1"
            max="10"
            style="width: 100px;"
          />
        </div>

        <div v-if="editStatus" class="message" :class="`message-${editStatus.type}`">
          {{ editStatus.message }}
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showModal = false">Cancel</button>
          <button class="btn btn-primary" :disabled="isSaving" @click="save">
            {{ isSaving ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.word-input {
  text-transform: uppercase;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  font-size: 20px;
  letter-spacing: 4px;
  width: 140px;
}
</style>
