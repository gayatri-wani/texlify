import { useState, useRef } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import './UploadZone.css'

const UploadZone = ({ onUpload, uploading }) => {
  const [dragOver, setDragOver] = useState(false)
  const [file, setFile]         = useState(null)
  const inputRef                = useRef()

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped && dropped.name.endsWith('.docx')) {
      setFile(dropped)
    } else {
      alert('Only .docx files are supported')
    }
  }

  const handleFileChange = (e) => {
    const selected = e.target.files[0]
    if (selected) setFile(selected)
  }

  const handleUpload = () => {
    if (file) onUpload(file)
  }

  const clearFile = () => {
    setFile(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="upload-zone">
      {!file ? (
        <div
          className={`upload-zone__drop ${dragOver ? 'upload-zone__drop--active' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".docx"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <div className="upload-zone__icon">
            <Upload size={28} />
          </div>
          <p className="upload-zone__title">
            Drop your Word document here
          </p>
          <p className="upload-zone__subtitle">
            or click to browse · .docx files only · max 50MB
          </p>
        </div>
      ) : (
        <div className="upload-zone__preview">
          <div className="upload-zone__file">
            <div className="upload-zone__file-icon">
              <FileText size={20} />
            </div>
            <div className="upload-zone__file-info">
              <p className="upload-zone__file-name">{file.name}</p>
              <p className="upload-zone__file-size">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <button className="upload-zone__clear" onClick={clearFile}>
              <X size={14} />
            </button>
          </div>
          <button
            className="upload-zone__btn"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? 'Uploading...' : 'Upload Document'}
          </button>
        </div>
      )}
    </div>
  )
}

export default UploadZone