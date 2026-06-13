import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import { useAuthStore } from '../stores/authStore';

interface Stats {
  total_employees: number;
  present_today: number;
  late_today: number;
  missing_punches: number;
  total_warnings: number;
  strike_1_count: number;
  strike_2_count: number;
  strike_3_count: number;
}

interface FeedItem {
  employee_id: string;
  name: string;
  check_in: string | null;
  check_out: string | null;
  status: string;
  strikes: number;
}

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);

  const { data: stats } = useQuery<Stats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard/stats');
      return res.data;
    },
  });

  const { data: feed } = useQuery<FeedItem[]>({
    queryKey: ['dashboard-feed'],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard/feed');
      return res.data;
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Welcome back, {user?.full_name?.split(' ')[0]}</h1>
        <p className="text-[#a1a1aa]">Here is your workforce overview for today</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Total Employees" value={stats?.total_employees ?? 0} />
        <StatCard title="Present Today" value={stats?.present_today ?? 0} />
        <StatCard title="Late Today" value={stats?.late_today ?? 0} />
        <StatCard title="Missing Punches" value={stats?.missing_punches ?? 0} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[#0f0f17] border border-[#1e1e2e] rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-[#1e1e2e] flex items-center justify-between">
            <h2 className="font-semibold text-white">Attendance Feed</h2>
            <span className="text-xs bg-[#1a1a2e] px-2 py-1 rounded-full text-[#a1a1aa]">
              {feed?.length ?? 0} employees
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs text-[#a1a1aa] border-b border-[#1e1e2e]">
                  <th className="px-6 py-3">Employee</th>
                  <th className="px-6 py-3">Check In</th>
                  <th className="px-6 py-3">Check Out</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Strikes</th>
                </tr>
              </thead>
              <tbody>
                {feed?.map((item) => (
                  <tr key={item.employee_id} className="border-b border-[#1e1e2e] hover:bg-[#1a1a2e] transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${
                          item.status === 'Late' ? 'bg-yellow-500/20 text-yellow-500' : 'bg-green-500/20 text-green-500'
                        }`}>
                          {item.name[0]}
                        </div>
                        <div>
                          <p className="font-medium text-sm text-white">{item.name}</p>
                          <p className="text-xs text-[#a1a1aa]">{item.employee_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-[#a1a1aa]">{item.check_in || '-'}</td>
                    <td className="px-6 py-4 text-sm text-[#a1a1aa]">{item.check_out || '-'}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                        item.status === 'Present' ? 'bg-green-500/20 text-green-500' :
                        item.status === 'Late' ? 'bg-yellow-500/20 text-yellow-500' :
                        'bg-red-500/20 text-red-500'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          item.status === 'Present' ? 'bg-green-500' :
                          item.status === 'Late' ? 'bg-yellow-500' : 'bg-red-500'
                        }`}></span>
                        {item.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {item.strikes > 0 ? (
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                          item.strikes === 1 ? 'bg-blue-500/20 text-blue-500' :
                          item.strikes === 2 ? 'bg-orange-500/20 text-orange-500' :
                          'bg-red-500/20 text-red-500'
                        }`}>
                          STRIKE {item.strikes}
                        </span>
                      ) : (
                        <span className="text-xs text-[#a1a1aa]">None</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-[#0f0f17] border border-[#1e1e2e] rounded-xl p-5">
            <h3 className="font-semibold text-white mb-4">Strike Distribution</h3>
            <div className="space-y-3">
              <StrikeBar label="Strike 1 (Friendly)" count={stats?.strike_1_count ?? 0} total={stats?.total_employees ?? 1} />
              <StrikeBar label="Strike 2 (Formal)" count={stats?.strike_2_count ?? 0} total={stats?.total_employees ?? 1} />
              <StrikeBar label="Strike 3 (Final)" count={stats?.strike_3_count ?? 0} total={stats?.total_employees ?? 1} />
            </div>
          </div>

          <div className="bg-[#0f0f17] border border-[#1e1e2e] rounded-xl p-5">
            <h3 className="font-semibold text-white mb-3">AI Insights</h3>
            <div className="space-y-2 text-sm text-[#a1a1aa]">
              <p>{stats?.late_today ?? 0} employees arrived late today</p>
              <p>{stats?.total_warnings ?? 0} warnings issued this month</p>
              <p>Attendance rate: <span className="text-green-500 font-medium">{stats ? Math.round((stats.present_today / stats.total_employees) * 100) : 0}%</span></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: number }) {
  return (
    <div className="bg-[#0f0f17] border border-[#1e1e2e] rounded-xl p-4">
      <p className="text-sm text-[#a1a1aa]">{title}</p>
      <p className="text-3xl font-bold text-white mt-1">{value}</p>
    </div>
  );
}

function StrikeBar({ label, count, total }: { label: string; count: number; total: number }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-[#a1a1aa]">{label}</span>
        <span className="text-white font-medium">{count}</span>
      </div>
      <div className="w-full bg-[#1a1a2e] rounded-full h-2">
        <div className="bg-[#6366f1] h-2 rounded-full transition-all" style={{ width: `${pct}%` }}></div>
      </div>
    </div>
  );
}
