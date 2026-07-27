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
}

const API_BASE = 'http://127.0.0.1:8000/api'
const WS_URL = 'ws://127.0.0.1:8000/api/ws'

export const useAppStore = defineStore('app', () => {
  const settings = ref<Settings>({
    year: 2026,
    use_previous_year: true,
    first_day_of_week: 'sunday',
    auto_festivities: true,
    time_limit: 60,
    regenerate_from: null,
    pharmacies: [
      { id: 1, name: 'qualcosa', location: 'centro' },
      { id: 2, name: 'qualcos\'altro', location: 'centro' },
      { id: 3, name: 'niente', location: 'marina' }
    ],
    custom_festivities: [
      { name: 'Natale', date: '2026-12-25' },
      { name: 'Pasqua', date: '2026-04-05' },
      { name: 'Capodanno', date: '2026-01-01' },
    ],
    pharmacy_preferences: [
      { pharmacy_id: 1, date: '2026-12-25', state: 'Closed' },
      { pharmacy_id: 2, date: '2026-12-25', state: 'Closed' },
      { pharmacy_id: 3, date: '2026-12-25', state: 'Closed' },
    ]
  })

  const activeTab = ref<'schedules' | 'settings'>('schedules')
  const viewMode = ref<'compact' | 'extended'>('compact')
  const scheduleRows = ref<ScheduleRow[]>([])
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
        duration: 100000,
        id: 'schedule-generating'
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
      fetchScheduleRows(settings.value.year)
    } else if (event.type === 'JOB_FAILED') {
      isJobRunning.value = false
      toast.dismiss('schedule-generating')
      toast.error(`❌ Scheduling failed for ${event.payload.year}`, {
        description: event.payload.error
      })
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

  async function triggerGenerate() {
    if (isJobRunning.value) return

    try {
      const res = await fetch(`${API_BASE}/schedules/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          year: settings.value.year,
          time_limit: settings.value.time_limit,
          auto_festivities: settings.value.auto_festivities
        })
      })

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
    isJobRunning,
    isProgressModalOpen,
    isSettingsOpen,
    isGenerateOpen,
    isRescheduleOpen,
    isExportOpen,
    jobProgressLines,
    wsStatus,
    fetchSettings,
    updateSettings,
    fetchScheduleRows,
    triggerGenerate
  }
})
