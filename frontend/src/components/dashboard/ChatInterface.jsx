import { useState, useRef, useEffect } from 'react'
import {
  Send, Bot, User, Loader, Sparkles,
  RotateCcw, Image as ImageIcon, Keyboard
} from 'lucide-react'
import { documentService } from '../../services/documentService'
import ImageUpload from './ImageUpload'
import { useCommandSuggestions } from '../../hooks/useCommandSuggestions'
import { toast } from 'react-hot-toast'
import './ChatInterface.css'

const EXAMPLE_COMMANDS = [
  'Make all headings bold and underlined',
  'Add page numbers at the bottom right',
  'Insert a table of contents at the beginning',
  'Replace all "AI" with "Artificial Intelligence"',
  'Add a watermark that says CONFIDENTIAL',
  'Apply SPPU format to the document',
  'Highlight all headings in yellow',
  'Apply APA format',
  'Add a cover page with title My Report',
  'Set font to Times New Roman 12pt for body text',
  'Apply IEEE format',
  'Set line spacing to 1.5',
]

const DOWNLOAD_KEYWORDS = [
  'give me', 'download', 'get document', 'modified document',
  'save document', 'export document', 'get file', 'send me'
]

const SHORTCUTS = [
  { keys: 'Ctrl + Enter', action: 'Send command' },
  { keys: 'Escape',       action: 'Clear input'  },
  { keys: '↑ Arrow',      action: 'Previous command' },
  { keys: '↓ Arrow',      action: 'Next command' },
]

