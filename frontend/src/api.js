// Central place for every call to the backend. Keeping this in one
// file means if the backend URL or an endpoint path changes, there's
// exactly one place to update it, rather than hunting through every
// component that happens to fetch something.

const BASE_URL = 'http://127.0.0.1:8000'

async function handleResponse(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const message = body.detail || `Request failed with status ${res.status}`
    throw new Error(message)
  }
  return res.json()
}

export async function uploadDocument(file, force = false) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${BASE_URL}/upload?force=${force}`, {
    method: 'POST',
    body: formData,
  })
  return handleResponse(res)
}

export async function listDocuments() {
  const res = await fetch(`${BASE_URL}/documents`)
  return handleResponse(res)
}

export async function sendChatMessage(question, documentId = null) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, document_id: documentId }),
  })
  return handleResponse(res)
}

export async function getChatHistory() {
  const res = await fetch(`${BASE_URL}/chat/history`)
  return handleResponse(res)
}
