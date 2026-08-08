import SourceCard from './SourceCard.jsx'

export default function Message({ role, content, sources, isError }) {
  if (role === 'user') {
    return (
      <div className="message message-user">
        <div className="message-bubble message-bubble-user">{content}</div>
      </div>
    )
  }

  return (
    <div className="message message-assistant">
      <div className={`message-bubble message-bubble-assistant ${isError ? 'message-bubble-error' : ''}`}>
        {content}
      </div>
      {sources && sources.length > 0 && (
        <div className="sources">
          <div className="sources-label">Grounded in</div>
          <div className="sources-list">
            {sources.map((s, i) => (
              <SourceCard key={`${s.document_id}-${i}`} source={s} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
