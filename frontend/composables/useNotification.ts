import { ref } from 'vue'

interface Notification {
  id: number
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
}

const notifications = ref<Notification[]>([])
let nextId = 0

export function useNotification() {
  function show(
    type: Notification['type'],
    title: string,
    message: string,
    duration = 3000
  ) {
    const id = nextId++
    const notification: Notification = {
      id,
      type,
      title,
      message,
      duration,
    }

    notifications.value.push(notification)

    return id
  }

  function success(title: string, message: string, duration?: number) {
    return show('success', title, message, duration)
  }

  function error(title: string, message: string, duration?: number) {
    return show('error', title, message, duration)
  }

  function warning(title: string, message: string, duration?: number) {
    return show('warning', title, message, duration)
  }

  function info(title: string, message: string, duration?: number) {
    return show('info', title, message, duration)
  }

  function remove(id: number) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }

  function clear() {
    notifications.value = []
  }

  return {
    notifications,
    show,
    success,
    error,
    warning,
    info,
    remove,
    clear,
  }
}
