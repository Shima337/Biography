'use client'

import { useEffect, useState } from 'react'
import { api, User } from '@/lib/api'

export default function UserSelector() {
  const [users, setUsers] = useState<User[]>([])
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    loadUsers()
    loadSelectedUser()
  }, [])

  const loadUsers = async () => {
    try {
      const allUsers = await api.getUsers()
      setUsers(allUsers)
      
      // If no user selected and users exist, select first one
      if (allUsers.length > 0 && !selectedUserId) {
        const saved = localStorage.getItem('selectedUserId')
        if (saved) {
          const savedId = parseInt(saved)
          if (allUsers.find(u => u.id === savedId)) {
            setSelectedUserId(savedId)
            return
          }
        }
        setSelectedUserId(allUsers[0].id)
        localStorage.setItem('selectedUserId', allUsers[0].id.toString())
      }
    } catch (error) {
      console.error('Failed to load users:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadSelectedUser = () => {
    const saved = localStorage.getItem('selectedUserId')
    if (saved) {
      setSelectedUserId(parseInt(saved))
    }
  }

  const handleCreateUser = async () => {
    setCreating(true)
    try {
      const newUser = await api.createUser()
      await loadUsers()
      setSelectedUserId(newUser.id)
      localStorage.setItem('selectedUserId', newUser.id.toString())
    } catch (error) {
      console.error('Failed to create user:', error)
      alert('Failed to create user')
    } finally {
      setCreating(false)
    }
  }

  const handleSelectUser = (userId: number) => {
    setSelectedUserId(userId)
    localStorage.setItem('selectedUserId', userId.toString())
  }

  if (loading) {
    return <div style={{ padding: '10px' }}>Loading users...</div>
  }

  const selectedUser = users.find(u => u.id === selectedUserId)

  return (
    <div style={{
      padding: '15px',
      backgroundColor: '#fff',
      borderBottom: '1px solid #ddd',
      marginBottom: '20px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px', flexWrap: 'wrap' }}>
        <label style={{ fontWeight: 'bold' }}>User:</label>
        
        {users.length > 0 && (
          <select
            value={selectedUserId || ''}
            onChange={(e) => handleSelectUser(parseInt(e.target.value))}
            style={{
              padding: '5px 10px',
              fontSize: '14px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              minWidth: '150px'
            }}
          >
            {users.map(user => (
              <option key={user.id} value={user.id}>
                {user.name} {selectedUserId === user.id ? '✓' : ''}
              </option>
            ))}
          </select>
        )}

        <button
          onClick={handleCreateUser}
          disabled={creating}
          style={{
            padding: '5px 15px',
            fontSize: '16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: creating ? 'not-allowed' : 'pointer',
            opacity: creating ? 0.6 : 1
          }}
          title="Create new user"
        >
          {creating ? '...' : '+'}
        </button>

        {selectedUser && (
          <span style={{ color: '#666', fontSize: '14px' }}>
            Selected: <strong>{selectedUser.name}</strong> (ID: {selectedUser.id})
          </span>
        )}
      </div>
    </div>
  )
}
