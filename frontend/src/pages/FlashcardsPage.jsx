import { useState, useEffect } from 'react'
import { generateFlashcards, getFlashcards } from '../services/api'

function FlashcardsPage() {
  const [documentId] = useState(() => localStorage.getItem('documentId'))
  const [flashcards, setFlashcards] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!documentId) return
    loadFlashcards()
  }, [documentId])

  const loadFlashcards = async () => {
    setStatus('loading')
    try {
      const data = await getFlashcards(documentId)
      setFlashcards(data.flashcards)
      setStatus('ready')
    } catch (err) {
      if (err.response?.status === 404) {
        setStatus('empty')
      } else {
        setError('Failed to load flashcards.')
        setStatus('error')
      }
    }
  }

  const handleGenerate = async () => {
    setStatus('generating')
    setError(null)
    try {
      const data = await generateFlashcards(documentId)
      setFlashcards(data.flashcards)
      setStatus('ready')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate flashcards.')
      setStatus('empty')
    }
  }

  const handleNext = () => {
    setFlipped(false)
    setTimeout(() => setCurrentIndex(i => (i + 1) % flashcards.length), 150)
  }

  const handlePrev = () => {
    setFlipped(false)
    setTimeout(() => setCurrentIndex(i => (i - 1 + flashcards.length) % flashcards.length), 150)
  }

  if (!documentId) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">No document loaded. Please upload your notes first.</p>
      </div>
    )
  }

  if (status === 'idle' || status === 'loading' || status === 'generating') {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4 animate-spin">⚙️</div>
        <p className="text-gray-600 font-medium">
          {status === 'generating' ? 'Generating flashcards with AI...' : 'Loading flashcards...'}
        </p>
      </div>
    )
  }

  if (status === 'empty') {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-800 mb-2">Flashcards</h1>
        <p className="text-gray-500 mb-8">
          Generate flashcards from your uploaded notes using AI.
        </p>
        {error && <p className="mb-4 text-red-500 text-sm">{error}</p>}
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="text-4xl mb-4">🃏</div>
          <p className="text-gray-600 font-medium mb-6">
            No flashcards yet for this document.
          </p>
          <button
            onClick={handleGenerate}
            className="py-3 px-8 bg-blue-600 text-white rounded-lg font-medium
              hover:bg-blue-700 transition-colors"
          >
            Generate Flashcards
          </button>
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="text-center py-16">
        <p className="text-red-500">{error}</p>
      </div>
    )
  }

  const card = flashcards[currentIndex]

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-semibold text-gray-800">Flashcards</h1>
        <span className="text-gray-400 text-sm">
          {currentIndex + 1} / {flashcards.length}
        </span>
      </div>

      <div
        onClick={() => setFlipped(f => !f)}
        className="bg-white rounded-xl border border-gray-200 p-12 text-center
          cursor-pointer hover:border-gray-300 transition-colors min-h-64
          flex items-center justify-center"
      >
        <div>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-4">
            {flipped ? 'Answer' : 'Question'}
          </p>
          <p className="text-gray-800 text-lg leading-relaxed">
            {flipped ? card.answer : card.question}
          </p>
          {!flipped && (
            <p className="text-gray-400 text-sm mt-6">Click to reveal answer</p>
          )}
        </div>
      </div>

      <div className="flex justify-between mt-6">
        <button
          onClick={handlePrev}
          className="py-2 px-6 border border-gray-200 rounded-lg text-gray-600
            hover:bg-gray-50 transition-colors"
        >
          ← Previous
        </button>
        <button
          onClick={handleNext}
          className="py-2 px-6 border border-gray-200 rounded-lg text-gray-600
            hover:bg-gray-50 transition-colors"
        >
          Next →
        </button>
      </div>
    </div>
  )
}

export default FlashcardsPage