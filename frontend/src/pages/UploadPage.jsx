import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadFile, getDocumentStatus } from '../services/api'

function UploadPage() {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState(null)
  const [documentId, setDocumentId] = useState(null)
  const fileInputRef = useRef(null)
  const navigate = useNavigate()

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
          setStatus('ready')
        } else if (data.status === 'error') {
          clearInterval(interval)
          setStatus('error')
          setError('Processing failed. Please try again.')
        }
      } catch (err) {
        clearInterval(interval)
        setStatus('error')
        setError('Could not check processing status.')
      }
    }, 2000)
  }

  const handleUpload = async () => {
    if (!file) return
    setStatus('uploading')
    setError(null)
    try {
      const data = await uploadFile(file)
      setDocumentId(data.document_id)
      setStatus('processing')
      pollStatus(data.document_id)
    } catch (err) {
      setStatus('error')
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    }
  }

  const handleNavigate = (page) => {
    localStorage.setItem('documentId', documentId)
    navigate(`/${page}`)
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-800 mb-2">Upload Notes</h1>
      <p className="text-gray-500 mb-8">
        Upload your lecture notes or textbook chapters to get started.
      </p>

      {status === 'idle' || status === 'error' ? (
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

          {error && (
            <p className="mt-3 text-red-500 text-sm">{error}</p>
          )}

          <button
            onClick={handleUpload}
            disabled={!file}
            className="mt-6 w-full py-3 px-6 bg-blue-600 text-white rounded-lg font-medium
              hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Upload and Process
          </button>
        </>
      ) : status === 'uploading' || status === 'processing' ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="text-4xl mb-4 animate-spin">⚙️</div>
          <p className="text-gray-800 font-medium mb-1">
            {status === 'uploading' ? 'Uploading your file...' : 'Processing your notes...'}
          </p>
          <p className="text-gray-400 text-sm">
            {status === 'processing' && 'Extracting text and generating embeddings. This takes about 10 seconds.'}
          </p>
        </div>
      ) : status === 'ready' ? (
        <div className="bg-white rounded-xl border border-gray-200 p-8">
          <div className="text-center mb-8">
            <div className="text-4xl mb-3">✅</div>
            <p className="text-gray-800 font-medium text-lg">Notes processed successfully</p>
            <p className="text-gray-400 text-sm mt-1">{file.name}</p>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <button
              onClick={() => handleNavigate('flashcards')}
              className="py-4 px-4 bg-blue-50 hover:bg-blue-100 rounded-xl text-center transition-colors"
            >
              <div className="text-2xl mb-2">🃏</div>
              <p className="text-blue-700 font-medium text-sm">Generate Flashcards</p>
            </button>
            <button
              onClick={() => handleNavigate('chat')}
              className="py-4 px-4 bg-purple-50 hover:bg-purple-100 rounded-xl text-center transition-colors"
            >
              <div className="text-2xl mb-2">💬</div>
              <p className="text-purple-700 font-medium text-sm">Chat with Notes</p>
            </button>
            <button
              onClick={() => handleNavigate('quiz')}
              className="py-4 px-4 bg-green-50 hover:bg-green-100 rounded-xl text-center transition-colors"
            >
              <div className="text-2xl mb-2">🧠</div>
              <p className="text-green-700 font-medium text-sm">Start Quiz</p>
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default UploadPage