import { useState } from 'react'
import {
  Bold, Italic, Underline, Strikethrough,
  Highlighter, Type, AlignCenter, Heading1,
  Send, X, ChevronDown
} from 'lucide-react'
import './SelectionToolbar.css'

const QUICK_ACTIONS = [
  { label: 'Bold',        icon: Bold,          type: 'bold' },
  { label: 'Italic',      icon: Italic,         type: 'italic' },
  { label: 'Underline',   icon: Underline,      type: 'underline' },
  { label: 'Strike',      icon: Strikethrough,  type: 'strikethrough' },
  { label: 'Highlight',   icon: Highlighter,    type: 'highlight',   extra: { highlight_color: 'yellow' } },
  { label: 'H1',          icon: Heading1,       type: 'heading',     extra: { make_heading: 1 } },
  { label: 'UPPER',       icon: Type,           type: 'uppercase' },
  { label: 'Center',      icon: AlignCenter,    type: 'align',       extra: { alignment: 'center' } },
]

const SelectionToolbar = ({
  selectedTexts,
  position,
  onApply,
  onClose,
  loading
}) => {
  const [customCmd, setCustomCmd]   = useState('')
  const [showCustom, setShowCustom] = useState(false)

  if (!selectedTexts?.length) return null

  const handleQuick = (action) => {
    onApply({
      type: 'apply_to_selection',
      params: {
        selected_texts: selectedTexts,
        command_type:   action.type,
        ...(action.extra || {})
      }
    })
  }

  const handleCustom = (e) => {
    e.preventDefault()
    if (!customCmd.trim()) return
    const ctx = selectedTexts.slice(0, 2).map(t => `"${t.slice(0,50)}"`).join(', ')
    onApply({
      type:          'custom_command',
      command:       `For selected text ${ctx}: ${customCmd}`,
      selected_texts: selectedTexts
    })
    setCustomCmd('')
    setShowCustom(false)
  }

  return (
    <div
      className="selection-toolbar"
      style={{ top: position.y + 'px', left: position.x + 'px' }}
    >
      {/* Header */}
      <div className="selection-toolbar__header">
        <span className="selection-toolbar__count">
          {selectedTexts.length} paragraph{selectedTexts.length > 1 ? 's' : ''} selected
        </span>
        <button className="selection-toolbar__close" onClick={onClose}>
          <X size={12} />
        </button>
      </div>

      {/* Quick actions */}
      <div className="selection-toolbar__actions">
        {QUICK_ACTIONS.map((a) => (
          <button
            key={a.type + (a.extra?.make_heading || '')}
            className="selection-toolbar__btn"
            onClick={() => handleQuick(a)}
            disabled={loading}
            title={a.label}
          >
            <a.icon size={13} />
            <span>{a.label}</span>
          </button>
        ))}
      </div>

      {/* Custom toggle */}
      <button
        className="selection-toolbar__custom-toggle"
        onClick={() => setShowCustom(!showCustom)}
      >
        <ChevronDown size={12}
          style={{ transform: showCustom ? 'rotate(180deg)' : 'none',
                   transition: '0.2s' }} />
        Custom command
      </button>

      {/* Custom input */}
      {showCustom && (
        <form className="selection-toolbar__custom" onSubmit={handleCustom}>
          <input
            className="selection-toolbar__input"
            value={customCmd}
            onChange={(e) => setCustomCmd(e.target.value)}
            placeholder="e.g. make font size 14, color red..."
            autoFocus
          />
          <button
            type="submit"
            className="selection-toolbar__send"
            disabled={!customCmd.trim() || loading}
          >
            <Send size={12} />
          </button>
        </form>
      )}

      {/* Preview */}
      <div className="selection-toolbar__preview">
        {selectedTexts.slice(0, 2).map((t, i) => (
          <div key={i} className="selection-toolbar__preview-item">
            "{t.slice(0, 60)}{t.length > 60 ? '...' : ''}"
          </div>
        ))}
        {selectedTexts.length > 2 && (
          <div className="selection-toolbar__preview-more">
            +{selectedTexts.length - 2} more
          </div>
        )}
      </div>
    </div>
  )
}

export default SelectionToolbar