'use client'

import { useEffect, useState } from 'react'
import { api, Person, Memory } from '@/lib/api'

export default function PersonsPage() {
  const [persons, setPersons] = useState<Person[]>([])
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null)
  const [personMemories, setPersonMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const userId = 1 // TODO: Get from context or props

  useEffect(() => {
    loadPersons()
  }, [])

  useEffect(() => {
    if (selectedPerson) {
      loadPersonMemories(selectedPerson.id)
    }
  }, [selectedPerson])

  const loadPersons = async () => {
    try {
      const data = await api.getPersons(userId)
      setPersons(data)
    } catch (error) {
      console.error('Failed to load persons:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadPersonMemories = async (personId: number) => {
    try {
      const data = await api.getPersonMemories(personId)
      setPersonMemories(data)
    } catch (error) {
      console.error('Failed to load person memories:', error)
    }
  }

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1>People</h1>
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
          <div style={{ width: '400px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px' }}>
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
            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {personMemories.map(memory => (
                <div key={memory.id} style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                  <div><strong>{memory.summary}</strong></div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {memory.narrative.substring(0, 100)}...
                  </div>
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
