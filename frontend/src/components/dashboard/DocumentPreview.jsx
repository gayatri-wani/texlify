import { useState, useEffect, useRef } from 'react'
import {
  RefreshCw, Download, ZoomIn, ZoomOut,
  FileText, MousePointer
} from 'lucide-react'
import { documentService } from '../../services/documentService'
import SelectionToolbar from './SelectionToolbar'
import './DocumentPreview.css'

const DocumentPreview = ({
  document,
  refreshTrigger,
  onDownload,
  onSelectionCommand
}) => {
  const [html, setHtml]                   = useState('')
  const [loading, setLoading]             = useState(false)
  const [zoom, setZoom]                   = useState(100)
  const [selectedTexts, setSelectedTexts] = useState([])
  const [toolbarPos, setToolbarPos]       = useState({ x: 0, y: 0 })
  const [showToolbar, setShowToolbar]     = useState(false)
  const [cmdLoading, setCmdLoading]       = useState(false)
  const iframeRef                         = useRef()
  const containerRef                      = useRef()

  const loadPreview = async () => {
    if (!document) return
    setLoading(true)
    try {
      const content = await documentService.getPreview(document.id)
      setHtml(content)
    } catch {
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

  // Inject selection script into iframe
  useEffect(() => {
    if (!html || !iframeRef.current) return
    const iframe = iframeRef.current

    const inject = () => {
      try {
        const doc = iframe.contentDocument || iframe.contentWindow?.document
        if (!doc) return
        const existing = doc.getElementById('texlify-sel-script')
        if (existing) existing.remove()
        const script = doc.createElement('script')
        script.id = 'texlify-sel-script'
        script.textContent = `
          (function() {
            if (window.__texlifyInjected) return;
            window.__texlifyInjected = true;
            let selected = [];
            let ctrlHeld = false;
            document.addEventListener('keydown', e => {
              if (e.key==='Control'||e.key==='Meta') ctrlHeld=true;
            });
            document.addEventListener('keyup', e => {
              if (e.key==='Control'||e.key==='Meta') ctrlHeld=false;
            });
            document.addEventListener('click', e => {
              const el = e.target.closest('p,h1,h2,h3,h4,h5,h6,li,td,th');
              if (!el) return;
              if (ctrlHeld) {
                if (el.classList.contains('tx-sel')) {
                  el.classList.remove('tx-sel');
                  selected = selected.filter(x => x !== el);
                } else {
                  el.classList.add('tx-sel');
                  selected.push(el);
                }
              } else {
                document.querySelectorAll('.tx-sel').forEach(x => x.classList.remove('tx-sel'));
                selected = [];
                el.classList.add('tx-sel');
                selected = [el];
              }
              const texts = selected.map(x=>x.textContent.trim()).filter(Boolean);
              const rect  = el.getBoundingClientRect();
              window.parent.postMessage({
                type:'texlify-selection', texts,
                rect:{top:rect.top,left:rect.left,bottom:rect.bottom,right:rect.right}
              },'*');
            });
            const style = document.createElement('style');
            style.textContent = \`
              p,h1,h2,h3,h4,h5,h6,li,td,th {
                cursor:pointer; border-radius:3px; transition:background 0.1s;
              }
              p:hover,h1:hover,h2:hover,h3:hover,h4:hover,h5:hover,
              h6:hover,li:hover,td:hover,th:hover {
                background:rgba(16,185,129,0.06)!important;
                outline:1px dashed rgba(16,185,129,0.4);
              }
              .tx-sel {
                background:rgba(16,185,129,0.18)!important;
                outline:2px solid rgba(16,185,129,0.65)!important;
              }
            \`;
            document.head.appendChild(style);
          })();
        `
        doc.body.appendChild(script)
      } catch (e) {
        console.warn('iframe inject:', e)
      }
    }

    iframe.addEventListener('load', inject)
    if (iframe.contentDocument?.readyState === 'complete') inject()
    return () => iframe.removeEventListener('load', inject)
  }, [html])

  // Listen for selection messages from iframe
  useEffect(() => {
    const onMsg = (e) => {
      if (e.data?.type !== 'texlify-selection') return
      const { texts, rect } = e.data
      if (!texts?.length) {
        setShowToolbar(false); setSelectedTexts([]); return
      }
      setSelectedTexts(texts)
      const iframe     = iframeRef.current
      const iframeRect = iframe?.getBoundingClientRect()
      if (!iframeRect) return
      const scale = zoom / 100
      const x = Math.min(iframeRect.left + rect.left * scale, window.innerWidth - 340)
      const y = Math.max(iframeRect.top  + rect.top  * scale - 10, 10)
      setToolbarPos({ x, y })
      setShowToolbar(true)
    }
    window.addEventListener('message', onMsg)
    return () => window.removeEventListener('message', onMsg)
  }, [zoom])

  // Close toolbar on outside click
  useEffect(() => {
    const handler = (e) => {
      if (!e.target.closest('.selection-toolbar') &&
          !e.target.closest('iframe')) {
        setShowToolbar(false)
      }
    }
    window.document.addEventListener('click', handler)
    return () => window.document.removeEventListener('click', handler)
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
          {selectedTexts.length > 0 && (
            <div className="preview__sel-badge">
              <MousePointer size={10} />
              {selectedTexts.length} selected
            </div>
          )}
        </div>
        <div className="preview__toolbar-right">
          <button className="preview__tool-btn"
            onClick={() => setZoom(z => Math.max(z - 10, 50))}>
            <ZoomOut size={14} />
          </button>
          <span className="preview__zoom-label">{zoom}%</span>
          <button className="preview__tool-btn"
            onClick={() => setZoom(z => Math.min(z + 10, 200))}>
            <ZoomIn size={14} />
          </button>
          <button className="preview__tool-btn" onClick={loadPreview}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
          <button className="preview__download-btn"
            onClick={() => onDownload(document)}>
            <Download size={14} /> Download
          </button>
        </div>
      </div>

      {/* Hint */}
      <div className="preview__hint">
        <MousePointer size={11} />
        Click paragraph to select · Ctrl+Click for multi-select
      </div>

      {/* Preview area */}
      <div className="preview__area">
        {loading && (
          <div className="preview__loading">
            <div className="preview__spinner" />
            <span>Updating preview...</span>
          </div>
        )}
        {html && (
          <div className="preview__paper-wrapper">
            <div className="preview__paper"
              style={{
                transform: `scale(${zoom / 100})`,
                transformOrigin: 'top center'
              }}>
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