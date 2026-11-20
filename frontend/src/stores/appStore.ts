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

const getWsUrl = () => {
  if (typeof window !== 'undefined' && window.location) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/api/ws`
  }
  return 'ws://127.0.0.1:8001/api/ws'
}

export const API_BASE = '/api'
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
      { id: 10, name: 'SAN LEONARDO', location: 'marina' },
    ],
    custom_festivities: [],
    pharmacy_preferences: [],
  })

  const viewMode = ref<'compact' | 'extended'>('compact')
  const scheduleRows = ref<ScheduleRow[]>([])
  const availableYears = ref<number[]>([2025, 2026])
  const isJobRunning = ref(false)
  const runningJobYear = ref<number | null>(null)
  const isSettingsOpen = ref(false)
  const isGenerateOpen = ref(false)
  const isRescheduleOpen = ref(false)
  const isExportOpen = ref(false)

  useWebSocket(WS_URL, {
    autoReconnect: true,
    onMessage(_, event) {
      try {
        const data = JSON.parse(event.data)
        handleWSEvent(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    },
  })

  function handleWSEvent(event: { type: string; payload: any }) {
    if (event.type === 'SETTINGS_UPDATED') {
      settings.value = { ...settings.value, ...event.payload }
    } else if (event.type === 'JOB_STARTED') {
      isJobRunning.value = true
      runningJobYear.value = event.payload?.year ?? settings.value.year
      toast.info(`Generating schedule for ${runningJobYear.value}...`, {
        duration: Infinity,
        id: 'schedule-generating',
        action: {
          label: 'Cancel',
          onClick: () => cancelJob(),
        },
      })
    } else if (event.type === 'JOB_COMPLETED') {
      isJobRunning.value = false
      runningJobYear.value = null
      toast.dismiss('schedule-generating')
      toast.success(`Schedule for ${event.payload.year} generated!`, {
        description: `Completed in ${event.payload.execution_time_seconds}s`,
      })
      if (event.payload?.year) {
        settings.value.year = event.payload.year
      }
      fetchAvailableYears()
      fetchScheduleRows(settings.value.year)
    } else if (event.type === 'JOB_FAILED') {
      isJobRunning.value = false
      runningJobYear.value = null
      toast.dismiss('schedule-generating')
      toast.error(`Scheduling stopped for ${event.payload.year}`, {
        description: event.payload.error,
      })
    }
  }

  async function cancelJob() {
    try {
      const res = await fetch(`${API_BASE}/schedules/cancel`, { method: 'POST' })
      if (res.ok) {
        toast.dismiss('schedule-generating')
        toast.info('Schedule generation cancelled.')
      } else {
        toast.error('Failed to cancel job.')
      }
    } catch {
      toast.error('Network error cancelling job.')
    }
  }

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
          const years = Array.from(new Set(data.map((item: any) => item.year))).sort(
            (a: any, b: any) => a - b
          ) as number[]
          if (years.length > 0) {
            availableYears.value = years
          }
        }
      }
    } catch (e) {
      console.warn('Failed to fetch available schedule years:', e)
    }
  }

  async function updateSettings(newSettings: Partial<Settings>, showToast = false): Promise<boolean> {
    settings.value = { ...settings.value, ...newSettings }
    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings.value),
      })
      if (res.ok) {
        if (showToast) toast.success('Settings saved successfully!')
        return true
      }
      if (showToast) toast.error('Failed to save settings to server.')
      return false
    } catch (e) {
      console.error('Failed to save settings:', e)
      if (showToast) toast.error('Network error saving settings.')
      return false
    }
  }

  async function fetchScheduleRows(year: number) {
    try {
      const res = await fetch(`${API_BASE}/schedules/${year}`)
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
      ...payload,
    }

    try {
      const res = await fetch(`${API_BASE}/schedules/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyData),
      })

      if (res.status === 400) {
        const err = await res.json()
        toast.error('Validation Error: ' + (err.detail || 'Invalid parameters'))
        return
      }

      if (res.status === 409) {
        toast.warning('A scheduling job is already running.')
        return
      }

      if (!res.ok) {
        const err = await res.json()
        toast.error('Failed to start schedule generation: ' + (err.detail || 'Unknown error'))
      }
    } catch {
      toast.error('Network error triggering schedule generation.')
    }
  }

  return {
    settings,
    viewMode,
    scheduleRows,
    availableYears,
    isJobRunning,
    runningJobYear,
    isSettingsOpen,
    isGenerateOpen,
    isRescheduleOpen,
    isExportOpen,
    fetchSettings,
    fetchAvailableYears,
    updateSettings,
    fetchScheduleRows,
    triggerGenerate,
    cancelJob,
  }
})
