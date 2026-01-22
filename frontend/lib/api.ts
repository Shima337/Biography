const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Message {
  id: number
  session_id: number
  role: string
  content_text: string
  created_at: string
}

export interface Memory {
  id: number
  user_id: number
  session_id: number
  source_message_id: number
  summary: string
  narrative: string
  time_text: string | null
  location_text: string | null
  topics: string[]
  importance_score: number
  created_at: string
}

export interface Person {
  id: number
  user_id: number
  display_name: string
  type: string
  first_seen_memory_id: number | null
  notes: string | null
}

export interface Chapter {
  id: number
  user_id: number
  title: string
  order_index: number
  period_text: string | null
  status: string
}

export interface PromptRun {
  id: number
  session_id: number
  message_id: number | null
  prompt_name: string
  prompt_version: string
  model: string
  input_json: any
  output_text: string | null
  output_json: any
  parse_ok: boolean
  error_text: string | null
  token_in: number | null
  token_out: number | null
  latency_ms: number | null
  created_at: string
}

export interface Question {
  id: number
  user_id: number
  session_id: number
  question_text: string
  reason: string
  confidence: number
  target_type: string
  target_ref: string | null
  status: string
  created_at: string
}

export interface Session {
  id: number
  user_id: number
  created_at: string
}

export interface User {
  id: number
  name: string
  locale: string
  created_at: string
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }
  
  return response.json()
}

export const api = {
  // Users
  getUsers: () => fetchAPI<User[]>('/api/users'),
  getUser: (id: number) => fetchAPI<User>(`/api/users/${id}`),
  createUser: (name?: string) => {
    const body = name ? JSON.stringify({ name }) : JSON.stringify({});
    return fetchAPI<User>('/api/users', {
      method: 'POST',
      body,
    });
  },
  deleteUser: (id: number) =>
    fetchAPI(`/api/users/${id}`, {
      method: 'DELETE',
    }),

  // Sessions
  getSessions: () => fetchAPI<Session[]>('/api/sessions'),
  getSession: (id: number) => fetchAPI<Session>(`/api/sessions/${id}`),
  createSession: (user_id?: number) => {
    const body = user_id ? JSON.stringify({ user_id }) : JSON.stringify({});
    return fetchAPI<Session>('/api/sessions', {
      method: 'POST',
      body,
    });
  },
  getSessionMessages: (sessionId: number) => fetchAPI<Message[]>(`/api/sessions/${sessionId}/messages`),
  createMessage: (sessionId: number, text: string, extractorVersion = 'v3', plannerVersion = 'v1') =>
    fetchAPI(`/api/sessions/${sessionId}/messages?extractor_version=${extractorVersion}&planner_version=${plannerVersion}`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  // Memories
  getMemories: (params?: { user_id?: number; session_id?: number }) => {
    const query = new URLSearchParams()
    if (params?.user_id) query.append('user_id', params.user_id.toString())
    if (params?.session_id) query.append('session_id', params.session_id.toString())
    return fetchAPI<Memory[]>(`/api/memories?${query}`)
  },
  getMemory: (id: number) => fetchAPI<Memory>(`/api/memories/${id}`),

  // Persons
  getPersons: (user_id: number) => fetchAPI<Person[]>(`/api/persons?user_id=${user_id}`),
  getPerson: (id: number) => fetchAPI<Person>(`/api/persons/${id}`),
  getPersonMemories: (id: number) => fetchAPI<Memory[]>(`/api/persons/${id}/memories`),
  mergePersons: (personId: number, targetPersonId: number) =>
    fetchAPI(`/api/persons/${personId}/merge`, {
      method: 'POST',
      body: JSON.stringify({ target_person_id: targetPersonId }),
      headers: {
        'Content-Type': 'application/json',
      },
    }),

  // Chapters
  getChapters: (user_id: number) => fetchAPI<Chapter[]>(`/api/chapters?user_id=${user_id}`),
  getChapter: (id: number) => fetchAPI<Chapter>(`/api/chapters/${id}`),
  getChapterMemories: (id: number) => fetchAPI<Memory[]>(`/api/chapters/${id}/memories`),
  getChapterCoverage: (id: number) => fetchAPI(`/api/chapters/${id}/coverage`),

  // Prompt Runs
  getPromptRuns: (params?: { session_id?: number; prompt_name?: string; parse_ok?: boolean; model?: string }) => {
    const query = new URLSearchParams()
    if (params?.session_id) query.append('session_id', params.session_id.toString())
    if (params?.prompt_name) query.append('prompt_name', params.prompt_name)
    if (params?.parse_ok !== undefined) query.append('parse_ok', params.parse_ok.toString())
    if (params?.model) query.append('model', params.model)
    return fetchAPI<PromptRun[]>(`/api/prompt-runs?${query}`)
  },
  getPromptRun: (id: number) => fetchAPI<PromptRun>(`/api/prompt-runs/${id}`),

  // Questions
  getQuestions: (params?: { user_id?: number; session_id?: number; status?: string }) => {
    const query = new URLSearchParams()
    if (params?.user_id) query.append('user_id', params.user_id.toString())
    if (params?.session_id) query.append('session_id', params.session_id.toString())
    if (params?.status) query.append('status', params.status)
    return fetchAPI<Question[]>(`/api/questions?${query}`)
  },
  getQuestion: (id: number) => fetchAPI<Question>(`/api/questions/${id}`),
  updateQuestionStatus: (id: number, status: string) =>
    fetchAPI(`/api/questions/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),
}
