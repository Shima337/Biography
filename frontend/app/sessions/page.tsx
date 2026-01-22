'use client'

import { useEffect, useState } from 'react'
import { api, Session, Message } from '@/lib/api'
import Link from 'next/link'

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)

  useEffect(() => {
    loadSelectedUser()
    loadSessions()
    
    // Listen for user changes
    const handleUserChange = () => {
      loadSelectedUser()
    }
    window.addEventListener('userChanged', handleUserChange)
    return () => window.removeEventListener('userChanged', handleUserChange)
  }, [])

  useEffect(() => {
    if (selectedUserId) {
      loadSessions()
    }
  }, [selectedUserId])

  const loadSelectedUser = () => {
    const saved = localStorage.getItem('selectedUserId')
    if (saved) {
      setSelectedUserId(parseInt(saved))
    }
  }

  const loadSessions = async () => {
    try {
      const data = await api.getSessions()
      // Filter by selected user if available
      const filtered = selectedUserId 
        ? data.filter(s => s.user_id === selectedUserId)
        : data
      setSessions(filtered)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSession = async () => {
    if (!selectedUserId) {
      alert('Please select a user first')
      return
    }
    
    setCreating(true)
    try {
      const newSession = await api.createSession(selectedUserId)
      await loadSessions()
      // Optionally redirect to new session
      window.location.href = `/sessions/${newSession.id}`
    } catch (error) {
      console.error('Failed to create session:', error)
      alert('Failed to create session')
    } finally {
      setCreating(false)
    }
  }

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Sessions</h1>
        <button
          onClick={handleCreateSession}
          disabled={creating || !selectedUserId}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: creating || !selectedUserId ? 'not-allowed' : 'pointer',
            opacity: creating || !selectedUserId ? 0.6 : 1
          }}
        >
          {creating ? 'Creating...' : '+ New Session'}
        </button>
      </div>
      
      {!selectedUserId && (
        <div style={{ padding: '10px', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px', marginBottom: '20px' }}>
          Please select a user to create sessions
        </div>
      )}

      {selectedUserId && (
        <div style={{ marginBottom: '15px', color: '#666' }}>
          Showing sessions for User ID: <strong>{selectedUserId}</strong>
        </div>
      )}

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>User ID</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map(session => (
            <tr key={session.id}>
              <td>{session.id}</td>
              <td>{session.user_id}</td>
              <td>{new Date(session.created_at).toLocaleString()}</td>
              <td>
                <Link href={`/sessions/${session.id}`}>
                  <button>View</button>
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
