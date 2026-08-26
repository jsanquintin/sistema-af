import { useEffect, useState } from 'react'

export type ToastVariant = 'default' | 'success' | 'warning' | 'destructive'

export interface ToastItem {
  id: string
  title: string
  description?: string
  variant: ToastVariant
}

const DURATION_MS = 5000

let toasts: ToastItem[] = []
let listeners: ((toasts: ToastItem[]) => void)[] = []

function emit() {
  listeners.forEach((listener) => listener(toasts))
}

export function dismissToast(id: string) {
  toasts = toasts.filter((t) => t.id !== id)
  emit()
}

export function toast({ title, description, variant = 'default' }: Omit<ToastItem, 'id'>) {
  const id = crypto.randomUUID()
  toasts = [...toasts, { id, title, description, variant }]
  emit()
  setTimeout(() => dismissToast(id), DURATION_MS)
  return id
}

export function useToast() {
  const [state, setState] = useState<ToastItem[]>(toasts)

  useEffect(() => {
    listeners.push(setState)
    return () => {
      listeners = listeners.filter((listener) => listener !== setState)
    }
  }, [])

  return { toasts: state, dismiss: dismissToast }
}
