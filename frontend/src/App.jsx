import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import UploadPage from './pages/UploadPage'
import FlashcardsPage from './pages/FlashcardsPage'
import ChatPage from './pages/ChatPage'
import QuizPage from './pages/QuizPage'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/flashcards" element={<FlashcardsPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/quiz" element={<QuizPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App