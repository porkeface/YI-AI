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
const MAX_NOTIFICATIONS = 5

export function useNotification() {
  function show(
    type: Notification['type'],
    title: string,
    message: string,
    duration = 3000
  ) {
    // 去重：相同 type+title+message 的通知不重复弹出
    const exists = notifications.value.find(
      n => n.type === type && n.title === title && n.message === message
    )
    if (exists) {
      return exists.id
    }

    const id = nextId++
    const notification: Notification = {
      id,
      type,
      title,
      message,
      duration,
    }

    // 限制最大数量，超出时移除最早的通知
    const updated = [...notifications.value, notification]
    if (updated.length > MAX_NOTIFICATIONS) {
      updated.splice(0, updated.length - MAX_NOTIFICATIONS)
    }
    notifications.value = updated

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
    notifications.value = notifications.value.filter(n => n.id !== id)
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
