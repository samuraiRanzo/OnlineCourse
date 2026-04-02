import {createApp} from 'vue'
import {createPinia} from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import 'primeicons/primeicons.css'
import {createI18n} from 'vue-i18n'
import mn from './locales/mn.json'
import en from './locales/en.json'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const messages = {en, mn};
const app = createApp(App)
const i18n = createI18n({
    locale: 'mn',
    fallbackLocale: 'mn',
    messages: messages,
    legacy: false,
    globalInjection: true,
})
app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            darkModeSelector: '.dark',
        },
    },
})
app.use(ToastService)
app.use(ConfirmationService)

app.mount('#app')
