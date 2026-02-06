/**
 * useConfirmDialog Hook
 * Feature: 010-magic-dj-controller
 *
 * Promise-based confirmation dialog hook replacing window.confirm().
 * Returns dialog props to be spread on ConfirmDialog component.
 */

import { useCallback, useState } from 'react'

interface ConfirmOptions {
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
}

export function useConfirmDialog() {
  const [state, setState] = useState<(ConfirmOptions & { resolve: (value: boolean) => void }) | null>(null)

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise<boolean>((resolve) => {
      setState({ ...options, resolve })
    })
  }, [])

  const handleConfirm = useCallback(() => {
    state?.resolve(true)
    setState(null)
  }, [state])

  const handleCancel = useCallback(() => {
    state?.resolve(false)
    setState(null)
  }, [state])

  const dialogProps = state
    ? {
        open: true,
        title: state.title,
        message: state.message,
        confirmLabel: state.confirmLabel,
        cancelLabel: state.cancelLabel,
        onConfirm: handleConfirm,
        onCancel: handleCancel,
      }
    : {
        open: false,
        title: '',
        message: '',
        onConfirm: handleConfirm,
        onCancel: handleCancel,
      }

  return { confirm, dialogProps }
}
