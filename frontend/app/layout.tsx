import './globals.css'
import Link from 'next/link'

export const metadata = {
  title: 'LifeBook Lab Console',
  description: 'Developer console for AI memory extraction debugging',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <div style={{ display: 'flex', minHeight: '100vh' }}>
          <nav style={{
            width: '200px',
            backgroundColor: '#f5f5f5',
            padding: '20px',
            borderRight: '1px solid #ddd'
          }}>
            <h2 style={{ marginTop: 0 }}>LifeBook Lab</h2>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li style={{ marginBottom: '10px' }}>
                <Link href="/sessions" style={{ textDecoration: 'none', color: '#333' }}>
                  Sessions
                </Link>
              </li>
              <li style={{ marginBottom: '10px' }}>
                <Link href="/memories" style={{ textDecoration: 'none', color: '#333' }}>
                  Memory Inbox
                </Link>
              </li>
              <li style={{ marginBottom: '10px' }}>
                <Link href="/persons" style={{ textDecoration: 'none', color: '#333' }}>
                  People
                </Link>
              </li>
              <li style={{ marginBottom: '10px' }}>
                <Link href="/chapters" style={{ textDecoration: 'none', color: '#333' }}>
                  Chapters
                </Link>
              </li>
              <li style={{ marginBottom: '10px' }}>
                <Link href="/prompt-runs" style={{ textDecoration: 'none', color: '#333' }}>
                  Prompt Runs
                </Link>
              </li>
              <li style={{ marginBottom: '10px' }}>
                <Link href="/questions" style={{ textDecoration: 'none', color: '#333' }}>
                  Next Questions
                </Link>
              </li>
            </ul>
          </nav>
          <main style={{ flex: 1, padding: '20px' }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
