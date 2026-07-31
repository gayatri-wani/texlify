import { useState, useRef, useEffect } from 'react'
import {
  Send, Bot, User, Loader, Sparkles,
  RotateCcw, Keyboard
} from 'lucide-react'
import { useCommandSuggestions } from '../../hooks/useCommandSuggestions'
import './ChatInterface.css'

const ChatInterface = ({
  document,
  onSendCommand,
  loading,
  onCommandSuccess
}) => {
  const [input, setInput]       = useState('')
  const [messages, setMessages] = useState([])
  const [history, setHistory]   = useState([])
  const [historyIdx, setHistoryIdx] = useState(-1)
  const [showShortcuts, setShowShortcuts] = useState(false)
  const bottomRef               = useRef()
  const textareaRef             = useRef()
  const suggestions             = useCommandSuggestions(input)
  const [showSuggestions, setShowSuggestions] = useState(false)

  useEffect(() => {
    setMessages([{
      id: Date.now(), role: 'assistant',
      text: document
        ? `**${document.title}** is ready to edit.\n\nType any formatting command below. The preview on the right updates after every command.`
        : 'Select or upload a document to get started.',
      timestamp: new Date(),
    }])
  }, [document?.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    setShowSuggestions(input.trim().length >= 2 && suggestions.length > 0)
  }, [input, suggestions])

  const handleInput = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
    setHistoryIdx(-1)
  }

  const sendMessage = async (text) => {
    if (!text.trim() || !document || loading) return
    setShowSuggestions(false)
    const userMsg = {
      id: Date.now(), role: 'user',
      text: text.trim(), timestamp: new Date()
    }
    setMessages(prev => [...prev, userMsg])
    setHistory(prev => [text.trim(), ...prev.slice(0, 49)])
    setHistoryIdx(-1)
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    const thinkingId = Date.now() + 1
    setMessages(prev => [...prev, {
      id: thinkingId, role: 'assistant',
      text: '', thinking: true, timestamp: new Date()
    }])

    try {
      const result = await onSendCommand(document.id, text.trim())
      const errCount = result?.actions_performed?.filter(
        a => a.status === 'error').length || 0
      let responseText = result?.message || 'Done!'
      if (errCount > 0) {
        responseText += `\n\n⚠️ ${errCount} action(s) had issues.`
      } else {
        responseText += '\n\n✅ Preview updated →'
      }
      setMessages(prev => prev.map(m =>
        m.id === thinkingId
          ? { ...m, thinking: false, text: responseText, success: errCount === 0 }
          : m
      ))
      if (onCommandSuccess) onCommandSuccess()
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Something went wrong.'
      const isRate = err?.response?.status === 429
      setMessages(prev => prev.map(m =>
        m.id === thinkingId
          ? { ...m, thinking: false,
              text: isRate ? `⏱️ ${detail}` : `❌ ${detail}`,
              error: true }
          : m
      ))
    }
  }

  const handleKeyDown = (e) => {
    if (showSuggestions) {
      if (e.key === 'Tab' || e.key === 'ArrowDown') {
        e.preventDefault()
        return
      }
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
      return
    }
    if (e.key === 'ArrowUp' && !input) {
      e.preventDefault()
      const newIdx = Math.min(historyIdx + 1, history.length - 1)
      setHistoryIdx(newIdx)
      setInput(history[newIdx] || '')
    }
    if (e.key === 'ArrowDown' && historyIdx >= 0) {
      e.preventDefault()
      const newIdx = historyIdx - 1
      setHistoryIdx(newIdx)
      setInput(newIdx >= 0 ? history[newIdx] : '')
    }
    if (e.key === 'Escape') setShowSuggestions(false)
  }

  const renderText = (text) =>
    text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>')

  const formatTime = (date) =>
    new Date(date).toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit'
    })

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
        <div style={{ display:'flex', gap:6 }}>
          <button
            className="chat__icon-btn"
            onClick={() => setShowShortcuts(!showShortcuts)}
            title="Keyboard shortcuts"
          >
            <Keyboard size={14} />
          </button>
          <button
            className="chat__icon-btn"
            title="Clear chat"
            onClick={() => setMessages([{
              id: Date.now(), role: 'assistant',
              text: document
                ? `**${document.title}** is ready.`
                : 'Select a document.',
              timestamp: new Date()
            }])}
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </div>

      {/* Shortcuts panel */}
      {showShortcuts && (
        <div className="chat__shortcuts">
          <p className="chat__shortcuts-title">Keyboard Shortcuts</p>
          <div className="chat__shortcuts-list">
            {[
              ['Enter',       'Send command'],
              ['Shift+Enter', 'New line'],
              ['↑ / ↓',       'Command history'],
              ['Esc',         'Close suggestions'],
              ['Tab',         'Select suggestion'],
            ].map(([key, desc]) => (
              <div key={key} className="chat__shortcut">
                <kbd className="chat__kbd">{key}</kbd>
                <span>{desc}</span>
              </div>
            ))}
          </div>
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
              msg.error   ? 'chat__message--error'   : '',
              msg.success ? 'chat__message--success' : '',
            ].filter(Boolean).join(' ')}
          >
            <div className="chat__avatar">
              {msg.role === 'assistant'
                ? <Bot size={13} /> : <User size={13} />}
            </div>
            <div className="chat__bubble">
              {msg.thinking ? (
                <div className="chat__thinking">
                  <span /><span /><span />
                </div>
              ) : (
                <>
                  <p className="chat__bubble-text"
                    dangerouslySetInnerHTML={{ __html: renderText(msg.text) }}
                  />
                  <span className="chat__bubble-time">
                    {formatTime(msg.timestamp)}
                  </span>
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
          <p className="chat__examples-label">Try these</p>
          <div className="chat__examples-list">
            {[
              'Make all headings bold',
              'Apply SPPU format',
              'Add table of contents',
              'Set font Times New Roman 12pt',
              'Add page numbers bottom right',
              'Apply IEEE format',
            ].map((cmd, i) => (
              <button key={i} className="chat__example-chip"
                onClick={() => sendMessage(cmd)}>
                {cmd}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="chat__input-area">
        <div className={`chat__input-container ${!document ? 'chat__input-container--disabled' : ''}`}>
          <textarea
            ref={textareaRef}
            className="chat__input"
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            onFocus={() => input.length >= 2 && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            placeholder={
              document
                ? 'Type a command... (Enter to send)'
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
              ? <Loader size={15} className="animate-spin" />
              : <Send size={15} />}
          </button>
        </div>

        {/* Autocomplete */}
        {showSuggestions && (
          <div className="chat__suggestions">
            {suggestions.map((s, i) => (
              <button
                key={i}
                className="chat__suggestion"
                onMouseDown={() => { setInput(s); setShowSuggestions(false) }}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <p className="chat__input-hint">
          <kbd>Enter</kbd> send · <kbd>Shift+Enter</kbd> new line ·
          <kbd>↑↓</kbd> history
        </p>
      </div>
    </div>
  )
}

export default ChatInterface