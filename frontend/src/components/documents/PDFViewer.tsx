import { useState, useEffect } from 'react'
import {
  ZoomIn,
  ZoomOut,
  RotateCw,
  Download,
  Maximize2,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'

interface PDFViewerProps {
  documentId: string
  filename?: string
  className?: string
}

export default function PDFViewer({
  documentId,
  filename,
  className,
}: PDFViewerProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [scale, setScale] = useState(1.0)
  const [rotation, setRotation] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    // Load PDF blob and create object URL
    const loadPdf = async () => {
      setLoading(true)
      setError(null)
      try {
        const blob = await api.getDocumentFileBlob(documentId)
        const url = URL.createObjectURL(blob)
        setPdfUrl(url)
      } catch (err) {
        console.error('Failed to load PDF:', err)
        setError('PDF konnte nicht geladen werden')
      } finally {
        setLoading(false)
      }
    }

    loadPdf()

    return () => {
      // Cleanup object URL
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl)
      }
    }
  }, [documentId])

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 3.0))
  }

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, 0.5))
  }

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360)
  }

  const handleDownload = async () => {
    try {
      const blob = await api.getDocumentFileBlob(documentId)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || `document_${documentId}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  const handleFullscreen = () => {
    setIsFullscreen(prev => !prev)
  }

  if (loading) {
    return (
      <div className={clsx('flex items-center justify-center bg-theme-bg rounded-lg', className)}>
        <div className="text-center">
          <Loader2 className="w-8 h-8 mx-auto mb-2 text-theme-primary animate-spin" />
          <p className="text-sm text-theme-text-muted">PDF wird geladen...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={clsx('flex items-center justify-center bg-theme-bg rounded-lg', className)}>
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 text-status-danger" />
          <p className="text-sm text-status-danger">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div
      className={clsx(
        'flex flex-col bg-theme-bg rounded-lg overflow-hidden',
        isFullscreen && 'fixed inset-0 z-50',
        className
      )}
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-theme-surface border-b border-theme-border">
        <div className="flex items-center gap-2">
          {/* Zoom controls */}
          <button
            onClick={handleZoomOut}
            disabled={scale <= 0.5}
            className="p-1.5 text-theme-text-muted hover:text-theme-text disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Verkleinern"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-sm text-theme-text-muted w-12 text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            disabled={scale >= 3.0}
            className="p-1.5 text-theme-text-muted hover:text-theme-text disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Vergrößern"
          >
            <ZoomIn className="w-4 h-4" />
          </button>

          <div className="w-px h-4 bg-theme-border mx-2" />

          {/* Rotate */}
          <button
            onClick={handleRotate}
            className="p-1.5 text-theme-text-muted hover:text-theme-text transition-colors"
            title="Drehen"
          >
            <RotateCw className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-2">
          {/* Download */}
          <button
            onClick={handleDownload}
            className="p-1.5 text-theme-text-muted hover:text-theme-text transition-colors"
            title="Herunterladen"
          >
            <Download className="w-4 h-4" />
          </button>

          {/* Fullscreen */}
          <button
            onClick={handleFullscreen}
            className="p-1.5 text-theme-text-muted hover:text-theme-text transition-colors"
            title={isFullscreen ? 'Vollbild beenden' : 'Vollbild'}
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* PDF Container */}
      <div className="flex-1 overflow-auto p-4 bg-neutral-800">
        {pdfUrl && (
          <div
            className="mx-auto bg-white shadow-lg"
            style={{
              transform: `scale(${scale}) rotate(${rotation}deg)`,
              transformOrigin: 'top center',
              transition: 'transform 0.2s ease',
            }}
          >
            {/* Using iframe for PDF rendering - most compatible approach */}
            <iframe
              src={pdfUrl}
              className="w-full"
              style={{
                minHeight: '800px',
                border: 'none',
              }}
              title={filename || 'PDF Document'}
            />
          </div>
        )}
      </div>
    </div>
  )
}
