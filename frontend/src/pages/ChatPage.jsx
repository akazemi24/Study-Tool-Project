import { useState, useRef, useEffect } from 'react'
import { askQuestion } from '../services/api'
import ReactMarkdown from 'react-markdown'

function ChatPage() {
  const [documentId] = useState(() => localStorage.getItem('documentId'))
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const question = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      const data = await askQuestion(documentId, question)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        similarity: data.top_similarity
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'error',
        content: err.response?.data?.detail || 'Something went wrong. Please try again.'
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!documentId) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">No document loaded. Please upload your notes first.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <h1 className="text-2xl font-semibold text-gray-800 mb-6">Chat with your Notes</h1>

      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-center py-16">
            <div className="text-4xl mb-4">💬</div>
            <p className="text-gray-500 font-medium mb-2">Ask anything about your notes</p>
            <p className="text-gray-400 text-sm">
              Answers are grounded in your uploaded document
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-2xl rounded-xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-blue-50 text-gray-800 border border-blue-200'
                  : message.role === 'error'
                  ? 'bg-red-50 text-red-600 border border-red-200'
                  : 'bg-white text-gray-800 border border-gray-200'
              }`}
            >
              <div className="leading-relaxed prose prose-sm max-w-none">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
              {message.similarity !== undefined && (
                <p className="text-xs text-gray-400 mt-2">
                  Relevance: {Math.round(message.similarity * 100)}%
                </p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="flex gap-3">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your notes..."
          rows={2}
          className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-3
            text-gray-800 placeholder-gray-400 focus:outline-none focus:border-blue-400
            transition-colors"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="px-6 bg-blue-600 text-white rounded-xl font-medium
            hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed
            transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default ChatPage