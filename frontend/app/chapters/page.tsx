'use client'

import { useEffect, useState } from 'react'
import { api, Chapter, Memory } from '@/lib/api'

export default function ChaptersPage() {
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [selectedChapter, setSelectedChapter] = useState<Chapter | null>(null)
  const [chapterMemories, setChapterMemories] = useState<Memory[]>([])
  const [coverage, setCoverage] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const userId = 1 // TODO: Get from context or props

  useEffect(() => {
    loadChapters()
  }, [])

  useEffect(() => {
    if (selectedChapter) {
      loadChapterData(selectedChapter.id)
    }
  }, [selectedChapter])

  const loadChapters = async () => {
    try {
      const data = await api.getChapters(userId)
      setChapters(data)
    } catch (error) {
      console.error('Failed to load chapters:', error)
    } finally {
      setLoading(false)
    }
  }

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

  return (
    <div>
      <h1>Chapters (Outline)</h1>
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ flex: 1 }}>
          <table>
            <thead>
              <tr>
                <th>Order</th>
                <th>Title</th>
                <th>Period</th>
                <th>Status</th>
                <th>Coverage</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {chapters.map(chapter => (
                <tr key={chapter.id}>
                  <td>{chapter.order_index}</td>
                  <td>{chapter.title}</td>
                  <td>{chapter.period_text || 'N/A'}</td>
                  <td>{chapter.status}</td>
                  <td>-</td>
                  <td>
                    <button onClick={() => setSelectedChapter(chapter)}>View</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {selectedChapter && (
          <div style={{ width: '400px', padding: '15px', border: '1px solid #ddd', borderRadius: '4px' }}>
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
            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {chapterMemories.map(memory => (
                <div key={memory.id} style={{ marginBottom: '10px', padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                  <div><strong>{memory.summary}</strong></div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {memory.narrative.substring(0, 100)}...
                  </div>
                </div>
              ))}
            </div>
            <button onClick={() => setSelectedChapter(null)} style={{ marginTop: '10px' }}>Close</button>
          </div>
        )}
      </div>
    </div>
  )
}
