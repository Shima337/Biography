'use client'

import { useEffect, useState } from 'react'
import { api, PromptRun } from '@/lib/api'

export default function PromptRunsPage() {
  const [runs, setRuns] = useState<PromptRun[]>([])
  const [selectedRun, setSelectedRun] = useState<PromptRun | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [filters, setFilters] = useState({
    prompt_name: '',
    parse_ok: null as boolean | null,
    model: ''
  })

  useEffect(() => {
    loadSelectedUser()
  }, [])

  useEffect(() => {
    if (selectedUserId) {
      loadRuns()
    }
  }, [filters, selectedUserId])

  const loadSelectedUser = () => {
    const saved = localStorage.getItem('selectedUserId')
    if (saved) {
      setSelectedUserId(parseInt(saved))
    }
  }

  const loadRuns = async () => {
    if (!selectedUserId) return
    
    try {
      const params: any = { user_id: selectedUserId }
      if (filters.prompt_name) params.prompt_name = filters.prompt_name
      if (filters.parse_ok !== null) params.parse_ok = filters.parse_ok
      if (filters.model) params.model = filters.model
      
      const data = await api.getPromptRuns(params)
      setRuns(data)
    } catch (error) {
      console.error('Failed to load prompt runs:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading...</div>

  if (!selectedUserId) {
    return (
      <div>
        <h1>Prompt Runs (Debug)</h1>
        <div style={{ padding: '20px', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px' }}>
          Please select a user to view prompt runs
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1>Prompt Runs (Debug)</h1>
      <div style={{ marginBottom: '15px', color: '#666' }}>
        Showing prompt runs for User ID: <strong>{selectedUserId}</strong>
      </div>
      
      <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px' }}>
        <h3>Filters</h3>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <select
            value={filters.prompt_name}
            onChange={(e) => setFilters({ ...filters, prompt_name: e.target.value })}
          >
            <option value="">All Prompts</option>
            <option value="extractor">Extractor</option>
            <option value="planner">Planner</option>
          </select>
          <select
            value={filters.parse_ok === null ? '' : filters.parse_ok.toString()}
            onChange={(e) => setFilters({ ...filters, parse_ok: e.target.value === '' ? null : e.target.value === 'true' })}
          >
            <option value="">All Status</option>
            <option value="true">Parse OK</option>
            <option value="false">Parse Error</option>
          </select>
          <input
            type="text"
            placeholder="Model filter"
            value={filters.model}
            onChange={(e) => setFilters({ ...filters, model: e.target.value })}
          />
        </div>
      </div>

      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ flex: 1 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Prompt</th>
                <th>Version</th>
                <th>Model</th>
                <th>Parse OK</th>
                <th>Tokens</th>
                <th>Latency</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.map(run => (
                <tr key={run.id}>
                  <td>{run.id}</td>
                  <td>{run.prompt_name}</td>
                  <td>{run.prompt_version}</td>
                  <td>{run.model}</td>
                  <td>
                    {run.parse_ok ? (
                      <span style={{ color: 'green' }}>✓</span>
                    ) : (
                      <span style={{ color: 'red' }}>✗</span>
                    )}
                  </td>
                  <td>{run.token_in}/{run.token_out}</td>
                  <td>{run.latency_ms}ms</td>
                  <td>{new Date(run.created_at).toLocaleString()}</td>
                  <td>
                    <button onClick={() => setSelectedRun(run)}>View</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {selectedRun && (
          <div style={{ width: '500px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px' }}>
            <h3>Prompt Run Detail</h3>
            <div style={{ marginBottom: '10px' }}>
              <strong>Prompt:</strong> {selectedRun.prompt_name} v{selectedRun.prompt_version}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Model:</strong> {selectedRun.model}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Parse OK:</strong> {selectedRun.parse_ok ? 'Yes' : 'No'}
            </div>
            {selectedRun.error_text && (
              <div style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#fee', borderRadius: '4px' }}>
                <strong>Error:</strong> {selectedRun.error_text}
              </div>
            )}
            
            <h4>Input JSON</h4>
            <div className="json-view" style={{ marginBottom: '15px' }}>
              {JSON.stringify(selectedRun.input_json, null, 2)}
            </div>
            
            <h4>Output Text</h4>
            <div className="json-view" style={{ marginBottom: '15px' }}>
              {selectedRun.output_text || 'N/A'}
            </div>
            
            <h4>Parsed Output JSON</h4>
            <div className="json-view" style={{ marginBottom: '15px' }}>
              {JSON.stringify(selectedRun.output_json, null, 2)}
            </div>
            
            <div style={{ fontSize: '12px', color: '#666' }}>
              Tokens: {selectedRun.token_in} in / {selectedRun.token_out} out<br />
              Latency: {selectedRun.latency_ms}ms
            </div>
            
            <button onClick={() => setSelectedRun(null)} style={{ marginTop: '10px' }}>Close</button>
          </div>
        )}
      </div>
    </div>
  )
}
