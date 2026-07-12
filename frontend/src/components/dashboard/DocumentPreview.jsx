import { useState, useEffect, useRef, useCallback } from 'react'
import { RefreshCw, Download, ZoomIn, ZoomOut, FileText, MousePointer } from 'lucide-react'
import { documentService } from '../../services/documentService'
import SelectionToolbar from './SelectionToolbar'
import './DocumentPreview.css'

const DocumentPreview = ({ document, refreshTrigger, onDownload, onSelectionCommand }) => {
  const [html, setHtml]                   = useState('')
  const [loading, setLoading]             = useState(false)
  const [zoom, setZoom]                   = useState(100)
  const [selectedTexts, setSelectedTexts] = useState([])
  const [toolbarPos, setToolbarPos]       = useState({ x: 0, y: 0 })
  const [showToolbar, setShowToolbar]     = useState(false)
  const [selectionMode, setSelectionMode] = useState(false)
  const [cmdLoading, setCmdLoading]       = useState(false)
  const iframeRef                         = useRef()
  const containerRef                      = useRef()

  const loadPreview = async () => {
    if (!document) return
    setLoading(true)
    try {
      const htmlContent = await documentService.getPreview(document.id)
      setHtml(htmlContent)
    } catch (err) {
      setHtml('<div style="padding:40px;color:#666;font-family:sans-serif;">Preview failed. Download the document to see changes.</div>')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPreview()
    setShowToolbar(false)
    setSelectedTexts([])
  }, [document?.id, refreshTrigger])

  // Inject selection listener into iframe after html loads
  useEffect(() => {
    if (!html || !iframeRef.current) return
    const iframe = iframeRef.current
    const handleLoad = () => {
      try {
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document
        if (!iframeDoc) return

        // Inject selection script into iframe
        const script = iframeDoc.createElement('script')
        script.textContent = `
          let selectedElements = [];
          let ctrlHeld = false;

          document.addEventListener('keydown', (e) => {
            if (e.key === 'Control' || e.key === 'Meta') ctrlHeld = true;
          });
          document.addEventListener('keyup', (e) => {
            if (e.key === 'Control' || e.key === 'Meta') ctrlHeld = false;
          });

          document.addEventListener('click', (e) => {
            const para = e.target.closest('p, h1, h2, h3, h4, h5, h6, li');
            if (!para) return;

            if (ctrlHeld) {
              // Multi-select with Ctrl
              if (para.classList.contains('texlify-selected')) {
                para.classList.remove('texlify-selected');
                selectedElements = selectedElements.filter(el => el !== para);
              } else {
                para.classList.add('texlify-selected');
                selectedElements.push(para);
              }
            } else {
              // Single select — clear previous
              document.querySelectorAll('.texlify-selected').forEach(el => {
                el.classList.remove('texlify-selected');
              });
              selectedElements = [];
              para.classList.add('texlify-selected');
              selectedElements = [para];
            }

            const texts = selectedElements.map(el => el.textContent.trim()).filter(Boolean);
            const rect  = para.getBoundingClientRect();
            window.parent.postMessage({
              type: 'texlify-selection',
              texts: texts,
              rect: {
                top:    rect.top,
                left:   rect.left,
                bottom: rect.bottom,
                right:  rect.right
              }
            }, '*');
          });

          // Inject selection styles
          const style = document.createElement('style');
          style.textContent = \`
            p, h1, h2, h3, h4, h5, h6, li {
              cursor: pointer;
              border-radius: 3px;
              transition: background 0.1s;
            }
            p:hover, h1:hover, h2:hover, h3:hover, h4:hover, h5:hover, h6:hover, li:hover {
              background: rgba(16, 185, 129, 0.06) !important;
              outline: 1px dashed rgba(16, 185, 129, 0.4);
            }
            .texlify-selected {
              background: rgba(16, 185, 129, 0.15) !important;
              outline: 2px solid rgba(16, 185, 129, 0.6) !important;
            }
          \`;
          document.head.appendChild(style);
        `
        iframeDoc.head.appendChild(script)
      } catch (e) {
        console.warn('Could not inject iframe script:', e)
      }
    }
    iframe.addEventListener('load', handleLoad)
    return () => iframe.removeEventListener('load', handleLoad)
  }, [html])

  // Listen for messages from iframe
  useEffect(() => {
    const handleMessage = (e) => {
      if (e.data?.type !== 'texlify-selection') return
      const { texts, rect } = e.data
      if (!texts || texts.length === 0) {
        setShowToolbar(false)
        setSelectedTexts([])
        return
      }
      setSelectedTexts(texts)

      // Position toolbar above selected element
      const container    = containerRef.current
      const containerRect = container?.getBoundingClientRect()
      if (!containerRect) return

      const iframe    = iframeRef.current
      const iframeRect = iframe?.getBoundingClientRect()
      if (!iframeRect) return

      const scale = zoom / 100
      const x = Math.min(
        iframeRect.left + rect.left * scale,
        window.innerWidth - 340
      )
      const y = Math.max(
        iframeRect.top + rect.top * scale - 10,
        10
      )

      setToolbarPos({ x, y })
      setShowToolbar(true)
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [zoom])

  // Close toolbar when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!e.target.closest('.selection-toolbar') &&
          !e.target.closest('iframe')) {
        setShowToolbar(false)
      }
    }
    window.document.addEventListener('click', handleClickOutside)
    return () => window.document.removeEventListener('click', handleClickOutside)
  }, [])

 const handleSelectionAction = async (action) => {
  if (!document || !onSelectionCommand) return
  setCmdLoading(true)
  try {
    if (action.type === 'custom_command') {
      // Custom text prompt — goes through AI
      await onSelectionCommand(document.id, action.command, null)
    } else {
      // Direct action — bypass AI, go straight to executor
      await onSelectionCommand(document.id, null, action.params)
    }
    setShowToolbar(false)
    setSelectedTexts([])
  } catch (e) {
    console.error('Selection command failed:', e)
  } finally {
    setCmdLoading(false)
  }
}

  if (!document) {
    return (
      <div className="preview-empty">
        <FileText size={48} />
        <h3>No document selected</h3>
        <p>Select a document to see a live preview here</p>
      </div>
    )
  }

  return (
    <div className="preview" ref={containerRef}>

      {/* Toolbar */}
      <div className="preview__toolbar">
        <div className="preview__toolbar-left">
          <div className="preview__doc-name">
            <FileText size={14} />
            <span>{document.title}</span>
          </div>
          <div
            className={`preview__selection-badge ${selectionMode ? 'preview__selection-badge--active' : ''}`}
            onClick={() => setSelectionMode(!selectionMode)}
            title="Click to toggle selection mode"
          >
            <MousePointer size={11} />
            {selectedTexts.length > 0
              ? `${selectedTexts.length} selected`
              : 'Click to select'}
          </div>
        </div>
        <div className="preview__toolbar-right">
          <button className="preview__tool-btn" onClick={() => setZoom(z => Math.max(z - 10, 50))} title="Zoom out">
            <ZoomOut size={14} />
          </button>
          <span className="preview__zoom-label">{zoom}%</span>
          <button className="preview__tool-btn" onClick={() => setZoom(z => Math.min(z + 10, 200))} title="Zoom in">
            <ZoomIn size={14} />
          </button>
          <button className="preview__tool-btn" onClick={loadPreview} title="Refresh preview">
            <RefreshCw size={14} className={loading ? 'preview__spin' : ''} />
          </button>
          <button className="preview__download-btn" onClick={() => onDownload(document)}>
            <Download size={14} />
            Download
          </button>
        </div>
      </div>

      {/* Selection hint */}
      {!showToolbar && (
        <div className="preview__hint">
          <MousePointer size={11} />
          Click any paragraph to select it · Ctrl+Click for multiple selection
        </div>
      )}

      {/* Preview area */}
      <div className="preview__area">
        {loading && (
          <div className="preview__loading">
            <div className="preview__loading-spinner" />
            <span>Updating preview...</span>
          </div>
        )}
        {html && (
          <div className="preview__paper-wrapper">
            <div
              className="preview__paper"
              style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top center' }}
            >
              <iframe
                ref={iframeRef}
                srcDoc={html}
                title="Document Preview"
                className="preview__iframe"
                sandbox="allow-same-origin allow-scripts"
              />
            </div>
          </div>
        )}
      </div>

      {/* Selection toolbar */}
      {showToolbar && selectedTexts.length > 0 && (
        <SelectionToolbar
          selectedTexts={selectedTexts}
          position={toolbarPos}
          onApply={handleSelectionAction}
          onClose={() => { setShowToolbar(false); setSelectedTexts([]) }}
          loading={cmdLoading}
        />
      )}
    </div>
  )
}

export default DocumentPreview