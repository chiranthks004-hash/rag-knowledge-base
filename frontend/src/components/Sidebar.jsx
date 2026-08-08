import { useRef, useState } from 'react'

const STATUS_LABEL = {
  ready: 'Ready',
  processing: 'Processing',
  failed: 'Failed',
}

export default function Sidebar({
  documents,
  loadingDocuments,
  selectedDocId,
  onSelectDoc,
  onUpload,
  uploadState,
}) {
  const fileInputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)

  function handleFiles(files) {
    if (files && files[0]) onUpload(files[0])
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-mark">§</span>
        <h1 className="sidebar-title">Knowledge Base</h1>
      </div>

      <div
        className={`dropzone ${dragOver ? 'dropzone-active' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          handleFiles(e.dataTransfer.files)
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          hidden
          onChange={(e) => handleFiles(e.target.files)}
        />
        <span className="dropzone-label">
          {uploadState.status === 'uploading' ? 'Uploading…' : 'Drop a PDF, or click to browse'}
        </span>
      </div>

      {uploadState.status === 'error' && (
        <div className="upload-error">{uploadState.message}</div>
      )}

      <div className="doc-list-header">
        <span>Documents</span>
        <span className="doc-count">{documents.length}</span>
      </div>

      <div className="doc-list">
        {loadingDocuments && <p className="muted">Loading…</p>}
        {!loadingDocuments && documents.length === 0 && (
          <p className="muted">No documents yet. Upload a PDF to get started.</p>
        )}

        <button
          className={`doc-item doc-item-all ${selectedDocId === null ? 'doc-item-selected' : ''}`}
          onClick={() => onSelectDoc(null)}
        >
          All documents
        </button>

        {documents.map((doc) => (
          <button
            key={doc.id}
            className={`doc-item ${selectedDocId === doc.id ? 'doc-item-selected' : ''}`}
            onClick={() => onSelectDoc(doc.id)}
            disabled={doc.status !== 'ready'}
            title={doc.filename}
          >
            <span className="doc-item-name">{doc.filename}</span>
            <span className={`doc-status doc-status-${doc.status}`}>
              {STATUS_LABEL[doc.status] || doc.status}
            </span>
          </button>
        ))}
      </div>
    </aside>
  )
}
