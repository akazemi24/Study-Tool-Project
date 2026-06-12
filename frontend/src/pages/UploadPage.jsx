import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadFile, getDocumentStatus, getDocuments } from '../services/api'

function UploadPage() {
  const [documents, setDocuments] = useState([])
  const [selectedId, setSelectedId] = useState(() => localStorage.getItem('documentId'))
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('idle')
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const data = await getDocuments()
      setDocuments(data.documents)
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }

  const handleSelectDocument = (docId) => {
    setSelectedId(docId)
    localStorage.setItem('documentId', docId)
  }

  const handleFileSelect = (selectedFile) => {
    const allowed = ['application/pdf', 'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (!allowed.includes(selectedFile.type)) {
      setError('Please upload a PDF, TXT, or DOCX file.')
      return
    }
    setFile(selectedFile)
    setError(null)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) handleFileSelect(dropped)
  }

  const pollStatus = async (docId) => {
    const interval = setInterval(async () => {
      try {
        const data = await getDocumentStatus(docId)
        if (data.status === 'ready') {
          clearInterval(interval)
          setUploadStatus('ready')
          await loadDocuments()
          handleSelectDocument(docId)
          setFile(null)
        } else if (data.status === 'error') {
          clearInterval(interval)
          setUploadStatus('error')
          setError('Processing failed. Please try again.')
        }
      } catch (err) {
        clearInterval(interval)
        setUploadStatus('error')
        setError('Could not check processing status.')
      }
    }, 2000)
  }

  const handleUpload = async () => {
    if (!file) return
    setUploadStatus('uploading')
    setError(null)
    try {
      const data = await uploadFile(file)
      setUploadStatus('processing')
      pollStatus(data.document_id)
    } catch (err) {
      setUploadStatus('error')
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    }
  }

  const handleNavigate = (page) => {
    navigate(`/${page}`)
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric'
    })
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-800 mb-2">Documents</h1>
      <p className="text-gray-500 mb-8">
        Select a document to study or upload a new one.
      </p>

      {documents.length > 0 && (
        <div className="mb-8">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            Your Documents
          </h2>
          <div className="space-y-2">
            {documents.map(doc => (
              <div
                key={doc.id}
                onClick={() => handleSelectDocument(doc.id)}
                className={`flex items-center justify-between p-4 rounded-xl border cursor-pointer transition-colors ${
                  selectedId === doc.id
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">📄</span>
                  <div>
                    <p className="text-gray-800 font-medium text-sm">{doc.filename}</p>
                    <p className="text-gray-400 text-xs">{formatDate(doc.uploaded_at)}</p>
                  </div>
                </div>
                {selectedId === doc.id && (
                  <span className="text-blue-600 text-sm font-medium">Selected</span>
                )}
              </div>
            ))}
          </div>

          {selectedId && (
            <div className="grid grid-cols-3 gap-4 mt-6">
              <button
                onClick={() => handleNavigate('flashcards')}
                className="py-4 px-4 bg-blue-50 hover:bg-blue-100 rounded-xl text-center transition-colors"
              >
                <div className="text-2xl mb-2">🃏</div>
                <p className="text-blue-700 font-medium text-sm">Flashcards</p>
              </button>
              <button
                onClick={() => handleNavigate('chat')}
                className="py-4 px-4 bg-purple-50 hover:bg-purple-100 rounded-xl text-center transition-colors"
              >
                <div className="text-2xl mb-2">💬</div>
                <p className="text-purple-700 font-medium text-sm">Chat</p>
              </button>
              <button
                onClick={() => handleNavigate('quiz')}
                className="py-4 px-4 bg-green-50 hover:bg-green-100 rounded-xl text-center transition-colors"
              >
                <div className="text-2xl mb-2">🧠</div>
                <p className="text-green-700 font-medium text-sm">Quiz</p>
              </button>
            </div>
          )}
        </div>
      )}

      <div>
        <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
          Upload New Document
        </h2>

        {uploadStatus === 'uploading' || uploadStatus === 'processing' ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <div className="text-4xl mb-4 animate-spin">⚙️</div>
            <p className="text-gray-800 font-medium mb-1">
              {uploadStatus === 'uploading' ? 'Uploading...' : 'Processing your notes...'}
            </p>
            <p className="text-gray-400 text-sm">
              {uploadStatus === 'processing' && 'Extracting text and generating embeddings.'}
            </p>
          </div>
        ) : uploadStatus === 'ready' ? (
          <div className="bg-green-50 rounded-xl border border-green-200 p-6 text-center">
            <p className="text-green-700 font-medium">✅ Document processed and selected</p>
          </div>
        ) : (
          <>
            <div
              onClick={() => fileInputRef.current.click()}
              onDrop={handleDrop}
              onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
                dragging
                  ? 'border-blue-400 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400 bg-white'
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".pdf,.txt,.docx"
                onChange={(e) => handleFileSelect(e.target.files[0])}
              />
              <div className="text-4xl mb-4">📄</div>
              {file ? (
                <p className="text-gray-800 font-medium">{file.name}</p>
              ) : (
                <>
                  <p className="text-gray-600 font-medium mb-1">
                    Drop your file here or click to browse
                  </p>
                  <p className="text-gray-400 text-sm">PDF, DOCX, or TXT up to 10MB</p>
                </>
              )}
            </div>

            {error && <p className="mt-3 text-red-500 text-sm">{error}</p>}

            <button
              onClick={handleUpload}
              disabled={!file}
              className="mt-4 w-full py-3 px-6 bg-blue-600 text-white rounded-lg font-medium
                hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Upload and Process
            </button>
          </>
        )}
      </div>
    </div>
  )
}

export default UploadPage