import axios from 'axios'

// Create an Axios instance with default configuration
// this is where you determine the base URL
const api = axios.create({
  baseURL: 'http://studytool-backend-env.eba-h9ihc2tv.us-east-2.elasticbeanstalk.com',
  headers: {
    'Content-Type': 'application/json'
  }
})

export const uploadFile = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/ingest/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export const getDocumentStatus = async (documentId) => {
    // call api endpoint
  const response = await api.get(`/ingest/documents/${documentId}/status`)
  return response.data
}

export const generateFlashcards = async (documentId) => {
  const response = await api.post(`/flashcards/generate/${documentId}`)
  return response.data
}

export const getFlashcards = async (documentId) => {
  const response = await api.get(`/flashcards/${documentId}`)
  return response.data
}

export const askQuestion = async (documentId, question) => {
  const response = await api.post('/chat/ask', {
    document_id: documentId,
    question
  })
  return response.data
}

export const getDueCards = async (documentId) => {
  const response = await api.get(`/quiz/due/${documentId}`)
  return response.data
}

export const rateCard = async (flashcardId, rating) => {
  const response = await api.post('/quiz/rate', {
    flashcard_id: flashcardId,
    rating
  })
  return response.data
}

export default api