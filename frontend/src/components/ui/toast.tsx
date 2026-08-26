import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from 'lucide-react'
import { Toast as ToastPrimitive } from 'radix-ui'

import { cn } from '@/lib/utils'

const ToastProvider = ToastPrimitive.Provider

function ToastViewport({ className, ...props }: React.ComponentProps<typeof ToastPrimitive.Viewport>) {
  return (
    <ToastPrimitive.Viewport
      data-slot="toast-viewport"
      className={cn(
        'fixed right-0 bottom-0 z-100 flex w-full max-w-[380px] flex-col gap-2 p-4 outline-none sm:right-4 sm:bottom-4',
        className
      )}
      {...props}
    />
  )
}

const toastVariants = cva(
  'group/toast relative flex w-full items-start gap-2.5 overflow-hidden rounded-lg border-l-2 bg-card p-3.5 shadow-lg data-[state=open]:animate-toast-in data-[state=closed]:animate-toast-out',
  {
    variants: {
      variant: {
        default: 'border-l-border',
        success: 'border-l-success bg-success/10',
        warning: 'border-l-warning bg-warning/10',
        destructive: 'border-l-destructive bg-destructive/10',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

const ICONS = {
  default: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  destructive: XCircle,
} as const

const ICON_COLOR = {
  default: 'text-muted-foreground',
  success: 'text-success',
  warning: 'text-warning',
  destructive: 'text-destructive',
} as const

function Toast({
  className,
  variant = 'default',
  ...props
}: React.ComponentProps<typeof ToastPrimitive.Root> & VariantProps<typeof toastVariants>) {
  const Icon = ICONS[variant ?? 'default']
  return (
    <ToastPrimitive.Root
      data-slot="toast"
      data-variant={variant}
      className={cn(toastVariants({ variant }), className)}
      {...props}
    >
      <Icon className={cn('mt-0.5 size-4 shrink-0', ICON_COLOR[variant ?? 'default'])} />
      <div className="flex min-w-0 flex-1 flex-col gap-0.5">{props.children}</div>
    </ToastPrimitive.Root>
  )
}

function ToastTitle({ className, variant, ...props }: React.ComponentProps<'div'> & VariantProps<typeof toastVariants>) {
  return (
    <ToastPrimitive.Title
      data-slot="toast-title"
      className={cn('text-sm font-medium', variant && variant !== 'default' && ICON_COLOR[variant], className)}
      {...props}
    />
  )
}

function ToastDescription({ className, ...props }: React.ComponentProps<typeof ToastPrimitive.Description>) {
  return (
    <ToastPrimitive.Description
      data-slot="toast-description"
      className={cn('text-xs text-muted-foreground', className)}
      {...props}
    />
  )
}

function ToastClose({ className, ...props }: React.ComponentProps<typeof ToastPrimitive.Close>) {
  return (
    <ToastPrimitive.Close
      data-slot="toast-close"
      aria-label="Cerrar"
      className={cn(
        'absolute top-2.5 right-2.5 cursor-pointer rounded-md p-0.5 text-muted-foreground/70 opacity-0 outline-none transition-opacity hover:text-foreground focus-visible:opacity-100 focus-visible:ring-2 focus-visible:ring-ring/50 group-hover/toast:opacity-100',
        className
      )}
      {...props}
    >
      <X className="size-3.5" />
    </ToastPrimitive.Close>
  )
}

export { Toast, ToastClose, ToastDescription, ToastProvider, ToastTitle, ToastViewport }
