'use client'

import { useEffect, useState } from 'react'
import { api, Person, Memory } from '@/lib/api'

export default function PersonsPage() {
  const [personsV1, setPersonsV1] = useState<Person[]>([])
  const [personsV2, setPersonsV2] = useState<Person[]>([])
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
      const [v1Data, v2Data] = await Promise.all([
        api.getPersons(selectedUserId, 'v1'),
        api.getPersons(selectedUserId, 'v2')
      ])
      setPersonsV1(v1Data)
      setPersonsV2(v2Data)
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

  const renderPersonTable = (persons: Person[], title: string, pipelineVersion: string) => (
    <div style={{ flex: 1 }}>
      <h3 style={{ marginBottom: '10px', padding: '10px', backgroundColor: pipelineVersion === 'v1' ? '#e3f2fd' : '#f3e5f5', borderRadius: '4px' }}>
        {title} ({persons.length} персон)
      </h3>
      <table style={{ width: '100%' }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Type</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {persons.length === 0 ? (
            <tr>
              <td colSpan={4} style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
                Нет персон для этого пайплайна
              </td>
            </tr>
          ) : (
            persons.map(person => (
              <tr key={person.id}>
                <td>{person.id}</td>
                <td>{person.display_name}</td>
                <td>{person.type}</td>
                <td>
                  <button onClick={() => setSelectedPerson(person)}>View</button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )

  return (
    <div>
      <h1>People - Pipeline Comparison</h1>
      <div style={{ marginBottom: '15px', color: '#666' }}>
        Showing people for User ID: <strong>{selectedUserId}</strong>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {renderPersonTable(personsV1, 'Pipeline v1 (Single-stage)', 'v1')}
        {renderPersonTable(personsV2, 'Pipeline v2 (Two-stage)', 'v2')}
      </div>
      
      {selectedPerson && (
        <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px', maxHeight: '90vh', overflowY: 'auto' }}>
          <h3>Person Detail</h3>
          <div style={{ marginBottom: '10px' }}>
            <strong>Name:</strong> {selectedPerson.display_name}
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Type:</strong> {selectedPerson.type}
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Pipeline:</strong> {selectedPerson.pipeline_version || 'v1'}
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
  )
}
