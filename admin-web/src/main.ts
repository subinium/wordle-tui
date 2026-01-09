import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory('/admin/'),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('./views/Dashboard.vue'),
    },
    {
      path: '/words',
      name: 'words',
      component: () => import('./views/Words.vue'),
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('./views/Users.vue'),
    },
    {
      path: '/leaderboard',
      name: 'leaderboard',
      component: () => import('./views/Leaderboard.vue'),
    },
  ],
})

// Auth guard
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('adminToken')
  if (!token && to.name !== 'dashboard') {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

createApp(App).use(router).mount('#app')
