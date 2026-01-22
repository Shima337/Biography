'use client'

import { useEffect, useState } from 'react'
import { api, Memory } from '@/lib/api'

export default function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null)
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
      loadMemories()
    }
  }, [selectedUserId])

  const loadSelectedUser = () => {
    const saved = localStorage.getItem('selectedUserId')
    if (saved) {
      setSelectedUserId(parseInt(saved))
    }
  }

  const loadMemories = async () => {
    if (!selectedUserId) return
    
    try {
      const data = await api.getMemories({ user_id: selectedUserId })
      setMemories(data)
    } catch (error) {
      console.error('Failed to load memories:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading...</div>

  if (!selectedUserId) {
    return (
      <div>
        <h1>Memory Inbox</h1>
        <div style={{ padding: '20px', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px' }}>
          Please select a user to view memories
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1>Memory Inbox</h1>
      <div style={{ marginBottom: '15px', color: '#666' }}>
        Showing memories for User ID: <strong>{selectedUserId}</strong>
      </div>
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ flex: 1 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Summary</th>
                <th>Importance</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {memories.map(memory => (
                <tr key={memory.id}>
                  <td>{memory.id}</td>
                  <td>{memory.summary}</td>
                  <td>{memory.importance_score.toFixed(2)}</td>
                  <td>{new Date(memory.created_at).toLocaleString()}</td>
                  <td>
                    <button onClick={() => setSelectedMemory(memory)}>View</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {selectedMemory && (
          <div style={{ width: '400px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px' }}>
            <h3>Memory Detail</h3>
            <div style={{ marginBottom: '10px' }}>
              <strong>Summary:</strong> {selectedMemory.summary}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Narrative:</strong>
              <div style={{ marginTop: '5px', padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                {selectedMemory.narrative}
              </div>
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Time:</strong> {selectedMemory.time_text || 'N/A'}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Location:</strong> {selectedMemory.location_text || 'N/A'}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Topics:</strong> {selectedMemory.topics.join(', ') || 'None'}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Importance:</strong> {selectedMemory.importance_score.toFixed(2)}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Source Message ID:</strong> {selectedMemory.source_message_id}
            </div>
            <button onClick={() => setSelectedMemory(null)}>Close</button>
          </div>
        )}
      </div>
    </div>
  )
}
