'use client'

import { useEffect, useState } from 'react'
import { api, Question } from '@/lib/api'

export default function QuestionsPage() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)

  useEffect(() => {
    loadSelectedUser()
    
    // Listen for user changes
    const handleUserChange = () => {
      loadSelectedUser()
    }
    window.addEventListener('userChanged', handleUserChange)
    return () => window.removeEventListener('userChanged', handleUserChange)
  }, [])

  useEffect(() => {
    if (selectedUserId) {
      loadQuestions()
    }
  }, [statusFilter, selectedUserId])

  const loadSelectedUser = () => {
    const saved = localStorage.getItem('selectedUserId')
    if (saved) {
      setSelectedUserId(parseInt(saved))
    }
  }

  const loadQuestions = async () => {
    if (!selectedUserId) return
    
    try {
      const params: any = { user_id: selectedUserId }
      if (statusFilter) params.status = statusFilter
      const data = await api.getQuestions(params)
      setQuestions(data)
    } catch (error) {
      console.error('Failed to load questions:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateStatus = async (questionId: number, newStatus: string) => {
    try {
      await api.updateQuestionStatus(questionId, newStatus)
      loadQuestions()
    } catch (error) {
      console.error('Failed to update question status:', error)
      alert('Failed to update status')
    }
  }

  if (loading) return <div>Loading...</div>

  if (!selectedUserId) {
    return (
      <div>
        <h1>Next Questions</h1>
        <div style={{ padding: '20px', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px' }}>
          Please select a user to view questions
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1>Next Questions</h1>
      <div style={{ marginBottom: '15px', color: '#666' }}>
        Showing questions for User ID: <strong>{selectedUserId}</strong>
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <label>
          Filter by Status:
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ marginLeft: '10px' }}
          >
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="asked">Asked</option>
            <option value="dismissed">Dismissed</option>
          </select>
        </label>
      </div>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Question</th>
            <th>Reason</th>
            <th>Confidence</th>
            <th>Target</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {questions.map(question => (
            <tr key={question.id}>
              <td>{question.id}</td>
              <td>{question.question_text}</td>
              <td>{question.reason}</td>
              <td>{question.confidence.toFixed(2)}</td>
              <td>{question.target_type} {question.target_ref ? `(${question.target_ref})` : ''}</td>
              <td>{question.status}</td>
              <td>{new Date(question.created_at).toLocaleString()}</td>
              <td>
                {question.status === 'pending' && (
                  <>
                    <button onClick={() => updateStatus(question.id, 'asked')}>Mark Asked</button>
                    <button onClick={() => updateStatus(question.id, 'dismissed')}>Dismiss</button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
