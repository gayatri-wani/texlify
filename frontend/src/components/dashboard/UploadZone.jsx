import { useState, useRef } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import './UploadZone.css'

const UploadZone = ({ onUpload, uploading }) => {
  const [dragOver, setDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const inputRef = useRef()

  const validateAndSet = (file) => {
    const allowed = [
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
    ]
    if (!allowed.includes(file.type)) {
      alert('Only .docx or .doc files are allowed')
      return
    }
    if (file.size > 50 * 1024 * 1024) {
      alert('File size must be under 50MB')
      return
    }
    setSelectedFile(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) validateAndSet(file)
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) validateAndSet(file)
  }

  const handleUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile)
      setSelectedFile(null)
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="upload-zone-wrapper">

      <div
        className={[
          'upload-zone',
          dragOver ? 'upload-zone--dragover' : '',
          selectedFile ? 'upload-zone--has-file' : '',
        ].filter(Boolean).join(' ')}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !selectedFile && inputRef.current.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".docx,.doc"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />

        {!selectedFile ? (
          <div className="upload-zone__empty">
            <div className="upload-zone__icon"><Upload size={28} /></div>
            <p className="upload-zone__title">Drop your Word document here</p>
            <p className="upload-zone__subtitle">
              or <span className="upload-zone__browse">browse files</span>
            </p>
            <p className="upload-zone__hint">.docx or .doc · max 50MB</p>
          </div>
        ) : (
          <div className="upload-zone__selected">
            <div className="upload-zone__file-icon"><FileText size={24} /></div>
            <div className="upload-zone__file-info">
              <span className="upload-zone__file-name">{selectedFile.name}</span>
              <span className="upload-zone__file-size">{formatSize(selectedFile.size)}</span>
            </div>
            <button
              className="upload-zone__remove"
              onClick={(e) => { e.stopPropagation(); setSelectedFile(null) }}
            >
              <X size={16} />
            </button>
          </div>
        )}
      </div>

      {selectedFile && (
        <button
          className={`upload-btn ${uploading ? 'upload-btn--loading' : ''}`}
          onClick={handleUpload}
          disabled={uploading}
        >
          {uploading
            ? <><span className="upload-btn__spinner" />Uploading...</>
            : <><Upload size={15} />Upload Document</>
          }
        </button>
      )}

    </div>
  )
}

export default UploadZone