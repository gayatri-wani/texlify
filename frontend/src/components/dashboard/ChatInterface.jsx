import { useState, useRef, useEffect } from 'react'
import {
  Send, Bot, User, Loader, Sparkles,
  RotateCcw, Image as ImageIcon
} from 'lucide-react'
import { documentService } from '../../services/documentService'
import ImageUpload from './ImageUpload'
import { toast } from 'react-hot-toast'
import './ChatInterface.css'

const EXAMPLE_COMMANDS = [
  'Make all headings bold and underlined',
  'Add page numbers at the bottom right',
  'Insert a table of contents at the beginning',
  'Replace all "AI" with "Artificial Intelligence"',
  'Add a watermark that says CONFIDENTIAL',
  'Apply SPPU format to the document',
  'Make all chapter titles start on a new page',
  'Highlight all headings in yellow',
  'Apply APA format',
  'Convert document to IEEE format',
  'Add a cover page with title My Report',
  'Set font to Times New Roman 12pt for body text',
]

const DOWNLOAD_KEYWORDS = [
  'give me', 'download', 'get document', 'modified document',
  'save document', 'export document', 'get file', 'send me'
]

const ChatInterface = ({ document, onSendCommand, loading, onCommandSuccess }) => {
  const [input, setInput]             = useState('')
  const [messages, setMessages]       = useState([])
  const [showImageUpload, setShowImageUpload] = useState(false)
  const bottomRef                     = useRef()
  const textareaRef                   = useRef()

  useEffect(() => {
    setMessages([{
      id: Date.now(), role: 'assistant',
      text: document
        ? `Document **${document.title}** is ready. What would you like to do?\n\nType any editing command and I'll apply it instantly. The preview updates after each change.`
        : 'Please select or upload a document to get started.',
      timestamp: new Date(),
    }])
  }, [document?.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleInput = (e) => {
    setInput(e.target.value)
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
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    // Intercept download commands
    const isDownload = DOWNLOAD_KEYWORDS.some(kw => text.toLowerCase().includes(kw))
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
      const successCount = result?.actions_performed?.filter(a => a.status === 'success').length || 0
      const errorCount   = result?.actions_performed?.filter(a => a.status === 'error').length || 0

      let responseText = result?.message || 'Done!'
      if (errorCount > 0) {
        responseText += `\n\n⚠️ ${errorCount} action(s) had issues.`
      } else {
        responseText += '\n\n✅ Preview updated on the right →'
      }

      setMessages(prev => prev.map(m =>
        m.id === thinkingId
          ? { ...m, thinking: false, text: responseText }
          : m
      ))
      if (onCommandSuccess) onCommandSuccess()
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Something went wrong.'
      setMessages(prev => prev.map(m =>
        m.id === thinkingId
          ? { ...m, thinking: false, text: `❌ ${detail}`, error: true }
          : m
      ))
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); sendMessage(input)
    }
  }

  const handleImageUploaded = (serverPath, filename) => {
    const command = `Insert image from path ${serverPath} with width 4 inches centered`
    sendMessage(command)
    toast.success(`Image "${filename}" will be inserted`)
  }

  const formatTime = (date) =>
    new Date(date).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })

  const renderText = (text) =>
    text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>')

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
        <button className="chat__clear-btn" onClick={resetChat} title="Clear chat">
          <RotateCcw size={14} />
        </button>
      </div>

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
                ? 'Type a command... (Enter to send, Shift+Enter for new line)'
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
          <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line · 📎 image button to insert images
        </p>
      </div>

    </div>
  )
}

export default ChatInterface