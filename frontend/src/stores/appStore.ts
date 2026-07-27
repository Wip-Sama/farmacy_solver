import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useWebSocket } from '@vueuse/core'
import { toast } from 'vue-sonner'

export interface CustomFestivity {
  name: string
  date: string
}

export interface PharmacyPreference {
  pharmacy_id: number
  date: string
  state: string
}

export interface Pharmacy {
  id: number
  name: string
  location: string
}

export interface Settings {
  year: number
  use_previous_year: boolean
  first_day_of_week: string
  auto_festivities: boolean
  time_limit: number
  regenerate_from: string | null
  pharmacies: Pharmacy[]
  custom_festivities: CustomFestivity[]
  pharmacy_preferences: PharmacyPreference[]
}

export interface ScheduleRow {
  week: number
  date: string
  festivity: string | null
  pharmacies: Array<{ id: number; name: string; location: string }>
  status: 'past' | 'current' | 'future'
  is_summer?: boolean
}

const getApiBase = () => {
  if (typeof window !== 'undefined' && window.location) {
    if (window.location.port === '5173' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
      return `${window.location.protocol}//${window.location.hostname}:8001/api`
    }
    return `${window.location.origin}/api`
  }
  return 'http://127.0.0.1:8001/api'
}

const getWsUrl = () => {
  if (typeof window !== 'undefined' && window.location) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = (window.location.port === '5173' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
      ? `${window.location.hostname}:8001`
      : window.location.host
    return `${protocol}//${host}/api/ws`
  }
  return 'ws://127.0.0.1:8001/api/ws'
}

export const API_BASE = getApiBase()
export const WS_URL = getWsUrl()

