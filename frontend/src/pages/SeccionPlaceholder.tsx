interface SeccionPlaceholderProps {
  titulo: string
  descripcion: string
}

export function SeccionPlaceholder({ titulo, descripcion }: SeccionPlaceholderProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border text-center">
      <h1 className="text-base font-semibold">{titulo}</h1>
      <p className="max-w-sm text-sm text-muted-foreground">{descripcion}</p>
    </div>
  )
}
