import { useState, useEffect } from 'react';

interface Record {
  id: string;
  name: string;
  checkIn: string;
  status: 'Safe' | 'Warning' | 'At Risk' | 'Critical';
  strikes: number;
}

const mockData: Record[] = [
  { id: 'EMP001', name: 'Aarav Sharma', checkIn: '09:15 AM', status: 'Safe', strikes: 0 },
  { id: 'EMP042', name: 'Ishita Kapoor', checkIn: '11:23 AM', status: 'Warning', strikes: 1 },
  { id: 'EMP108', name: 'Rohan Verma', checkIn: '11:45 AM', status: 'At Risk', strikes: 2 },
  { id: 'EMP015', name: 'Sanya Gupta', checkIn: '12:10 PM', status: 'Critical', strikes: 3 },
  { id: 'EMP089', name: 'Vikram Singh', checkIn: '08:50 AM', status: 'Safe', strikes: 0 },
];

function App() {
  const [records, setRecords] = useState<Record[]>(mockData);
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="dashboard-container">
      <header className="header">
        <div className="logo-section">
          <div className="logo">GROWIFY AI</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '4px' }}>
            Next-Gen Attendance Orchestration
          </div>
        </div>
        
        <div className="header-actions">
          <div className="status-badge">
            <div className="status-dot"></div>
            System Active • {time}
          </div>
        </div>
      </header>

      <section className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Employees Today</div>
          <div className="stat-value">124</div>
          <div className="stat-trend trend-down">
            <span>↑ 4.2%</span> from yesterday
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Late Check-ins</div>
          <div className="stat-value" style={{ color: 'var(--warning)' }}>18</div>
          <div className="stat-trend trend-up">
            <span>↑ 12%</span> intensity
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">AI Warnings Sent</div>
          <div className="stat-value" style={{ color: 'var(--accent-primary)' }}>12</div>
          <div className="stat-trend">
            <span>8 Friendly, 4 Strict</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Critical Escalations</div>
          <div className="stat-value" style={{ color: 'var(--danger)' }}>3</div>
          <div className="stat-trend">
            <span>Meetings scheduled for 5:00 PM</span>
          </div>
        </div>
      </section>

      <div className="content-grid">
        <main className="record-table-container">
          <div className="table-header">
            <h2>Live Attendance Feed</h2>
            <div className="filter-chip">Today, {new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long' })}</div>
          </div>
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Check-In</th>
                <th>Status</th>
                <th>Monthly Strikes</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {records.map((rec) => (
                <tr key={rec.id}>
                  <td>
                    <div className="employee-info">
                      <div className="avatar">{rec.name[0]}</div>
                      <div>
                        <div style={{ fontWeight: 600 }}>{rec.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{rec.id}</div>
                      </div>
                    </div>
                  </td>
                  <td>{rec.checkIn}</td>
                  <td>
                    <span style={{ 
                      color: rec.status === 'Safe' ? 'var(--success)' : 
                             rec.status === 'Warning' ? 'var(--warning)' : 'var(--danger)',
                      fontSize: '0.85rem',
                      fontWeight: 600
                    }}>
                      ● {rec.status}
                    </span>
                  </td>
                  <td>
                    {rec.strikes > 0 ? (
                      <span className={`strike-badge strike-${rec.strikes}`}>
                        STRIKE {rec.strikes}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>None</span>
                    )}
                  </td>
                  <td>
                    <button style={{ 
                      background: 'rgba(255,255,255,0.05)', 
                      border: '1px solid var(--glass-border)',
                      color: 'white',
                      padding: '4px 12px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      cursor: 'pointer'
                    }}>
                      View Log
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </main>

        <aside className="ai-panel">
          <div className="ai-card">
            <div className="ai-title">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12L2.1 10.1"/><path d="M12 12l9.9 1.9"/><path d="M12 12l1.9 9.9"/><path d="M12 12l-1.9-9.9"/></svg>
              AI Insights
            </div>
            <div className="ai-insight">
              <strong>Pattern Detected:</strong> Repeated lateness on Tuesdays observed for Team Delta. Suggests potential commute sync issue.
            </div>
            <div className="ai-insight">
              <strong>Action Taken:</strong> 3 final warnings issued. Meeting invitations dispatched for today at 5:00 PM IST via Google Calendar.
            </div>
            <div style={{ textAlign: 'center', marginTop: '1rem' }}>
              <button style={{ 
                background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '12px',
                fontWeight: 600,
                width: '100%',
                cursor: 'pointer'
              }}>
                Generate weekly AI Report
              </button>
            </div>
          </div>

          <div className="stat-card" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Active Alerts</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'start' }}>
                <div style={{ width: '4px', height: '30px', background: 'var(--danger)', borderRadius: '2px' }}></div>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Final Warning Signed</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Sanya Gupta acknowledged meeting invite.</div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'start' }}>
                <div style={{ width: '4px', height: '30px', background: 'var(--warning)', borderRadius: '2px' }}></div>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Strike 2 Auto-Issued</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Rohan Verma reached 2nd strike this month.</div>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default App;