export const useAppStore = defineStore('app', () => {
  const settings = ref<Settings>({
    year: 2026,
    use_previous_year: true,
    first_day_of_week: 'monday',
    auto_festivities: true,
    time_limit: 55,
    regenerate_from: null,
    pharmacies: [
      { id: 1, name: 'MONTORO', location: 'centro' },
      { id: 2, name: 'BUCCARELLI', location: 'centro' },
      { id: 3, name: 'CENTRALE', location: 'centro' },
      { id: 4, name: 'DE PINO', location: 'centro' },
      { id: 5, name: 'DAVID', location: 'centro' },
      { id: 6, name: 'SAN MICHELE', location: 'centro' },
      { id: 7, name: 'MARCELLINI', location: 'marina' },
      { id: 8, name: 'PHARMADUO', location: 'marina' },
      { id: 9, name: 'IORFIDA', location: 'marina' },
      { id: 10, name: 'SAN LEONARDO', location: 'marina' }
    ],
    custom_festivities: [],
    pharmacy_preferences: []
  })

  const activeTab = ref<'schedules' | 'settings'>('schedules')
  const viewMode = ref<'compact' | 'extended'>('compact')
  const scheduleRows = ref<ScheduleRow[]>([])
  const availableYears = ref<number[]>([2025, 2026])
  const isJobRunning = ref(false)
  const isProgressModalOpen = ref(false)
  const isSettingsOpen = ref(false)
  const isGenerateOpen = ref(false)
  const isRescheduleOpen = ref(false)
  const isExportOpen = ref(false)
  const jobProgressLines = ref<string[]>([])

  // Connect WebSocket for zero-polling real-time multi-tab synchronization
  const { status: wsStatus } = useWebSocket(WS_URL, {
    autoReconnect: true,
    onMessage(_, event) {
      try {
        const data = JSON.parse(event.data)
        handleWSEvent(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
  })

  function handleWSEvent(event: { type: string; payload: any }) {
    console.log('[WS Event]:', event.type, event.payload)

    if (event.type === 'SETTINGS_UPDATED') {
      settings.value = { ...settings.value, ...event.payload }
    } else if (event.type === 'JOB_STARTED') {
      isJobRunning.value = true
      isProgressModalOpen.value = true
      jobProgressLines.value = [event.payload.message || 'Starting ASP solver job...']
      toast.info(`⚡ Generating schedule for ${event.payload.year}...`, {
        duration: Infinity,
        id: 'schedule-generating',
        action: {
          label: 'Cancel',
          onClick: () => cancelJob()
        }
      })
    } else if (event.type === 'JOB_PROGRESS') {
      if (event.payload.line) {
        jobProgressLines.value.push(event.payload.line)
      }
    } else if (event.type === 'JOB_COMPLETED') {
      isJobRunning.value = false
      toast.dismiss('schedule-generating')
      toast.success(`✅ Schedule for ${event.payload.year} generated successfully!`, {
        description: `Completed in ${event.payload.execution_time_seconds}s`
      })
      fetchAvailableYears()
      fetchScheduleRows(settings.value.year)
    } else if (event.type === 'JOB_FAILED') {
      isJobRunning.value = false
      toast.dismiss('schedule-generating')
      toast.error(`❌ Scheduling failed for ${event.payload.year}`, {
        description: event.payload.error
      })
    }
  }

  async function cancelJob() {
    try {
      const res = await fetch(`${API_BASE}/schedules/cancel`, { method: 'POST' })
      if (res.ok) {
        toast.dismiss('schedule-generating')
        toast.info('Job cancellation requested...')
      } else {
        toast.error('Failed to cancel job.')
      }
    } catch (e) {
      toast.error('Network error cancelling job.')
    }
  }

  // REST API Actions
  async function fetchSettings() {
    try {
      const res = await fetch(`${API_BASE}/settings`)
      if (res.ok) {
        settings.value = await res.json()
      }
    } catch (e) {
      console.warn('Failed to fetch settings from API, using local defaults:', e)
    }
  }

  async function fetchAvailableYears() {
    try {
      const res = await fetch(`${API_BASE}/schedules`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) {
          const years = Array.from(new Set(data.map((item: any) => item.year))).sort((a: any, b: any) => a - b) as number[]
          if (years.length > 0) {
            availableYears.value = years
          }
        }
      }
    } catch (e) {
      console.warn('Failed to fetch available schedule years:', e)
    }
  }

  async function updateSettings(newSettings: Partial<Settings>) {
    settings.value = { ...settings.value, ...newSettings }
    try {
      await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings.value)
      })
    } catch (e) {
      console.error('Failed to save settings:', e)
    }
  }

  async function saveCurrentSettings() {
    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings.value)
      })
      if (res.ok) {
        toast.success('Settings saved successfully!')
      } else {
        toast.error('Failed to save settings to server.')
      }
    } catch (e) {
      toast.error('Network error saving settings.')
    }
  }

  async function fetchScheduleRows(year: number) {
    try {
      const res = await fetch(`${API_BASE}/schedules/${year}?mode=${viewMode.value}`)
      if (res.ok) {
        scheduleRows.value = await res.json()
      }
    } catch (e) {
      console.warn(`Failed to fetch schedules for ${year}:`, e)
    }
  }

  async function triggerGenerate(payload?: Record<string, any>) {
    if (isJobRunning.value) return

    const bodyData = {
      year: settings.value.year,
      time_limit: settings.value.time_limit,
      auto_festivities: settings.value.auto_festivities,
      use_previous_year: settings.value.use_previous_year,
      first_day_of_week: settings.value.first_day_of_week,
      ...payload
    }


    try {
      const res = await fetch(`${API_BASE}/schedules/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyData)
      })

      if (res.status === 400) {
        const err = await res.json()
        toast.error('Validation Error: ' + (err.detail || 'Invalid parameters'))
        return
      }

      if (res.status === 409) {
        toast.warning('⚠️ A scheduling job is already running in another tab.')
        return
      }

      if (!res.ok) {
        const err = await res.json()
        toast.error('Failed to start schedule generation: ' + (err.detail || 'Unknown error'))
      }
    } catch (e) {
      toast.error('Network error triggering schedule generation.')
    }
  }

  return {
    settings,
    activeTab,
    viewMode,
    scheduleRows,
    availableYears,
    isJobRunning,
    isProgressModalOpen,
    isSettingsOpen,
    isGenerateOpen,
    isRescheduleOpen,
    isExportOpen,
    jobProgressLines,
    wsStatus,
    fetchSettings,
    fetchAvailableYears,
    updateSettings,
    saveCurrentSettings,
    fetchScheduleRows,
    triggerGenerate
  }
})
