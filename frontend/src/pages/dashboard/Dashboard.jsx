import { useState, useEffect, useCallback } from 'react'
import { toast } from 'react-hot-toast'
import { FileText, Plus, X, ChevronLeft, ChevronRight, History } from 'lucide-react'
import Sidebar from '../../components/layout/Sidebar'
import UploadZone from '../../components/dashboard/UploadZone'
import DocumentCard from '../../components/dashboard/DocumentCard'
import ChatInterface from '../../components/dashboard/ChatInterface'
import DocumentPreview from '../../components/dashboard/DocumentPreview'
import { documentService } from '../../services/documentService'
import useAuthStore from '../../store/authStore'
import './Dashboard.css'

const Dashboard = () => {
  const { user }                          = useAuthStore()
  const [documents, setDocuments]         = useState([])
  const [selectedDoc, setSelectedDoc]     = useState(null)
  const [uploading, setUploading]         = useState(false)
  const [loadingDocs, setLoadingDocs]     = useState(true)
  const [cmdLoading, setCmdLoading]       = useState(false)
  const [showUpload, setShowUpload]       = useState(false)
  const [docsCollapsed, setDocsCollapsed] = useState(false)
  const [commandLog, setCommandLog]       = useState([])
  const [previewKey, setPreviewKey]       = useState(0)

  useEffect(() => { fetchDocuments() }, [])

  const fetchDocuments = async () => {
    try {
      const data = await documentService.getAll()
      setDocuments(data)
    } catch {
      toast.error('Failed to load documents')
    } finally {
      setLoadingDocs(false)
    }
  }

  const handleUpload = async (file) => {
    setUploading(true)
    try {
      const doc = await documentService.upload(file)
      setDocuments(prev => [doc, ...prev])
      setSelectedDoc(doc)
      setShowUpload(false)
      toast.success('Document uploaded!')
    } catch {
      toast.error('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this document?')) return
    try {
      await documentService.delete(id)
      setDocuments(prev => prev.filter(d => d.id !== id))
      if (selectedDoc?.id === id) setSelectedDoc(null)
      toast.success('Document deleted')
    } catch {
      toast.error('Delete failed')
    }
  }

  const handleCommand = async (documentId, command) => {
    setCmdLoading(true)
    try {
      const result = await documentService.sendCommand(documentId, command)
      setCommandLog(prev => [{
        id: Date.now(),
        command,
        message: result.message,
        actions: result.actions_performed,
        time: new Date(),
      }, ...prev.slice(0, 49)])
      return result
    } finally {
      setCmdLoading(false)
    }
  }

  const handleCommandSuccess = useCallback(() => {
    setPreviewKey(k => k + 1)
  }, [])

  const handleSelectionCommand = async (documentId, command, selectionParams) => {
    setCmdLoading(true)
    try {
      let result
      if (selectionParams && selectionParams.selected_texts) {
        // Direct selection command — goes straight to executor, bypasses AI
        result = await documentService.selectionCommand(documentId, {
          command_type:    selectionParams.command_type,
          selected_texts:  selectionParams.selected_texts,
          font_name:       selectionParams.font_name       || null,
          font_size:       selectionParams.font_size       || null,
          color:           selectionParams.color           || null,
          highlight_color: selectionParams.highlight_color || null,
          alignment:       selectionParams.alignment       || null,
          make_heading:    selectionParams.make_heading    || null,
        })
      } else {
        // Custom text command — goes through AI parser
        result = await documentService.sendCommand(documentId, command)
      }

      setCommandLog(prev => [{
        id: Date.now(),
        command: `[Selection] ${selectionParams?.command_type || command}`,
        message: result?.message || 'Applied to selection',
        actions: result?.actions_performed || [],
        time: new Date(),
      }, ...prev.slice(0, 49)])

      setPreviewKey(k => k + 1)
      toast.success('Applied to selected text!')
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Selection command failed'
      toast.error(detail)
    } finally {
      setCmdLoading(false)
    }
  }

  const handleDownload = async (doc) => {
    try {
      await documentService.download(doc.id, doc.original_filename)
      toast.success('Download started!')
    } catch {
      toast.error('Download failed')
    }
  }

  const getGreeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="dashboard">
      <Sidebar />

      <main className="dashboard__main">

        <div className="dashboard__topbar">
          <div>
            <h1 className="dashboard__title">
              {getGreeting()},{' '}
              <span className="dashboard__title-name">
                {user?.full_name?.split(' ')[0]}
              </span> 👋
            </h1>
            <p className="dashboard__subtitle">
              Chat to edit · Click paragraph in preview to select · Ctrl+Click for multi-select
            </p>
          </div>
          <button
            className="dashboard__upload-btn"
            onClick={() => setShowUpload(!showUpload)}
          >
            {showUpload ? <X size={16} /> : <Plus size={16} />}
            {showUpload ? 'Cancel' : 'Upload Document'}
          </button>
        </div>

        {showUpload && (
          <div className="dashboard__upload-section animate-fadeInDown">
            <UploadZone onUpload={handleUpload} uploading={uploading} />
          </div>
        )}

        <div className={`dashboard__content ${docsCollapsed ? 'dashboard__content--collapsed' : ''}`}>

          {/* LEFT: Document list */}
          <div className="dashboard__docs-panel">
            <div className="dashboard__panel-header">
              <h2 className="dashboard__panel-title">
                <FileText size={15} />
                {!docsCollapsed && 'Documents'}
              </h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {!docsCollapsed && (
                  <span className="dashboard__doc-count">{documents.length}</span>
                )}
                <button
                  className="dashboard__collapse-btn"
                  onClick={() => setDocsCollapsed(!docsCollapsed)}
                  title={docsCollapsed ? 'Expand' : 'Collapse'}
                >
                  {docsCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
                </button>
              </div>
            </div>

            {!docsCollapsed && (
              <div className="dashboard__docs-list">
                {loadingDocs ? (
                  <div className="dashboard__loading">
                    {[1, 2, 3].map(i => <div key={i} className="dashboard__skeleton" />)}
                  </div>
                ) : documents.length === 0 ? (
                  <div className="dashboard__empty">
                    <FileText size={32} />
                    <p>No documents yet</p>
                    <span>Upload a .docx file</span>
                  </div>
                ) : (
                  documents.map(doc => (
                    <DocumentCard
                      key={doc.id}
                      document={doc}
                      onSelect={(d) => {
                        setSelectedDoc(d)
                        setPreviewKey(k => k + 1)
                      }}
                      onDelete={handleDelete}
                      isSelected={selectedDoc?.id === doc.id}
                    />
                  ))
                )}
              </div>
            )}

            {!docsCollapsed && commandLog.length > 0 && (
              <div className="dashboard__log">
                <div className="dashboard__log-header">
                  <History size={13} />
                  <span>Recent commands</span>
                </div>
                <div className="dashboard__log-list">
                  {commandLog.slice(0, 10).map(log => (
                    <div key={log.id} className="dashboard__log-item">
                      <p className="dashboard__log-command">"{log.command}"</p>
                      <div className="dashboard__log-badges">
                        {log.actions?.slice(0, 3).map((a, i) => (
                          <span
                            key={i}
                            className={`dashboard__log-badge dashboard__log-badge--${a.status}`}
                          >
                            {a.action}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* MIDDLE: Chat */}
          <div className="dashboard__chat-panel">
            <ChatInterface
              document={selectedDoc}
              onSendCommand={handleCommand}
              loading={cmdLoading}
              onCommandSuccess={handleCommandSuccess}
            />
          </div>

          {/* RIGHT: Live preview with selection */}
          <div className="dashboard__preview-panel">
            <DocumentPreview
              document={selectedDoc}
              refreshTrigger={previewKey}
              onDownload={handleDownload}
              onSelectionCommand={handleSelectionCommand}
            />
          </div>

        </div>
      </main>
    </div>
  )
}

export default Dashboard