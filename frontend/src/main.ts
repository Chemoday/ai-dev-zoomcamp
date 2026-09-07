import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { router } from './router'
import { provideToken } from './api'
import { useAuthStore } from './stores/auth'
import './styles/nocturne.css'
import './styles/base.css'

const app = createApp(App)
app.use(createPinia())

// Hand the API client a token reader instead of importing the store there.
provideToken(() => useAuthStore().token)

app.use(router)
app.mount('#app')
