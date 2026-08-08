import { useEffect, useState, useCallback } from 'react'
import Sidebar from './components/Sidebar.jsx'
import ChatWindow from './components/ChatWindow.jsx'
import { uploadDocument, listDocuments, sendChatMessage } from './api.js'

export default function App() {
  const [documents, setDocuments] = useState([])
  const [loadingDocuments, setLoadingDocuments] = useState(true)
  const [selectedDocId, setSelectedDocId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isSending, setIsSending] = useState(false)
  const [uploadState, setUploadState] = useState({ status: 'idle', message: '' })

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch (err) {
      console.error('Failed to load documents:', err)
    } finally {
      setLoadingDocuments(false)
    }
  }, [])

  useEffect(() => {
    refreshDocuments()
  }, [refreshDocuments])

  async function handleUpload(file) {
    setUploadState({ status: 'uploading', message: '' })
    try {
      await uploadDocument(file)
      setUploadState({ status: 'idle', message: '' })
      await refreshDocuments()
    } catch (err) {
      setUploadState({ status: 'error', message: err.message })
    }
  }

  async function handleSend(question) {
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setIsSending(true)
    try {
      const result = await sendChatMessage(question, selectedDocId)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: result.answer, sources: result.sources },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: err.message, isError: true },
      ])
    } finally {
      setIsSending(false)
    }
  }

  const selectedDoc = documents.find((d) => d.id === selectedDocId)

  return (
    <div className="app-shell">
      <Sidebar
        documents={documents}
        loadingDocuments={loadingDocuments}
        selectedDocId={selectedDocId}
        onSelectDoc={(id) => {
          setSelectedDocId(id)
          setMessages([])
        }}
        onUpload={handleUpload}
        uploadState={uploadState}
      />
      <ChatWindow
        messages={messages}
        onSend={handleSend}
        isSending={isSending}
        selectedDocName={selectedDoc?.filename}
      />
    </div>
  )
}
