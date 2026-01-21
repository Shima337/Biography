import Link from 'next/link'

export default function Home() {
  return (
    <div>
      <h1>LifeBook Lab Console</h1>
      <p>Developer-facing application for debugging, observing, and iterating AI memory extraction prompts.</p>
      
      <h2>Quick Navigation</h2>
      <ul>
        <li><Link href="/sessions">Sessions</Link> - View and manage conversation sessions</li>
        <li><Link href="/memories">Memory Inbox</Link> - Browse extracted memories</li>
        <li><Link href="/persons">People</Link> - Manage person entities</li>
        <li><Link href="/chapters">Chapters</Link> - View biography outline</li>
        <li><Link href="/prompt-runs">Prompt Runs</Link> - Debug AI prompt executions</li>
        <li><Link href="/questions">Next Questions</Link> - Review AI-generated questions</li>
      </ul>
    </div>
  )
}
