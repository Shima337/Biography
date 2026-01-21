'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { api, Message, PromptRun } from '@/lib/api'

export default function SessionDetailPage() {
  const params = useParams()
  const sessionId = parseInt(params.id as string)
  
  const [messages, setMessages] = useState<Message[]>([])
  const [promptRuns, setPromptRuns] = useState<PromptRun[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [extractorVersion, setExtractorVersion] = useState('v1')
  const [plannerVersion, setPlannerVersion] = useState('v1')
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [sessionId])

  const loadData = async () => {
    try {
      const [msgs, runs] = await Promise.all([
        api.getSessionMessages(sessionId),
        api.getPromptRuns({ session_id: sessionId })
      ])
      setMessages(msgs)
      setPromptRuns(runs)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setProcessing(true)
    setError(null)
    try {
      await api.createMessage(sessionId, newMessage, extractorVersion, plannerVersion)
      setNewMessage('')
      await loadData()
    } catch (error: any) {
      console.error('Failed to create message:', error)
      const errorMsg = error?.message || 'Failed to process message. Check backend logs.'
      setError(errorMsg)
      alert(`Error: ${errorMsg}`)
    } finally {
      setProcessing(false)
    }
  }

  const getMessageRuns = (messageId: number) => {
    return promptRuns.filter(run => run.message_id === messageId)
  }

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1>Session {sessionId}</h1>
      
      <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px' }}>
        <h3>Send New Message</h3>
        {error && (
          <div style={{ padding: '10px', backgroundColor: '#fee', color: '#c00', borderRadius: '4px', marginBottom: '10px' }}>
            <strong>Error:</strong> {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Enter text to process..."
            rows={4}
            required
            disabled={processing}
          />
          <div style={{ marginTop: '10px' }}>
            <label>
              Extractor Version:
              <select value={extractorVersion} onChange={(e) => setExtractorVersion(e.target.value)} disabled={processing}>
                <option value="v1">v1</option>
                <option value="v2">v2</option>
              </select>
            </label>
            <label style={{ marginLeft: '20px' }}>
              Planner Version:
              <select value={plannerVersion} onChange={(e) => setPlannerVersion(e.target.value)} disabled={processing}>
                <option value="v1">v1</option>
                <option value="v2">v2</option>
              </select>
            </label>
          </div>
          <button type="submit" style={{ marginTop: '10px' }} disabled={processing}>
            {processing ? 'Processing...' : 'Process Message'}
          </button>
        </form>
      </div>

      <h2>Message Timeline</h2>
      {messages.map(message => {
        const runs = getMessageRuns(message.id)
        return (
          <div key={message.id} style={{ marginBottom: '30px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px' }}>
            <div style={{ marginBottom: '10px' }}>
              <strong>{message.role}:</strong> {message.content_text}
              <div style={{ fontSize: '12px', color: '#666' }}>
                {new Date(message.created_at).toLocaleString()}
              </div>
            </div>
            
            {runs.length > 0 && (
              <div style={{ marginTop: '15px' }}>
                <h4>Prompt Runs:</h4>
                {runs.map(run => (
                  <div key={run.id} style={{ marginTop: '10px', padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                    <div>
                      <strong>{run.prompt_name}</strong> v{run.prompt_version} ({run.model})
                      {run.parse_ok ? (
                        <span style={{ color: 'green', marginLeft: '10px' }}>✓ Parsed OK</span>
                      ) : (
                        <span style={{ color: 'red', marginLeft: '10px' }}>✗ Parse Error</span>
                      )}
                    </div>
                    {run.output_json && (
                      <div className="json-view" style={{ marginTop: '5px' }}>
                        {JSON.stringify(run.output_json, null, 2)}
                      </div>
                    )}
                    {run.error_text && (
                      <div style={{ color: 'red', marginTop: '5px' }}>
                        Error: {run.error_text}
                      </div>
                    )}
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                      Tokens: {run.token_in} in / {run.token_out} out | Latency: {run.latency_ms}ms
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
