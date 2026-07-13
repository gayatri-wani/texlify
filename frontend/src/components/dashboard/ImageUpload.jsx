import { useState, useRef } from 'react'
import { Upload, Image, X, Check, Loader } from 'lucide-react'
import { documentService } from '../../services/documentService'
import { toast } from 'react-hot-toast'
import './ImageUpload.css'

const ImageUpload = ({ onImageUploaded, onClose }) => {
  const [dragging, setDragging]   = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress]   = useState(0)
  const [uploaded, setUploaded]   = useState(null)
  const fileRef                   = useRef()

  const handleFile = async (file) => {
    if (!file) return
    const allowed = ['image/jpeg','image/png','image/gif','image/webp','image/bmp']
    if (!allowed.includes(file.type)) {
      toast.error('Only JPEG, PNG, GIF, WEBP or BMP images allowed')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Image must be under 10MB')
      return
    }
    setUploading(true)
    setProgress(0)
    try {
      const result = await documentService.uploadImage(file, setProgress)
      setUploaded(result)
      toast.success('Image uploaded!')
    } catch {
      toast.error('Image upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleUse = () => {
    if (uploaded) {
      onImageUploaded(uploaded.server_path, uploaded.filename)
      onClose()
    }
  }

  return (
    <div className="img-upload">
      <div className="img-upload__header">
        <div className="img-upload__title">
          <Image size={16} />
          Upload Image
        </div>
        <button className="img-upload__close" onClick={onClose}>
          <X size={14} />
        </button>
      </div>

      {!uploaded ? (
        <>
          <div
            className={`img-upload__zone ${dragging ? 'img-upload__zone--dragging' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
          >
            {uploading ? (
              <div className="img-upload__progress">
                <Loader size={24} className="img-upload__spin" />
                <p>Uploading... {progress}%</p>
                <div className="img-upload__bar">
                  <div
                    className="img-upload__bar-fill"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            ) : (
              <>
                <Upload size={28} />
                <p>Drag and drop an image here</p>
                <span>or click to browse</span>
                <small>JPEG, PNG, GIF, WEBP · Max 10MB</small>
              </>
            )}
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={(e) => handleFile(e.target.files[0])}
          />
        </>
      ) : (
        <div className="img-upload__success">
          <div className="img-upload__success-icon">
            <Check size={20} />
          </div>
          <img
            src={`http://127.0.0.1:8000${uploaded.url}`}
            alt="Uploaded"
            className="img-upload__preview"
          />
          <p className="img-upload__filename">{uploaded.filename}</p>
          <div className="img-upload__success-actions">
            <button className="img-upload__use-btn" onClick={handleUse}>
              <Check size={14} />
              Insert this image
            </button>
            <button
              className="img-upload__retry-btn"
              onClick={() => { setUploaded(null); setProgress(0) }}
            >
              Upload different
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ImageUpload