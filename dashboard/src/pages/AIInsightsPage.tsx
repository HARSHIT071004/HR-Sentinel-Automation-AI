import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import { cn } from '../lib/utils';

interface Employee {
  id: string;
  employee_id: string;
  user_name: string | null;
  department_name: string | null;
}

interface RiskScore {
  employee_id: string;
  name: string;
  score: number;
  level: string;
  reasoning: string;
  recommendations: string[];
  factors: Record<string, string>;
  calculated_at: string;
}

interface BehaviorAnalysis {
  employee_id: string;
  name: string;
  behavior_summary: string;
  patterns: string[];
  anomalies: { description: string; severity: string }[];
  trends: { pattern: string; frequency: string; direction: string }[];
  potential_causes: string[];
  recommendations: string[];
  confidence: string;
}

export default function AIInsightsPage() {
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [riskResult, setRiskResult] = useState<RiskScore | null>(null);
  const [behaviorResult, setBehaviorResult] = useState<BehaviorAnalysis | null>(null);
  const [loading, setLoading] = useState<'risk' | 'behavior' | null>(null);
  const [error, setError] = useState('');

  const { data: employees } = useQuery<Employee[]>({
    queryKey: ['employees'],
    queryFn: async () => (await apiClient.get('/employees')).data,
  });

  const analyzeRisk = async () => {
    if (!selectedEmployee) return;
    setLoading('risk');
    setError('');
    try {
      const res = await apiClient.get(`/ai/risk/${selectedEmployee}`);
      setRiskResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze risk');
    } finally {
      setLoading(null);
    }
  };

  const analyzeBehavior = async () => {
    if (!selectedEmployee) return;
    setLoading('behavior');
    setError('');
    try {
      const res = await apiClient.get(`/ai/behavior/${selectedEmployee}`);
      setBehaviorResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze behavior');
    } finally {
      setLoading(null);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
      case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      default: return 'text-green-400 bg-green-500/10 border-green-500/20';
    }
  };

  const factorEntries = riskResult?.factors
    ? Object.entries(riskResult.factors)
    : [];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">AI Insights</h1>
        <p className="text-sm text-muted-foreground mt-1">AI-powered risk scoring and behavior analysis</p>
      </div>

      <div className="bg-card rounded-xl border border-border p-5">
        <h2 className="text-sm font-semibold text-foreground mb-3">Select Employee</h2>
        <div className="flex gap-3">
          <select
            value={selectedEmployee}
            onChange={(e) => setSelectedEmployee(e.target.value)}
            className="flex-1 px-3 py-2 bg-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">Choose an employee...</option>
            {employees?.map((emp) => (
              <option key={emp.employee_id} value={emp.employee_id}>
                {emp.user_name || emp.employee_id} ({emp.employee_id})
              </option>
            ))}
          </select>
          <button
            onClick={analyzeRisk}
            disabled={!selectedEmployee || loading !== null}
            className="px-4 py-2 bg-primary hover:bg-primary/90 disabled:opacity-50 text-primary-foreground text-sm font-medium rounded-lg transition-colors"
          >
            {loading === 'risk' ? 'Analyzing...' : 'Risk Score'}
          </button>
          <button
            onClick={analyzeBehavior}
            disabled={!selectedEmployee || loading !== null}
            className="px-4 py-2 bg-primary hover:bg-primary/90 disabled:opacity-50 text-primary-foreground text-sm font-medium rounded-lg transition-colors"
          >
            {loading === 'behavior' ? 'Analyzing...' : 'Behavior Analysis'}
          </button>
        </div>
        {error && (
          <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">{error}</div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-sm font-semibold text-foreground">Risk Assessment</h2>
          </div>
          {riskResult ? (
            <div className="p-5 space-y-4">
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <div className={cn('w-20 h-20 rounded-2xl border-2 flex items-center justify-center', getRiskColor(riskResult.level))}>
                    <span className="text-2xl font-bold">{riskResult.score}</span>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1">/100</p>
                </div>
                <div>
                  <span className={cn('px-2 py-1 rounded-md text-xs font-bold border', getRiskColor(riskResult.level))}>
                    {riskResult.level} Risk
                  </span>
                  <p className="text-xs text-muted-foreground mt-2">{riskResult.employee_id}</p>
                </div>
              </div>
              <div>
                <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Reasoning</h3>
                <p className="text-sm text-foreground/80 leading-relaxed">{riskResult.reasoning}</p>
              </div>
              {factorEntries.length > 0 && (
                <div>
                  <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Risk Factors</h3>
                  <div className="space-y-1.5">
                    {factorEntries.map(([key, val], i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                        <span className="text-red-400 mt-0.5">-</span>
                        <span><strong>{key}:</strong> {val}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {riskResult.recommendations?.length > 0 && (
                <div>
                  <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Recommendations</h3>
                  <div className="space-y-1.5">
                    {riskResult.recommendations.map((r, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                        <span className="text-primary mt-0.5">-</span>
                        {r}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-muted-foreground text-sm">
              Select an employee and click "Risk Score" to analyze
            </div>
          )}
        </div>

        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-sm font-semibold text-foreground">Behavior Analysis</h2>
          </div>
          {behaviorResult ? (
            <div className="p-5 space-y-4">
              {behaviorResult.behavior_summary && (
                <div className="p-3 bg-muted rounded-lg">
                  <p className="text-sm text-foreground/80">{behaviorResult.behavior_summary}</p>
                </div>
              )}
              {behaviorResult.patterns?.length > 0 && (
                <div>
                  <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Patterns</h3>
                  <div className="space-y-1.5">
                    {behaviorResult.patterns.map((p, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                        <span className="text-blue-400 mt-0.5">-</span>
                        {p}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {behaviorResult.anomalies?.length > 0 && (
                <div>
                  <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Anomalies</h3>
                  <div className="space-y-1.5">
                    {behaviorResult.anomalies.map((a, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                        <span className="text-yellow-400 mt-0.5">-</span>
                        {a.description}
                        <span className={cn('text-xs px-1.5 py-0.5 rounded', {
                          'bg-red-500/20 text-red-400': a.severity === 'high',
                          'bg-yellow-500/20 text-yellow-400': a.severity !== 'high',
                        })}>{a.severity}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {behaviorResult.trends?.length > 0 && (
                <div>
                  <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Trends</h3>
                  <div className="space-y-1.5">
                    {behaviorResult.trends.map((t, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                        <span className="text-green-400 mt-0.5">-</span>
                        {t.pattern}: {t.frequency} ({t.direction})
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {behaviorResult.potential_causes?.length > 0 && (
                <div>
                  <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Potential Causes</h3>
                  <div className="space-y-1.5">
                    {behaviorResult.potential_causes.map((c, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                        <span className="text-orange-400 mt-0.5">-</span>
                        {c}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {behaviorResult.recommendations?.length > 0 && (
                <div className="p-3 bg-primary/10 border border-primary/20 rounded-lg">
                  <h3 className="text-xs text-primary uppercase tracking-wider mb-1">Recommendations</h3>
                  <div className="space-y-1">
                    {behaviorResult.recommendations.map((r, i) => (
                      <p key={i} className="text-sm text-foreground/80">- {r}</p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-muted-foreground text-sm">
              Select an employee and click "Behavior Analysis" to analyze
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
