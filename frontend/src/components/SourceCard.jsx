export default function SourceCard({ source }) {
  return (
    <div className="source-card">
      <div className="source-highlight-bar" aria-hidden="true" />
      <div className="source-body">
        <span className="source-filename">{source.filename}</span>
      </div>
    </div>
  )
}
