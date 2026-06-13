import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import { useNavigate } from 'react-router-dom';

interface Employee {
  id: string;
  employee_id: string;
  user_name: string | null;
  designation: string | null;
  department_name: string | null;
  user_email: string | null;
}

interface RiskResult {
  score: number;
  level: string;
  reasoning: string;
  factors: Record<string, string>;
  recommendations: string[];
}

export default function EmployeesPage() {
  const navigate = useNavigate();
  const [selectedEmployee, setSelectedEmployee] = useState<string | null>(null);
  const [riskResult, setRiskResult] = useState<RiskResult | null>(null);
  const [loadingRisk, setLoadingRisk] = useState(false);

  const { data: employees, isLoading } = useQuery<Employee[]>({
    queryKey: ['employees'],
    queryFn: async () => {
      const res = await apiClient.get('/employees');
      return res.data;
    },
  });

  const analyzeRisk = async (employeeId: string) => {
    setSelectedEmployee(employeeId);
    setLoadingRisk(true);
    try {
      const res = await apiClient.get(`/ai/risk/${employeeId}`);
      setRiskResult(res.data);
    } catch (err: any) {
      setRiskResult(null);
    } finally {
      setLoadingRisk(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'bg-red-500/20 text-red-400';
      case 'high': return 'bg-orange-500/20 text-orange-400';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400';
      default: return 'bg-green-500/20 text-green-400';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Employee Directory</h1>
          <p className="text-[#a1a1aa]">{employees?.length || 0} employees registered</p>
        </div>
        <button
          onClick={() => navigate('/ai')}
          className="px-4 py-2 bg-[#6366f1] text-white rounded-lg text-sm font-medium hover:bg-[#5558e6] transition-colors"
        >
          AI Insights
        </button>
      </div>

      <div className="bg-[#0f0f17] border border-[#1e1e2e] rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-[#a1a1aa]">Loading...</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs text-[#a1a1aa] border-b border-[#1e1e2e]">
                <th className="px-6 py-3">Employee</th>
                <th className="px-6 py-3">Department</th>
                <th className="px-6 py-3">Designation</th>
                <th className="px-6 py-3">Email</th>
                <th className="px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees?.map((emp) => (
                <tr key={emp.id} className="border-b border-[#1e1e2e] hover:bg-[#1a1a2e]">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 bg-[#6366f1]/20 text-[#a78bfa] rounded-full flex items-center justify-center text-sm font-bold">
                        {emp.user_name?.[0] || emp.employee_id[0]}
                      </div>
                      <div>
                        <p className="font-medium text-sm text-white">{emp.user_name || emp.employee_id}</p>
                        <p className="text-xs text-[#a1a1aa]">{emp.employee_id}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-[#a1a1aa]">{emp.department_name || '-'}</td>
                  <td className="px-6 py-4 text-sm text-[#a1a1aa]">{emp.designation || '-'}</td>
                  <td className="px-6 py-4 text-sm text-[#a1a1aa]">{emp.user_email || '-'}</td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => analyzeRisk(emp.employee_id)}
                      disabled={loadingRisk && selectedEmployee === emp.employee_id}
                      className="px-3 py-1.5 bg-[#6366f1]/20 text-[#a78bfa] rounded-lg text-xs font-medium hover:bg-[#6366f1]/30 transition-colors disabled:opacity-50"
                    >
                      {loadingRisk && selectedEmployee === emp.employee_id ? 'Analyzing...' : 'Risk Score'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Risk Result Modal */}
      {riskResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setRiskResult(null)}>
          <div className="bg-[#0f0f17] border border-[#1e1e2e] rounded-xl p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Risk Assessment</h3>
              <button onClick={() => setRiskResult(null)} className="text-[#a1a1aa] hover:text-white">X</button>
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className={`w-16 h-16 rounded-xl flex items-center justify-center ${getRiskColor(riskResult.level)}`}>
                  <span className="text-2xl font-bold">{riskResult.score}</span>
                </div>
                <div>
                  <span className={`px-2 py-1 rounded text-xs font-bold ${getRiskColor(riskResult.level)}`}>
                    {riskResult.level}
                  </span>
                  <p className="text-xs text-[#a1a1aa] mt-1">Risk Level</p>
                </div>
              </div>
              <div>
                <p className="text-xs text-[#a1a1aa] mb-1">Reasoning</p>
                <p className="text-sm text-[#d4d4d8]">{riskResult.reasoning}</p>
              </div>
              {riskResult.recommendations?.length > 0 && (
                <div>
                  <p className="text-xs text-[#a1a1aa] mb-1">Recommendations</p>
                  {riskResult.recommendations.map((r, i) => (
                    <p key={i} className="text-sm text-[#d4d4d8]">- {r}</p>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
