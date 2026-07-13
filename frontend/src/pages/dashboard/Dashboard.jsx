import { useState, useEffect, useCallback } from 'react'
import { toast } from 'react-hot-toast'
import { FileText, Plus, X, ChevronLeft, ChevronRight } from 'lucide-react'
import Sidebar from '../../components/layout/Sidebar'
import UploadZone from '../../components/dashboard/UploadZone'
import DocumentCard from '../../components/dashboard/DocumentCard'
import ChatInterface from '../../components/dashboard/ChatInterface'
import DocumentPreview from '../../components/dashboard/DocumentPreview'
import UndoPanel from '../../components/dashboard/UndoPanel'
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

  const handleRename = async (id, title) => {
    try {
      await documentService.rename(id, title)
      setDocuments(prev =>
        prev.map(d => d.id === id ? { ...d, title } : d)
      )
      if (selectedDoc?.id === id) {
        setSelectedDoc(prev => ({ ...prev, title }))
      }
      toast.success('Document renamed!')
    } catch {
      toast.error('Rename failed')
      throw new Error('rename failed')
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
      return result
    } catch (err) {
      if (err?.response?.status === 429) {
        toast.error('Too many commands — please wait a moment')
      }
      throw err
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
        result = await documentService.sendCommand(documentId, command)
      }
      setPreviewKey(k => k + 1)
      toast.success('Applied to selected text!')
      return result
    } catch (err) {
      if (err?.response?.status === 429) {
        toast.error('Too many commands — please wait a moment')
      } else {
        toast.error('Selection command failed')
      }
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

  const handleUndo = useCallback(() => {
    setPreviewKey(k => k + 1)
  }, [])

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
              Chat to edit · Click paragraph to select · Ctrl+Click for multi-select · 📎 to insert images
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

          {/* LEFT: Document list + Undo */}
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
              <>
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
                        onRename={handleRename}
                        isSelected={selectedDoc?.id === doc.id}
                      />
                    ))
                  )}
                </div>

                {/* Undo Panel */}
                <UndoPanel
                  document={selectedDoc}
                  onUndo={handleUndo}
                />
              </>
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