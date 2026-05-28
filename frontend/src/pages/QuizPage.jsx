import { useState, useEffect } from 'react'
import { getDueCards, rateCard, generateFlashcards } from '../services/api'

function QuizPage() {
  const [documentId] = useState(() => localStorage.getItem('documentId'))
  const [cards, setCards] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [status, setStatus] = useState('idle')
  const [sessionStats, setSessionStats] = useState({ reviewed: 0, correct: 0 })
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!documentId) return
    loadDueCards()
  }, [documentId])

  const loadDueCards = async () => {
    setStatus('loading')
    try {
      const data = await getDueCards(documentId)
      if (data.cards.length === 0) {
        setStatus('done')
      } else {
        setCards(data.cards)
        setStatus('ready')
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setStatus('no-flashcards')
      } else {
        setError('Failed to load due cards.')
        setStatus('error')
      }
    }
  }

  const handleRate = async (rating) => {
    const card = cards[currentIndex]
    try {
      await rateCard(card.flashcard_id, rating)
      setSessionStats(prev => ({
        reviewed: prev.reviewed + 1,
        correct: rating >= 3 ? prev.correct + 1 : prev.correct
      }))

      if (currentIndex + 1 >= cards.length) {
        setStatus('session-complete')
      } else {
        setFlipped(false)
        setTimeout(() => setCurrentIndex(i => i + 1), 150)
      }
    } catch (err) {
      setError('Failed to save rating.')
    }
  }

  const handleGenerateAndLoad = async () => {
    setStatus('generating')
    try {
      await generateFlashcards(documentId)
      await loadDueCards()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate flashcards.')
      setStatus('no-flashcards')
    }
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
          {status === 'generating' ? 'Generating flashcards...' : 'Loading your cards...'}
        </p>
      </div>
    )
  }

  if (status === 'no-flashcards') {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-800 mb-8">Quiz</h1>
        {error && <p className="mb-4 text-red-500 text-sm">{error}</p>}
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="text-4xl mb-4">🧠</div>
          <p className="text-gray-600 font-medium mb-2">No flashcards yet</p>
          <p className="text-gray-400 text-sm mb-6">
            Generate flashcards from your notes to start quizzing.
          </p>
          <button
            onClick={handleGenerateAndLoad}
            className="py-3 px-8 bg-blue-600 text-white rounded-lg font-medium
              hover:bg-blue-700 transition-colors"
          >
            Generate Flashcards
          </button>
        </div>
      </div>
    )
  }

  if (status === 'done') {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-800 mb-8">Quiz</h1>
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="text-4xl mb-4">🎉</div>
          <p className="text-gray-800 font-medium text-lg mb-2">You're all caught up!</p>
          <p className="text-gray-400 text-sm">No cards are due for review today.</p>
        </div>
      </div>
    )
  }

  if (status === 'session-complete') {
    const accuracy = Math.round((sessionStats.correct / sessionStats.reviewed) * 100)
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-800 mb-8">Quiz</h1>
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="text-4xl mb-4">✅</div>
          <p className="text-gray-800 font-medium text-lg mb-6">Session complete</p>
          <div className="flex justify-center gap-12 mb-8">
            <div>
              <p className="text-3xl font-semibold text-gray-800">{sessionStats.reviewed}</p>
              <p className="text-gray-400 text-sm mt-1">Cards reviewed</p>
            </div>
            <div>
              <p className="text-3xl font-semibold text-green-600">{accuracy}%</p>
              <p className="text-gray-400 text-sm mt-1">Accuracy</p>
            </div>
            <div>
              <p className="text-3xl font-semibold text-gray-800">{sessionStats.correct}</p>
              <p className="text-gray-400 text-sm mt-1">Correct</p>
            </div>
          </div>
          <button
            onClick={() => {
              setCurrentIndex(0)
              setFlipped(false)
              setSessionStats({ reviewed: 0, correct: 0 })
              loadDueCards()
            }}
            className="py-3 px-8 bg-blue-600 text-white rounded-lg font-medium
              hover:bg-blue-700 transition-colors"
          >
            Study Again
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

  const card = cards[currentIndex]
  const progress = ((currentIndex) / cards.length) * 100

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">Quiz</h1>
        <span className="text-gray-400 text-sm">
          {currentIndex + 1} / {cards.length} due today
        </span>
      </div>

      <div className="w-full bg-gray-100 rounded-full h-1.5 mb-6">
        <div
          className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div
        onClick={() => setFlipped(f => !f)}
        className="bg-white rounded-xl border border-gray-200 p-12 text-center
          cursor-pointer hover:border-gray-300 transition-colors min-h-64
          flex items-center justify-center mb-6"
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

      {flipped && (
        <div>
          <p className="text-center text-gray-500 text-sm mb-4">How well did you know this?</p>
          <div className="grid grid-cols-4 gap-3">
            <button
              onClick={() => handleRate(1)}
              className="py-3 rounded-xl bg-red-50 hover:bg-red-100
                text-red-600 font-medium text-sm transition-colors"
            >
              😕 Forgot
            </button>
            <button
              onClick={() => handleRate(3)}
              className="py-3 rounded-xl bg-orange-50 hover:bg-orange-100
                text-orange-600 font-medium text-sm transition-colors"
            >
              😐 Hard
            </button>
            <button
              onClick={() => handleRate(4)}
              className="py-3 rounded-xl bg-blue-50 hover:bg-blue-100
                text-blue-600 font-medium text-sm transition-colors"
            >
              🙂 Good
            </button>
            <button
              onClick={() => handleRate(5)}
              className="py-3 rounded-xl bg-green-50 hover:bg-green-100
                text-green-600 font-medium text-sm transition-colors"
            >
              😄 Easy
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default QuizPage