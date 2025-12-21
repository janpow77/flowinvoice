import { useState, useRef, useCallback, useEffect } from 'react'
import {
  PanelLeft,
  PanelRight,
  GripVertical,
  Maximize2,
} from 'lucide-react'
import clsx from 'clsx'

interface DocumentSplitViewProps {
  leftPanel: React.ReactNode
  rightPanel: React.ReactNode
  defaultLeftWidth?: number
  minLeftWidth?: number
  maxLeftWidth?: number
  className?: string
}

export default function DocumentSplitView({
  leftPanel,
  rightPanel,
  defaultLeftWidth = 50,
  minLeftWidth = 25,
  maxLeftWidth = 75,
  className,
}: DocumentSplitViewProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth)
  const [isDragging, setIsDragging] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState<'left' | 'right' | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return

      const container = containerRef.current
      const containerRect = container.getBoundingClientRect()
      const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100

      // Clamp the width within bounds
      const clampedWidth = Math.max(minLeftWidth, Math.min(maxLeftWidth, newLeftWidth))
      setLeftWidth(clampedWidth)
    },
    [isDragging, minLeftWidth, maxLeftWidth]
  )

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  const toggleCollapse = (side: 'left' | 'right') => {
    if (isCollapsed === side) {
      setIsCollapsed(null)
    } else {
      setIsCollapsed(side)
    }
  }

  // Calculate actual widths based on collapse state
  const actualLeftWidth = isCollapsed === 'left' ? 0 : isCollapsed === 'right' ? 100 : leftWidth
  const actualRightWidth = 100 - actualLeftWidth

  return (
    <div
      ref={containerRef}
      className={clsx(
        'flex h-full overflow-hidden bg-theme-bg rounded-lg border border-theme-border',
        className
      )}
    >
      {/* Left Panel */}
      <div
        className={clsx(
          'relative overflow-hidden transition-all duration-200',
          isCollapsed === 'left' && 'w-0'
        )}
        style={{ width: isCollapsed === 'left' ? 0 : `${actualLeftWidth}%` }}
      >
        {/* Collapse button for left panel */}
        <button
          onClick={() => toggleCollapse('left')}
          className="absolute top-2 left-2 z-10 p-1.5 bg-theme-surface border border-theme-border rounded-lg text-theme-text-muted hover:text-theme-text transition-colors"
          title={isCollapsed === 'left' ? 'PDF anzeigen' : 'PDF ausblenden'}
        >
          {isCollapsed === 'left' ? (
            <Maximize2 className="w-4 h-4" />
          ) : (
            <PanelLeft className="w-4 h-4" />
          )}
        </button>

        <div className="h-full overflow-auto">{leftPanel}</div>
      </div>

      {/* Resizer */}
      {!isCollapsed && (
        <div
          onMouseDown={handleMouseDown}
          className={clsx(
            'flex-shrink-0 w-2 cursor-col-resize flex items-center justify-center',
            'bg-theme-border hover:bg-theme-primary/50 transition-colors',
            isDragging && 'bg-theme-primary'
          )}
        >
          <GripVertical className="w-3 h-3 text-theme-text-muted" />
        </div>
      )}

      {/* Right Panel */}
      <div
        className={clsx(
          'relative overflow-hidden transition-all duration-200',
          isCollapsed === 'right' && 'w-0'
        )}
        style={{ width: isCollapsed === 'right' ? 0 : `${actualRightWidth}%` }}
      >
        {/* Collapse button for right panel */}
        <button
          onClick={() => toggleCollapse('right')}
          className="absolute top-2 right-2 z-10 p-1.5 bg-theme-surface border border-theme-border rounded-lg text-theme-text-muted hover:text-theme-text transition-colors"
          title={isCollapsed === 'right' ? 'Details anzeigen' : 'Details ausblenden'}
        >
          {isCollapsed === 'right' ? (
            <Maximize2 className="w-4 h-4" />
          ) : (
            <PanelRight className="w-4 h-4" />
          )}
        </button>

        <div className="h-full overflow-auto">{rightPanel}</div>
      </div>

      {/* Show collapsed indicator */}
      {isCollapsed === 'left' && (
        <button
          onClick={() => setIsCollapsed(null)}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 p-2 bg-theme-surface border border-theme-border rounded-r-lg text-theme-text-muted hover:text-theme-text transition-colors"
        >
          <PanelLeft className="w-4 h-4" />
        </button>
      )}

      {isCollapsed === 'right' && (
        <button
          onClick={() => setIsCollapsed(null)}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 p-2 bg-theme-surface border border-theme-border rounded-l-lg text-theme-text-muted hover:text-theme-text transition-colors"
        >
          <PanelRight className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}
