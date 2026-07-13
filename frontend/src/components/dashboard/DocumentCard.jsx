import { useState } from 'react'
import {
  FileText, Trash2, Edit3, Download, Check, X, Clock
} from 'lucide-react'
import './DocumentCard.css'

const DocumentCard = ({ document, onSelect, onDelete, onRename, isSelected }) => {
  const [editing, setEditing]   = useState(false)
  const [newTitle, setNewTitle] = useState(document.title)
  const [saving, setSaving]     = useState(false)

  const formatSize = (bytes) => {
    if (bytes < 1024)       return `${bytes} B`
    if (bytes < 1024*1024)  return `${(bytes/1024).toFixed(1)} KB`
    return `${(bytes/(1024*1024)).toFixed(1)} MB`
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric'
    })
  }

  const handleRenameSubmit = async (e) => {
    e.preventDefault()
    if (!newTitle.trim() || newTitle.trim() === document.title) {
      setEditing(false)
      setNewTitle(document.title)
      return
    }
    setSaving(true)
    try {
      await onRename(document.id, newTitle.trim())
      setEditing(false)
    } catch {
      setNewTitle(document.title)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const handleRenameCancel = () => {
    setNewTitle(document.title)
    setEditing(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') handleRenameCancel()
  }

  return (
    <div
      className={`doc-card ${isSelected ? 'doc-card--selected' : ''}`}
      onClick={() => !editing && onSelect(document)}
    >
      <div className="doc-card__icon">
        <FileText size={18} />
      </div>

      <div className="doc-card__info">
        {editing ? (
          <form
            className="doc-card__rename-form"
            onSubmit={handleRenameSubmit}
            onClick={(e) => e.stopPropagation()}
          >
            <input
              className="doc-card__rename-input"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
              disabled={saving}
            />
            <div className="doc-card__rename-actions">
              <button
                type="submit"
                className="doc-card__rename-btn doc-card__rename-btn--confirm"
                disabled={saving}
                title="Save"
              >
                <Check size={12} />
              </button>
              <button
                type="button"
                className="doc-card__rename-btn doc-card__rename-btn--cancel"
                onClick={handleRenameCancel}
                title="Cancel"
              >
                <X size={12} />
              </button>
            </div>
          </form>
        ) : (
          <p className="doc-card__title">{document.title}</p>
        )}
        <div className="doc-card__meta">
          <span><Clock size={10} /> {formatDate(document.created_at)}</span>
          <span>{formatSize(document.file_size)}</span>
          {document.page_count > 0 && (
            <span>{document.page_count}p</span>
          )}
        </div>
      </div>

      <div
        className="doc-card__actions"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="doc-card__action-btn"
          onClick={() => { setEditing(true); setNewTitle(document.title) }}
          title="Rename"
        >
          <Edit3 size={13} />
        </button>
        <button
          className="doc-card__action-btn doc-card__action-btn--danger"
          onClick={() => onDelete(document.id)}
          title="Delete"
        >
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  )
}

export default DocumentCard