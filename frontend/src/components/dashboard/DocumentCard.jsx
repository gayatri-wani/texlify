import { useState } from 'react'
import { FileText, Trash2, Edit2, Check, X, Calendar } from 'lucide-react'
import { documentService } from '../../services/documentService'
import { toast } from 'react-hot-toast'
import './DocumentCard.css'

const DocumentCard = ({ document, onSelect, onDelete, isSelected }) => {
  const [editing, setEditing]   = useState(false)
  const [title, setTitle]       = useState(document.title)
  const [saving, setSaving]     = useState(false)

  const handleRename = async () => {
    if (!title.trim() || title === document.title) {
      setEditing(false)
      setTitle(document.title)
      return
    }
    setSaving(true)
    try {
      await documentService.rename(document.id, title.trim())
      toast.success('Renamed!')
      setEditing(false)
    } catch {
      toast.error('Rename failed')
      setTitle(document.title)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter')  handleRename()
    if (e.key === 'Escape') { setEditing(false); setTitle(document.title) }
  }

  const formatDate = (dateStr) => {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric'
    })
  }

  const formatSize = (bytes) => {
    if (!bytes) return '—'
    if (bytes < 1024)        return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  return (
    <div
      className={`doc-card ${isSelected ? 'doc-card--selected' : ''}`}
      onClick={() => !editing && onSelect(document)}
    >
      <div className="doc-card__icon">
        <FileText size={18} />
      </div>

      <div className="doc-card__body">
        {editing ? (
          <div
            className="doc-card__rename"
            onClick={(e) => e.stopPropagation()}
          >
            <input
              className="doc-card__rename-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
            />
            <button
              className="doc-card__rename-btn doc-card__rename-btn--save"
              onClick={handleRename}
              disabled={saving}
            >
              <Check size={12} />
            </button>
            <button
              className="doc-card__rename-btn doc-card__rename-btn--cancel"
              onClick={(e) => {
                e.stopPropagation()
                setEditing(false)
                setTitle(document.title)
              }}
            >
              <X size={12} />
            </button>
          </div>
        ) : (
          <p className="doc-card__title">{title}</p>
        )}
        <div className="doc-card__meta">
          <span className="doc-card__meta-item">
            <Calendar size={10} />
            {formatDate(document.created_at)}
          </span>
          <span className="doc-card__meta-dot" />
          <span className="doc-card__meta-item">
            {formatSize(document.file_size)}
          </span>
          {document.page_count > 1 && (
            <>
              <span className="doc-card__meta-dot" />
              <span className="doc-card__meta-item">
                {document.page_count}p
              </span>
            </>
          )}
        </div>
      </div>

      <div
        className="doc-card__actions"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="doc-card__action-btn"
          onClick={() => setEditing(true)}
          title="Rename"
        >
          <Edit2 size={12} />
        </button>
        <button
          className="doc-card__action-btn doc-card__action-btn--danger"
          onClick={() => onDelete(document.id)}
          title="Delete"
        >
          <Trash2 size={12} />
        </button>
      </div>
    </div>
  )
}

export default DocumentCard