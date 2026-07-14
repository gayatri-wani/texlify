import { useState, useEffect, useRef, useCallback } from 'react'
import {
  RefreshCw, Download, ZoomIn, ZoomOut,
  FileText, MousePointer, Hash
} from 'lucide-react'
import { documentService } from '../../services/documentService'
import SelectionToolbar from './SelectionToolbar'
import './DocumentPreview.css'

const DocumentPreview = ({
  document, refreshTrigger, onDownload, onSelectionCommand
}) => {
  const [html, setHtml]                   = useState('')
  const [loading, setLoading]             = useState(false)
  const [zoom, setZoom]                   = useState(100)
  const [selectedTexts, setSelectedTexts] = useState([])
  const [toolbarPos, setToolbarPos]       = useState({ x: 0, y: 0 })
  const [showToolbar, setShowToolbar]     = useState(false)
  const [cmdLoading, setCmdLoading]       = useState(false)
  const [wordCount, setWordCount]         = useState(null)
  const [scrollPos, setScrollPos]         = useState(0)
  const iframeRef                         = useRef()
  const containerRef                      = useRef()
  const areaRef                           = useRef()

  const loadPreview = async () => {
    if (!document) return
    // Save scroll position before refresh
    if (areaRef.current) setScrollPos(areaRef.current.scrollTop)
    setLoading(true)
    try {
      const htmlContent = await documentService.getPreview(document.id)
      setHtml(htmlContent)
      // Extract word count from HTML
      const tempDiv = window.document.createElement('div')
      tempDiv.innerHTML = htmlContent
      const text  = tempDiv.textContent || tempDiv.innerText || ''
      const words = text.trim().split(/\s+/).filter(w => w.length > 0).length
      setWordCount(words)
    } catch {
      setHtml('<div style="padding:40px;color:#666;font-family:sans-serif;">Preview failed. Download the document to see changes.</div>')
    } finally {
      setLoading(false)
    }
  }

  // Restore scroll position after content loads
  useEffect(() => {
    if (!loading && areaRef.current && scrollPos > 0) {
      setTimeout(() => {
        if (areaRef.current) areaRef.current.scrollTop = scrollPos
      }, 100)
    }
  }, [loading, html])

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
            const para = e.target.closest('p, h1, h2, h3, h4, h5, h6, li, td, th');
            if (!para) return;
            if (ctrlHeld) {
              if (para.classList.contains('texlify-selected')) {
                para.classList.remove('texlify-selected');
                selectedElements = selectedElements.filter(el => el !== para);
              } else {
                para.classList.add('texlify-selected');
                selectedElements.push(para);
              }
            } else {
              document.querySelectorAll('.texlify-selected').forEach(el => {
                el.classList.remove('texlify-selected');
              });
              selectedElements = [];
              para.classList.add('texlify-selected');
              selectedElements = [para];
            }
            const texts = selectedElements
              .map(el => el.textContent.trim())
              .filter(Boolean);
            const rect = para.getBoundingClientRect();
            window.parent.postMessage({
              type: 'texlify-selection',
              texts,
              rect: { top: rect.top, left: rect.left, bottom: rect.bottom, right: rect.right }
            }, '*');
          });

          const style = document.createElement('style');
          style.textContent = \`
            p, h1, h2, h3, h4, h5, h6, li, td, th {
              cursor: pointer;
              border-radius: 3px;
              transition: background 0.1s;
            }
            p:hover, h1:hover, h2:hover, h3:hover, h4:hover,
            h5:hover, h6:hover, li:hover, td:hover, th:hover {
              background: rgba(16,185,129,0.06) !important;
              outline: 1px dashed rgba(16,185,129,0.4);
            }
            .texlify-selected {
              background: rgba(16,185,129,0.15) !important;
              outline: 2px solid rgba(16,185,129,0.6) !important;
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
        setShowToolbar(false); setSelectedTexts([]); return
      }
      setSelectedTexts(texts)
      const iframeRect = iframeRef.current?.getBoundingClientRect()
      if (!iframeRect) return
      const scale = zoom / 100
      const x = Math.min(iframeRect.left + rect.left * scale, window.innerWidth - 360)
      const y = Math.max(iframeRect.top  + rect.top  * scale - 10, 10)
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
        await onSelectionCommand(document.id, action.command, null)
      } else {
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
          {wordCount !== null && (
            <div className="preview__word-count">
              <Hash size={11} />
              {wordCount.toLocaleString()} words
            </div>
          )}
        </div>
        <div className="preview__toolbar-right">
          <button
            className="preview__tool-btn"
            onClick={() => setZoom(z => Math.max(z - 10, 50))}
            title="Zoom out"
          >
            <ZoomOut size={14} />
          </button>
          <span className="preview__zoom-label">{zoom}%</span>
          <button
            className="preview__tool-btn"
            onClick={() => setZoom(z => Math.min(z + 10, 200))}
            title="Zoom in"
          >
            <ZoomIn size={14} />
          </button>
          <button
            className="preview__tool-btn"
            onClick={loadPreview}
            title="Refresh preview"
          >
            <RefreshCw size={14} className={loading ? 'preview__spin' : ''} />
          </button>
          <button
            className="preview__download-btn"
            onClick={() => onDownload(document)}
          >
            <Download size={14} />
            Download
          </button>
        </div>
      </div>

      {/* Selection hint */}
      {!showToolbar && (
        <div className="preview__hint">
          <MousePointer size={11} />
          Click any paragraph to select · Ctrl+Click for multiple selection
        </div>
      )}

      {/* Preview area */}
      <div className="preview__area" ref={areaRef}>
        {loading && (
          <div className="preview__loading">
            <div className="preview__loading-skeleton">
              <div className="preview__skeleton-line preview__skeleton-line--title" />
              <div className="preview__skeleton-line" />
              <div className="preview__skeleton-line" />
              <div className="preview__skeleton-line preview__skeleton-line--short" />
              <div className="preview__skeleton-line preview__skeleton-line--title" />
              <div className="preview__skeleton-line" />
              <div className="preview__skeleton-line" />
            </div>
          </div>
        )}
        {html && !loading && (
          <div className="preview__paper-wrapper">
            <div
              className="preview__paper"
              style={{
                transform: `scale(${zoom / 100})`,
                transformOrigin: 'top center'
              }}
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