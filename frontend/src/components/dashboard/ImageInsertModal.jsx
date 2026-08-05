import { useState, useRef } from 'react'
import {
  X, Upload, Image, AlignLeft, AlignCenter,
  AlignRight, Loader, Check
} from 'lucide-react'
import { documentService } from '../../services/documentService'
import { toast } from 'react-hot-toast'
import './ImageInsertModal.css'

const ImageInsertModal = ({ document, onClose, onInserted }) => {
  const [file, setFile]               = useState(null)
  const [preview, setPreview]         = useState(null)
  const [uploading, setUploading]     = useState(false)
  const [progress, setProgress]       = useState(0)
  const [alignment, setAlignment]     = useState('center')
  const [width, setWidth]             = useState(4.0)
  const [caption, setCaption]         = useState('')
  const [asLogo, setAsLogo]           = useState(false)
  const [logoPos, setLogoPos]         = useState('top_right')
  const [dragOver, setDragOver]       = useState(false)
  const inputRef                      = useRef()

  const handleFile = (f) => {
    if (!f) return
    const allowed = ['image/jpeg','image/png','image/gif','image/webp','image/bmp']
    if (!allowed.includes(f.type)) {
      toast.error('Only JPG, PNG, GIF, WebP, BMP allowed')
      return
    }
    if (f.size > 10 * 1024 * 1024) {
      toast.error('Image must be under 10MB')
      return
    }
    setFile(f)
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target.result)
    reader.readAsDataURL(f)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleInsert = async () => {
    if (!file || !document) return
    setUploading(true)
    setProgress(0)
    try {
      // Step 1: Upload image to server
      const uploadResult = await documentService.uploadImage(
        file,
        (pct) => setProgress(pct)
      )
      setProgress(100)

      // Step 2: Send insert command using server_path
      const cmd = asLogo
        ? `insert logo at ${logoPos} on first page from server path ${uploadResult.server_path} width ${width} inches`
        : `insert image from server path ${uploadResult.server_path} width ${width} inches aligned ${alignment}${caption ? ` with caption "${caption}"` : ''}`

      await documentService.sendCommand(document.id, cmd)
      toast.success('Image inserted into document!')
      onInserted()
      onClose()
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to insert image')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="img-modal-overlay" onClick={(e) => {
      if (e.target === e.currentTarget) onClose()
    }}>
      <div className="img-modal">

        {/* Header */}
        <div className="img-modal__header">
          <div className="img-modal__title">
            <Image size={18} />
            Insert Image into Document
          </div>
          <button className="img-modal__close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="img-modal__body">

          {/* Drop zone */}
          {!preview ? (
            <div
              className={`img-modal__drop ${dragOver ? 'img-modal__drop--active' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
            >
              <input
                ref={inputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => handleFile(e.target.files[0])}
              />
              <Upload size={32} />
              <p>Drop image here or click to browse</p>
              <span>JPG, PNG, GIF, WebP, BMP · max 10MB</span>
            </div>
          ) : (
            <div className="img-modal__preview">
              <img src={preview} alt="Preview" />
              <button
                className="img-modal__preview-remove"
                onClick={() => { setFile(null); setPreview(null) }}
              >
                <X size={14} /> Remove
              </button>
            </div>
          )}

          {/* Options */}
          {preview && (
            <div className="img-modal__options">

              {/* Logo toggle */}
              <label className="img-modal__toggle">
                <input
                  type="checkbox"
                  checked={asLogo}
                  onChange={(e) => setAsLogo(e.target.checked)}
                />
                <span>Insert as logo in header</span>
              </label>

              {asLogo ? (
                <div className="img-modal__field">
                  <label>Logo position</label>
                  <div className="img-modal__radio-group">
                    {[
                      { value: 'top_left',   label: 'Top Left' },
                      { value: 'top_center', label: 'Top Center' },
                      { value: 'top_right',  label: 'Top Right' },
                    ].map(opt => (
                      <label key={opt.value} className="img-modal__radio">
                        <input
                          type="radio"
                          name="logoPos"
                          value={opt.value}
                          checked={logoPos === opt.value}
                          onChange={() => setLogoPos(opt.value)}
                        />
                        {opt.label}
                      </label>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  {/* Alignment */}
                  <div className="img-modal__field">
                    <label>Alignment</label>
                    <div className="img-modal__align-group">
                      {[
                        { value: 'left',   icon: AlignLeft },
                        { value: 'center', icon: AlignCenter },
                        { value: 'right',  icon: AlignRight },
                      ].map(({ value, icon: Icon }) => (
                        <button
                          key={value}
                          className={`img-modal__align-btn ${alignment === value ? 'img-modal__align-btn--active' : ''}`}
                          onClick={() => setAlignment(value)}
                          title={value}
                        >
                          <Icon size={16} />
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Width */}
                  <div className="img-modal__field">
                    <label>Width: <strong>{width} inches</strong></label>
                    <input
                      type="range"
                      min="1"
                      max="7"
                      step="0.5"
                      value={width}
                      onChange={(e) => setWidth(parseFloat(e.target.value))}
                      className="img-modal__slider"
                    />
                    <div className="img-modal__slider-labels">
                      <span>1"</span><span>7"</span>
                    </div>
                  </div>

                  {/* Caption */}
                  <div className="img-modal__field">
                    <label>Caption (optional)</label>
                    <input
                      type="text"
                      className="img-modal__input"
                      placeholder="e.g. Figure 1: System Architecture"
                      value={caption}
                      onChange={(e) => setCaption(e.target.value)}
                    />
                  </div>
                </>
              )}
            </div>
          )}

          {/* Progress bar */}
          {uploading && (
            <div className="img-modal__progress">
              <div
                className="img-modal__progress-bar"
                style={{ width: `${progress}%` }}
              />
              <span>{progress < 100 ? `Uploading… ${progress}%` : 'Inserting into document…'}</span>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="img-modal__footer">
          <button className="img-modal__cancel" onClick={onClose} disabled={uploading}>
            Cancel
          </button>
          <button
            className="img-modal__insert"
            onClick={handleInsert}
            disabled={!file || uploading}
          >
            {uploading
              ? <><Loader size={14} className="animate-spin" /> Inserting…</>
              : <><Check size={14} /> Insert Image</>
            }
          </button>
        </div>

      </div>
    </div>
  )
}

export default ImageInsertModal