const API_BASE = import.meta.env.DEV ? '' : window.location.origin

export function getToken(): string | null {
  return localStorage.getItem('adminToken')
}

export function setToken(token: string): void {
  localStorage.setItem('adminToken', token)
}

export function clearToken(): void {
  localStorage.removeItem('adminToken')
}

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// Auth
export async function getGoogleAuthUrl(redirectUri: string) {
  return fetchAPI<{ auth_url: string; state: string }>(
    `/auth/google/auth-url?redirect_uri=${encodeURIComponent(redirectUri)}`
  )
}

export async function googleCallback(code: string, state: string, redirectUri: string) {
  return fetchAPI<{ success: boolean; token?: string; error?: string }>(
    '/auth/google/callback',
    {
      method: 'POST',
      body: JSON.stringify({ code, state, redirect_uri: redirectUri }),
    }
  )
}

export async function getAdminMe() {
  return fetchAPI<{
    id: number
    username: string
    email: string
    avatar_url: string | null
  }>('/admin/me')
}

// Stats
export async function getStats() {
  return fetchAPI<{
    total_users: number
    total_games: number
    total_solved: number
    solve_rate: number
    avg_attempts: number
    active_users_7d: number
    today: {
      date: string
      word: string | null
      games: number
      solved: number
    }
  }>('/admin/stats')
}

export async function getDailyStats(date: string) {
  return fetchAPI<{
    date: string
    word: string | null
    total_games: number
    total_solved: number
    solve_rate: number
    avg_attempts: number
    distribution: Record<string, number>
  }>(`/admin/daily/${date}`)
}

// Words
export interface Word {
  id: number
  date: string
  word: string
  difficulty_rank: number
}

export async function getWords(params: { year?: number; month?: number; limit?: number; offset?: number }) {
  const query = new URLSearchParams()
  if (params.year) query.set('year', String(params.year))
  if (params.month) query.set('month', String(params.month))
  if (params.limit) query.set('limit', String(params.limit))
  if (params.offset) query.set('offset', String(params.offset))

  return fetchAPI<{
    words: Word[]
    total: number
    limit: number
    offset: number
  }>(`/admin/words?${query}`)
}

export async function updateWord(date: string, word: string, difficulty?: number) {
  const query = new URLSearchParams({ word })
  if (difficulty !== undefined) query.set('difficulty_rank', String(difficulty))

  return fetchAPI<Word & { created?: boolean; updated?: boolean }>(
    `/admin/words/${date}?${query}`,
    { method: 'PUT' }
  )
}

// Users
export interface User {
  id: number
  username: string
  email: string | null
  google_id: string | null
  created_at: string | null
  total_games: number
  total_wins: number
  current_streak: number
  longest_streak: number
}

export async function getUsers(params: { limit?: number; offset?: number }) {
  const query = new URLSearchParams()
  if (params.limit) query.set('limit', String(params.limit))
  if (params.offset) query.set('offset', String(params.offset))

  return fetchAPI<{
    users: User[]
    limit: number
    offset: number
  }>(`/admin/users?${query}`)
}

// Leaderboard (All-time)
export interface LeaderboardEntry {
  rank: number
  username: string
  current_streak: number
  longest_streak: number
  total_games: number
  total_wins: number
  win_rate: number
}

export async function getLeaderboard(limit = 50) {
  return fetchAPI<{ leaderboard: LeaderboardEntry[] }>(`/admin/leaderboard?limit=${limit}`)
}

// Today's Leaderboard
export interface TodayLeaderboardEntry {
  rank: number
  username: string
  solved: boolean
  attempts: number
  time_seconds: number | null
  completed_at: string | null
}

export async function getTodayLeaderboard(limit = 20) {
  return fetchAPI<{
    leaderboard: TodayLeaderboardEntry[]
    date: string
    word: string | null
  }>(`/admin/leaderboard/today?limit=${limit}`)
}
