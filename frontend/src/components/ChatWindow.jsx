import { useEffect, useRef, useState } from 'react'
import Message from './Message.jsx'
import TypingIndicator from './TypingIndicator.jsx'

export default function ChatWindow({ messages, onSend, isSending, selectedDocName }) {
  const [input, setInput] = useState('')
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isSending])

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || isSending) return
    onSend(trimmed)
    setInput('')
  }

  return (
    <main className="chat-window">
      <div className="chat-scope">
        {selectedDocName ? (
          <>
            Asking within <span className="chat-scope-name">{selectedDocName}</span>
          </>
        ) : (
          'Asking across all documents'
        )}
      </div>

      <div className="messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            <p className="empty-state-title">Ask something about your documents</p>
            <p className="empty-state-sub">
              Answers are generated only from what you've uploaded — grounded, cited, no guessing.
            </p>
          </div>
        )}

        {messages.map((m, i) => (
          <Message key={i} role={m.role} content={m.content} sources={m.sources} isError={m.isError} />
        ))}

        {isSending && <TypingIndicator />}
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <input
          className="composer-input"
          type="text"
          placeholder="Ask a question about your documents…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isSending}
        />
        <button className="composer-send" type="submit" disabled={isSending || !input.trim()}>
          Send
        </button>
      </form>
    </main>
  )
}