const ChatInterface = ({ document, onSendCommand, loading, onCommandSuccess }) => {
  const [input, setInput]               = useState('')
  const [messages, setMessages]         = useState([])
  const [showImageUpload, setShowImageUpload] = useState(false)
  const [showShortcuts, setShowShortcuts]     = useState(false)
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1)
  const [commandHistory, setCommandHistory]   = useState([])
  const [historyIndex, setHistoryIndex]       = useState(-1)
  const bottomRef   = useRef()
  const textareaRef = useRef()

  const suggestions = useCommandSuggestions(input)

  useEffect(() => {
    setMessages([{
      id: Date.now(), role: 'assistant',
      text: document
        ? `Document **${document.title}** is ready. What would you like to do?\n\nType any editing command — suggestions will appear as you type.`
        : 'Please select or upload a document to get started.',
      timestamp: new Date(),
    }])
    setCommandHistory([])
    setHistoryIndex(-1)
  }, [document?.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Reset suggestion selection when suggestions change
  useEffect(() => {
    setSelectedSuggestion(-1)
  }, [suggestions.length])

  const handleInput = (e) => {
    setInput(e.target.value)
    setHistoryIndex(-1)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const sendMessage = async (text) => {
    if (!text.trim() || !document || loading) return

    const userMsg = {
      id: Date.now(), role: 'user',
      text: text.trim(), timestamp: new Date()
    }
    setMessages(prev => [...prev, userMsg])

    // Save to local command history for ↑↓ navigation
    setCommandHistory(prev => [text.trim(), ...prev.slice(0, 49)])
    setHistoryIndex(-1)

    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    // Intercept download commands
    const isDownload = DOWNLOAD_KEYWORDS.some(
      kw => text.toLowerCase().includes(kw))
    if (isDownload) {
      try {
        await documentService.download(document.id, document.original_filename)
        setMessages(prev => [...prev, {
          id: Date.now(), role: 'assistant',
          text: '✅ Your modified document is downloading now!',
          timestamp: new Date()
        }])
      } catch {
        setMessages(prev => [...prev, {
          id: Date.now(), role: 'assistant',
          text: 'Download failed. Use the Download button in the preview panel.',
          error: true, timestamp: new Date()
        }])
      }
      return
    }

    // Thinking indicator
    const thinkingId = Date.now() + 1
    setMessages(prev => [...prev, {
      id: thinkingId, role: 'assistant',
      text: '', thinking: true, timestamp: new Date()
    }])

    try {
      const result = await onSendCommand(document.id, text.trim())
      const successCount = result?.actions_performed
        ?.filter(a => a.status === 'success').length || 0
      const errorCount = result?.actions_performed
        ?.filter(a => a.status === 'error').length || 0
      const skippedCount = result?.actions_performed
        ?.filter(a => a.status === 'skipped').length || 0

      let responseText = result?.message || 'Done!'
      if (errorCount > 0 && successCount === 0) {
        responseText = `❌ Command failed. ${result?.actions_performed?.[0]?.error || 'Please try rephrasing.'}`
      } else if (errorCount > 0) {
        responseText += `\n\n⚠️ ${errorCount} action(s) had issues, ${successCount} succeeded.`
      } else if (skippedCount > 0 && successCount === 0) {
        responseText = `⚠️ No matching content found. Make sure your document has the content you are referring to.`
      } else {
        responseText += '\n\n✅ Preview updated on the right →'
      }

      setMessages(prev => prev.map(m =>
        m.id === thinkingId
          ? { ...m, thinking: false, text: responseText,
              actions: result?.actions_performed }
          : m
      ))
      if (onCommandSuccess) onCommandSuccess()
    } catch (err) {
      let detail = 'Something went wrong. Please try again.'
      if (err?.response?.status === 429) {
        detail = '⏱️ Too many commands. Please wait a moment before sending another.'
      } else if (err?.response?.status === 422) {
        detail = `❌ Could not understand that command. Try rephrasing it more clearly.`
      } else if (err?.response?.data?.detail) {
        detail = `❌ ${err.response.data.detail}`
      }
      setMessages(prev => prev.map(m =>
        m.id === thinkingId
          ? { ...m, thinking: false, text: detail, error: true }
          : m
      ))
    }
  }

  const handleKeyDown = (e) => {
    // Suggestion navigation
    if (suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedSuggestion(prev =>
          prev < suggestions.length - 1 ? prev + 1 : 0)
        return
      }
      if (e.key === 'ArrowUp' && selectedSuggestion >= 0) {
        e.preventDefault()
        setSelectedSuggestion(prev => prev > 0 ? prev - 1 : -1)
        return
      }
      if (e.key === 'Tab' || (e.key === 'Enter' && selectedSuggestion >= 0)) {
        e.preventDefault()
        const chosen = suggestions[selectedSuggestion] || suggestions[0]
        setInput(chosen)
        setSelectedSuggestion(-1)
        textareaRef.current?.focus()
        return
      }
      if (e.key === 'Escape') {
        setSelectedSuggestion(-1)
        return
      }
    }

    // Command history navigation (↑↓ when no suggestions)
    if (suggestions.length === 0) {
      if (e.key === 'ArrowUp' && commandHistory.length > 0) {
        e.preventDefault()
        const newIndex = Math.min(historyIndex + 1, commandHistory.length - 1)
        setHistoryIndex(newIndex)
        setInput(commandHistory[newIndex])
        return
      }
      if (e.key === 'ArrowDown' && historyIndex > 0) {
        e.preventDefault()
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setInput(newIndex >= 0 ? commandHistory[newIndex] : '')
        return
      }
    }

    // Send on Enter (not Shift+Enter)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }

    // Clear on Escape
    if (e.key === 'Escape') {
      setInput('')
      if (textareaRef.current) textareaRef.current.style.height = 'auto'
    }
  }

  const handleImageUploaded = (serverPath, filename) => {
    const command = `Insert image from path ${serverPath} with width 4 inches centered`
    sendMessage(command)
    toast.success(`Image "${filename}" will be inserted`)
  }

  const formatTime = (date) =>
    new Date(date).toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit'
    })

  const renderText = (text) =>
    text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>')

  const resetChat = () => {
    setMessages([{
      id: Date.now(), role: 'assistant',
      text: document
        ? `Document **${document.title}** is ready. What would you like to do?`
        : 'Select a document.',
      timestamp: new Date()
    }])
  }

  return (
    <div className="chat">

      {/* Header */}
      <div className="chat__header">
        <div className="chat__header-left">
          <div className="chat__header-icon"><Sparkles size={16} /></div>
          <div>
            <h3 className="chat__header-title">AI Document Agent</h3>
            <p className="chat__header-subtitle">
              {document ? `Editing: ${document.title}` : 'No document selected'}
            </p>
          </div>
        </div>
        <div className="chat__header-actions">
          <button
            className="chat__icon-btn"
            onClick={() => setShowShortcuts(!showShortcuts)}
            title="Keyboard shortcuts"
          >
            <Keyboard size={14} />
          </button>
          <button
            className="chat__icon-btn"
            onClick={resetChat}
            title="Clear chat"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </div>

      {/* Keyboard shortcuts panel */}
      {showShortcuts && (
        <div className="chat__shortcuts">
          <p className="chat__shortcuts-title">Keyboard Shortcuts</p>
          {SHORTCUTS.map((s, i) => (
            <div key={i} className="chat__shortcut">
              <kbd>{s.keys}</kbd>
              <span>{s.action}</span>
            </div>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="chat__messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={[
              'chat__message',
              `chat__message--${msg.role}`,
              msg.error ? 'chat__message--error' : '',
            ].filter(Boolean).join(' ')}
          >
            <div className="chat__avatar">
              {msg.role === 'assistant' ? <Bot size={14} /> : <User size={14} />}
            </div>
            <div className="chat__bubble">
              {msg.thinking ? (
                <div className="chat__thinking">
                  <span /><span /><span />
                </div>
              ) : (
                <>
                  <p
                    className="chat__bubble-text"
                    dangerouslySetInnerHTML={{ __html: renderText(msg.text) }}
                  />
                  {/* Action results summary */}
                  {msg.actions && msg.actions.length > 0 && (
                    <div className="chat__actions-summary">
                      {msg.actions.filter(a => a.status === 'success').length > 0 && (
                        <span className="chat__actions-badge chat__actions-badge--success">
                          ✓ {msg.actions.filter(a => a.status === 'success').length} done
                        </span>
                      )}
                      {msg.actions.filter(a => a.status === 'error').length > 0 && (
                        <span className="chat__actions-badge chat__actions-badge--error">
                          ✗ {msg.actions.filter(a => a.status === 'error').length} failed
                        </span>
                      )}
                    </div>
                  )}
                  <span className="chat__bubble-time">{formatTime(msg.timestamp)}</span>
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Example chips */}
      {document && messages.length <= 2 && (
        <div className="chat__examples">
          <p className="chat__examples-label">Try these commands</p>
          <div className="chat__examples-list">
            {EXAMPLE_COMMANDS.slice(0, 6).map((cmd, i) => (
              <button
                key={i}
                className="chat__example-chip"
                onClick={() => sendMessage(cmd)}
              >
                {cmd}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Image upload panel */}
      {showImageUpload && (
        <div className="chat__image-upload-wrapper">
          <ImageUpload
            onImageUploaded={handleImageUploaded}
            onClose={() => setShowImageUpload(false)}
          />
        </div>
      )}

      {/* Autocomplete suggestions */}
      {suggestions.length > 0 && input.trim().length >= 2 && (
        <div className="chat__suggestions">
          {suggestions.map((suggestion, i) => (
            <button
              key={i}
              className={`chat__suggestion ${i === selectedSuggestion ? 'chat__suggestion--selected' : ''}`}
              onClick={() => {
                setInput(suggestion)
                setSelectedSuggestion(-1)
                textareaRef.current?.focus()
              }}
              onMouseEnter={() => setSelectedSuggestion(i)}
            >
              <Sparkles size={11} />
              <span>{suggestion}</span>
            </button>
          ))}
          <p className="chat__suggestions-hint">
            ↑↓ to navigate · Tab to select · Enter to send
          </p>
        </div>
      )}

      {/* Input area */}
      <div className="chat__input-area">
        <div className={`chat__input-container ${!document ? 'chat__input-container--disabled' : ''}`}>
          <button
            className="chat__image-btn"
            onClick={() => setShowImageUpload(!showImageUpload)}
            disabled={!document}
            title="Upload and insert an image"
          >
            <ImageIcon size={15} />
          </button>
          <textarea
            ref={textareaRef}
            className="chat__input"
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={
              document
                ? 'Type a command... suggestions appear as you type'
                : 'Select a document first'
            }
            disabled={!document || loading}
            rows={1}
          />
          <button
            className="chat__send-btn"
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || !document || loading}
          >
            {loading
              ? <Loader size={16} className="animate-spin" />
              : <Send size={16} />
            }
          </button>
        </div>
        <p className="chat__input-hint">
          <kbd>Enter</kbd> send ·
          <kbd>Tab</kbd> autocomplete ·
          <kbd>↑↓</kbd> history ·
          <kbd>Esc</kbd> clear
        </p>
      </div>

    </div>
  )
}

export default ChatInterface