import { FileText, Trash2, MessageSquare, Clock, Download } from 'lucide-react'
import { documentService } from '../../services/documentService'
import { toast } from 'react-hot-toast'
import './DocumentCard.css'

const DocumentCard = ({ document, onSelect, onDelete, isSelected }) => {

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric',
    })
  }

  const formatSize = (bytes) => {
    if (!bytes) return '—'
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const handleDownload = async (e) => {
    e.stopPropagation()
    try {
      await documentService.download(document.id, document.original_filename)
      toast.success('Download started!')
    } catch {
      toast.error('Download failed')
    }
  }

  return (
    <div className={`doc-card ${isSelected ? 'doc-card--selected' : ''}`}>

      <div className="doc-card__icon">
        <FileText size={22} />
      </div>

      <div className="doc-card__info">
        <h4 className="doc-card__title">{document.title}</h4>
        <div className="doc-card__meta">
          <span className="doc-card__meta-item">
            <Clock size={11} />{formatDate(document.created_at)}
          </span>
          <span className="doc-card__meta-dot">·</span>
          <span className="doc-card__meta-item">{formatSize(document.file_size)}</span>
          {document.page_count > 0 && (
            <>
              <span className="doc-card__meta-dot">·</span>
              <span className="doc-card__meta-item">{document.page_count}p</span>
            </>
          )}
        </div>
      </div>

      <div className="doc-card__actions">
        <button
          className="doc-card__btn doc-card__btn--edit"
          onClick={() => onSelect(document)}
          title="Edit with AI"
        >
          <MessageSquare size={14} />
          <span>Edit</span>
        </button>
        <button
          className="doc-card__btn doc-card__btn--download"
          onClick={handleDownload}
          title="Download"
        >
          <Download size={14} />
        </button>
        <button
          className="doc-card__btn doc-card__btn--delete"
          onClick={() => onDelete(document.id)}
          title="Delete"
        >
          <Trash2 size={14} />
        </button>
      </div>

    </div>
  )
}

export default DocumentCard