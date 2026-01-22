'use client'

import { useEffect, useState } from 'react'
import { api, Chapter, Memory } from '@/lib/api'

export default function ChaptersPage() {
  const [chaptersV1, setChaptersV1] = useState<Chapter[]>([])
  const [chaptersV2, setChaptersV2] = useState<Chapter[]>([])
  const [selectedChapter, setSelectedChapter] = useState<Chapter | null>(null)
  const [chapterMemories, setChapterMemories] = useState<Memory[]>([])
  const [coverage, setCoverage] = useState<any>(null)
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
      loadChapters()
    }
  }, [selectedUserId])

  const loadSelectedUser = () => {
    const saved = localStorage.getItem('selectedUserId')
    if (saved) {
      setSelectedUserId(parseInt(saved))
    }
  }

  const loadChapters = async () => {
    if (!selectedUserId) return
    
    try {
      const [v1Data, v2Data] = await Promise.all([
        api.getChapters(selectedUserId, 'v1'),
        api.getChapters(selectedUserId, 'v2')
      ])
      setChaptersV1(v1Data)
      setChaptersV2(v2Data)
    } catch (error) {
      console.error('Failed to load chapters:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedChapter) {
      loadChapterData(selectedChapter.id)
    }
  }, [selectedChapter])

  const loadChapterData = async (chapterId: number) => {
    try {
      const [memories, cov] = await Promise.all([
        api.getChapterMemories(chapterId),
        api.getChapterCoverage(chapterId)
      ])
      setChapterMemories(memories)
      setCoverage(cov)
    } catch (error) {
      console.error('Failed to load chapter data:', error)
    }
  }

  if (loading) return <div>Loading...</div>

  if (!selectedUserId) {
    return (
      <div>
        <h1>Chapters (Outline)</h1>
        <div style={{ padding: '20px', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px' }}>
          Please select a user to view chapters
        </div>
      </div>
    )
  }

  const renderChapterTable = (chapters: Chapter[], title: string, pipelineVersion: string) => (
    <div style={{ flex: 1 }}>
      <h3 style={{ marginBottom: '10px', padding: '10px', backgroundColor: pipelineVersion === 'v1' ? '#e3f2fd' : '#f3e5f5', borderRadius: '4px' }}>
        {title} ({chapters.length} глав)
      </h3>
      <table style={{ width: '100%' }}>
        <thead>
          <tr>
            <th>Order</th>
            <th>Title</th>
            <th>Period</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {chapters.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
                Нет глав для этого пайплайна
              </td>
            </tr>
          ) : (
            chapters.map(chapter => (
              <tr key={chapter.id}>
                <td>{chapter.order_index}</td>
                <td>{chapter.title}</td>
                <td>{chapter.period_text || 'N/A'}</td>
                <td>{chapter.status}</td>
                <td>
                  <button onClick={() => setSelectedChapter(chapter)}>View</button>
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
      <h1>Chapters (Outline) - Pipeline Comparison</h1>
      <div style={{ marginBottom: '15px', color: '#666' }}>
        Showing chapters for User ID: <strong>{selectedUserId}</strong>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {renderChapterTable(chaptersV1, 'Pipeline v1 (Single-stage)', 'v1')}
        {renderChapterTable(chaptersV2, 'Pipeline v2 (Two-stage)', 'v2')}
      </div>
      
      {selectedChapter && (
        <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px', maxHeight: '90vh', overflowY: 'auto' }}>
          <h3>Chapter Detail</h3>
          <div style={{ marginBottom: '10px' }}>
            <strong>Title:</strong> {selectedChapter.title}
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Period:</strong> {selectedChapter.period_text || 'N/A'}
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Status:</strong> {selectedChapter.status}
          </div>
          {coverage && (
            <div style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
              <strong>Coverage:</strong> {coverage.coverage_percent}%
              <div style={{ fontSize: '12px' }}>
                {coverage.chapter_memories} / {coverage.total_memories} memories
              </div>
            </div>
          )}
          
          <h4>Linked Memories ({chapterMemories.length})</h4>
          <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
            {chapterMemories.map(memory => (
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
          <button onClick={() => setSelectedChapter(null)} style={{ marginTop: '10px' }}>Close</button>
        </div>
      )}
    </div>
  )
}
