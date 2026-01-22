'use client'

import { useEffect, useState } from 'react'
import { api, Person, Memory } from '@/lib/api'

export default function PersonsPage() {
  const [persons, setPersons] = useState<Person[]>([])
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null)
  const [personMemories, setPersonMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
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
      loadPersons()
    }
  }, [selectedUserId])

  const loadSelectedUser = () => {
    const saved = localStorage.getItem('selectedUserId')
    if (saved) {
      setSelectedUserId(parseInt(saved))
    }
  }

  const loadPersons = async () => {
    if (!selectedUserId) return
    
    try {
      const data = await api.getPersons(selectedUserId)
      setPersons(data)
    } catch (error) {
      console.error('Failed to load persons:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedPerson) {
      loadPersonMemories(selectedPerson.id)
    }
  }, [selectedPerson])

  const loadPersonMemories = async (personId: number) => {
    try {
      const data = await api.getPersonMemories(personId)
      setPersonMemories(data)
    } catch (error) {
      console.error('Failed to load person memories:', error)
    }
  }

  if (loading) return <div>Loading...</div>

  if (!selectedUserId) {
    return (
      <div>
        <h1>People</h1>
        <div style={{ padding: '20px', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px' }}>
          Please select a user to view people
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1>People</h1>
      <div style={{ marginBottom: '15px', color: '#666' }}>
        Showing people for User ID: <strong>{selectedUserId}</strong>
      </div>
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ flex: 1 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {persons.map(person => (
                <tr key={person.id}>
                  <td>{person.id}</td>
                  <td>{person.display_name}</td>
                  <td>{person.type}</td>
                  <td>
                    <button onClick={() => setSelectedPerson(person)}>View</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {selectedPerson && (
          <div style={{ width: '500px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px', maxHeight: '90vh', overflowY: 'auto' }}>
            <h3>Person Detail</h3>
            <div style={{ marginBottom: '10px' }}>
              <strong>Name:</strong> {selectedPerson.display_name}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Type:</strong> {selectedPerson.type}
            </div>
            {selectedPerson.notes && (
              <div style={{ marginBottom: '10px' }}>
                <strong>Notes:</strong> {selectedPerson.notes}
              </div>
            )}
            
            <h4>Related Memories ({personMemories.length})</h4>
            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {personMemories.map(memory => (
                <div key={memory.id} style={{ marginBottom: '15px', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>{memory.summary}</strong>
                  </div>
                  <div style={{ fontSize: '14px', color: '#333', whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                    {memory.narrative}
                  </div>
                  {memory.time_text && (
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                      <strong>Time:</strong> {memory.time_text}
                    </div>
                  )}
                  {memory.location_text && (
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      <strong>Location:</strong> {memory.location_text}
                    </div>
                  )}
                  {memory.topics && memory.topics.length > 0 && (
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                      <strong>Topics:</strong> {memory.topics.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <button onClick={() => setSelectedPerson(null)} style={{ marginTop: '10px' }}>Close</button>
          </div>
        )}
      </div>
    </div>
  )
}
