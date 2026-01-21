'use client'

import { useEffect, useState } from 'react'
import { api, Session, Message } from '@/lib/api'
import Link from 'next/link'

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const data = await api.getSessions()
      setSessions(data)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1>Sessions</h1>
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
