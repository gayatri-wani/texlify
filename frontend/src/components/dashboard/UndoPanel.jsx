import { useState, useEffect } from 'react'
import { RotateCcw, Clock, ChevronDown, ChevronUp, Loader } from 'lucide-react'
import { documentService } from '../../services/documentService'
import { toast } from 'react-hot-toast'
import './UndoPanel.css'

const UndoPanel = ({ document, onUndo }) => {
  const [backups, setBackups]     = useState([])
  const [loading, setLoading]     = useState(false)
  const [expanded, setExpanded]   = useState(false)
  const [restoring, setRestoring] = useState(null)

  useEffect(() => {
    if (document && expanded) loadBackups()
  }, [document?.id, expanded])

  const loadBackups = async () => {
    if (!document) return
    setLoading(true)
    try {
      const data = await documentService.getBackups(document.id)
      setBackups(data.backups || [])
    } catch {
      setBackups([])
    } finally {
      setLoading(false)
    }
  }

  const handleUndo = async (backup) => {
    if (!window.confirm(
      `Restore document to: ${backup.display}?\nAll changes after this point will be lost.`
    )) return
    setRestoring(backup.filename)
    try {
      await documentService.undo(document.id, backup.filename)
      toast.success('Document restored!')
      if (onUndo) onUndo()
      await loadBackups()
    } catch {
      toast.error('Restore failed')
    } finally {
      setRestoring(null)
    }
  }

  if (!document) return null

  return (
    <div className="undo-panel">
      <button
        className="undo-panel__toggle"
        onClick={() => { setExpanded(!expanded); if (!expanded) loadBackups() }}
      >
        <RotateCcw size={13} />
        <span>Undo History</span>
        {expanded
          ? <ChevronUp size={12} />
          : <ChevronDown size={12} />
        }
      </button>

      {expanded && (
        <div className="undo-panel__list">
          {loading ? (
            <div className="undo-panel__loading">
              <Loader size={14} className="undo-panel__spin" />
              <span>Loading backups...</span>
            </div>
          ) : backups.length === 0 ? (
            <div className="undo-panel__empty">
              No backups yet. Backups are created automatically before each command.
            </div>
          ) : (
            backups.map((backup) => (
              <div key={backup.filename} className="undo-panel__item">
                <div className="undo-panel__item-info">
                  <Clock size={11} />
                  <span>{backup.display}</span>
                </div>
                <button
                  className="undo-panel__restore-btn"
                  onClick={() => handleUndo(backup)}
                  disabled={restoring === backup.filename}
                  title="Restore to this version"
                >
                  {restoring === backup.filename ? (
                    <Loader size={11} className="undo-panel__spin" />
                  ) : (
                    <RotateCcw size={11} />
                  )}
                  Restore
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default UndoPanel