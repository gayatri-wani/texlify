import { useState } from 'react'
import {
  Bold, Italic, Underline, Strikethrough,
  Highlighter, Type, AlignLeft, Heading1,
  Send, X, ChevronDown, AlignCenter,
  AlignJustify, Trash2
} from 'lucide-react'
import './SelectionToolbar.css'

const QUICK_ACTIONS = [
  { label: 'Bold',          icon: Bold,          command_type: 'bold' },
  { label: 'Italic',        icon: Italic,         command_type: 'italic' },
  { label: 'Underline',     icon: Underline,      command_type: 'underline' },
  { label: 'Strike',        icon: Strikethrough,  command_type: 'strikethrough' },
  {
    label: 'Highlight',
    icon: Highlighter,
    command_type: 'highlight',
    extra: { highlight_color: 'yellow' }
  },
  {
    label: 'Heading 1',
    icon: Heading1,
    command_type: 'heading',
    extra: { make_heading: 1 }
  },
  {
    label: 'Center',
    icon: AlignCenter,
    command_type: 'align',
    extra: { alignment: 'center' }
  },
  {
    label: 'Justify',
    icon: AlignJustify,
    command_type: 'align',
    extra: { alignment: 'justify' }
  },
  { label: 'UPPER',         icon: Type,           command_type: 'uppercase' },
  { label: 'lower',         icon: Type,           command_type: 'lowercase' },
  { label: 'Remove Fmt',    icon: Trash2,         command_type: 'remove_formatting' },
]

const HIGHLIGHT_COLORS = [
  { label: 'Yellow',    value: 'yellow',    hex: '#FEF08A' },
  { label: 'Green',     value: 'green',     hex: '#BBF7D0' },
  { label: 'Cyan',      value: 'cyan',      hex: '#A5F3FC' },
  { label: 'Pink',      value: 'pink',      hex: '#FBCFE8' },
  { label: 'Blue',      value: 'blue',      hex: '#BFDBFE' },
  { label: 'Red',       value: 'red',       hex: '#FECACA' },
]

const SelectionToolbar = ({
  selectedTexts,
  position,
  onApply,
  onClose,
  loading
}) => {
  const [customPrompt, setCustomPrompt]   = useState('')
  const [showCustom, setShowCustom]       = useState(false)
  const [showHighlights, setShowHighlights] = useState(false)

  if (!selectedTexts || selectedTexts.length === 0) return null

  const handleQuickAction = (action) => {
    const params = {
      selected_texts: selectedTexts,
      command_type:   action.command_type,
      ...(action.extra || {})
    }
    onApply({ type: 'apply_to_selection', params })
  }

  const handleHighlightColor = (colorValue) => {
    onApply({
      type: 'apply_to_selection',
      params: {
        selected_texts:  selectedTexts,
        command_type:    'highlight',
        highlight_color: colorValue,
      }
    })
    setShowHighlights(false)
  }

  const handleCustomPrompt = (e) => {
    e.preventDefault()
    if (!customPrompt.trim()) return
    const selectionContext = selectedTexts
      .slice(0, 3)
      .map(t => `"${t.slice(0, 50)}"`)
      .join(', ')
    const fullCommand = `For the selected text ${selectionContext} — ${customPrompt}`
    onApply({
      type:           'custom_command',
      command:        fullCommand,
      selected_texts: selectedTexts
    })
    setCustomPrompt('')
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

      {/* Quick action buttons */}
      <div className="selection-toolbar__actions">
        {QUICK_ACTIONS.map((action, idx) => (
          action.command_type === 'highlight' ? (
            <div key={idx} style={{ position: 'relative' }}>
              <button
                className="selection-toolbar__btn"
                onClick={() => setShowHighlights(!showHighlights)}
                disabled={loading}
                title="Highlight color"
              >
                <action.icon size={13} />
                <span>{action.label}</span>
              </button>
              {showHighlights && (
                <div className="selection-toolbar__color-picker">
                  {HIGHLIGHT_COLORS.map(c => (
                    <button
                      key={c.value}
                      className="selection-toolbar__color-swatch"
                      style={{ background: c.hex }}
                      onClick={() => handleHighlightColor(c.value)}
                      title={c.label}
                    />
                  ))}
                </div>
              )}
            </div>
          ) : (
            <button
              key={idx}
              className="selection-toolbar__btn"
              onClick={() => handleQuickAction(action)}
              disabled={loading}
              title={action.label}
            >
              <action.icon size={13} />
              <span>{action.label}</span>
            </button>
          )
        ))}
      </div>

      {/* Font size quick row */}
      <div className="selection-toolbar__font-row">
        <span className="selection-toolbar__font-label">Font size:</span>
        {[10, 11, 12, 14, 16, 18, 24].map(size => (
          <button
            key={size}
            className="selection-toolbar__font-btn"
            onClick={() => onApply({
              type: 'apply_to_selection',
              params: {
                selected_texts: selectedTexts,
                command_type:   'font',
                font_size:      size,
              }
            })}
            disabled={loading}
          >
            {size}
          </button>
        ))}
      </div>

      {/* Custom prompt */}
      <button
        className="selection-toolbar__custom-toggle"
        onClick={() => setShowCustom(!showCustom)}
      >
        <ChevronDown
          size={12}
          style={{
            transform: showCustom ? 'rotate(180deg)' : 'none',
            transition: '0.2s'
          }}
        />
        Custom command
      </button>

      {showCustom && (
        <form className="selection-toolbar__custom" onSubmit={handleCustomPrompt}>
          <input
            className="selection-toolbar__input"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="e.g. make font Times New Roman, color red..."
            autoFocus
          />
          <button
            type="submit"
            className="selection-toolbar__send"
            disabled={!customPrompt.trim() || loading}
          >
            <Send size={12} />
          </button>
        </form>
      )}

      {/* Selected text preview */}
      <div className="selection-toolbar__preview">
        {selectedTexts.slice(0, 2).map((t, i) => (
          <div key={i} className="selection-toolbar__preview-item">
            "{t.slice(0, 60)}{t.length > 60 ? '...' : ''}"
          </div>
        ))}
        {selectedTexts.length > 2 && (
          <div className="selection-toolbar__preview-more">
            +{selectedTexts.length - 2} more selected
          </div>
        )}
      </div>
    </div>
  )
}

export default SelectionToolbar