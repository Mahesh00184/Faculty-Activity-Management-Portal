import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell 
} from 'recharts';

export default function Analytics() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const role = localStorage.getItem('role') || 'faculty';
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  useEffect(() => {
    const endpoint = role === 'admin' ? '/analytics/dashboard/admin' : '/analytics/dashboard/faculty';
    api.get(endpoint)
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || "Failed to load analytics");
        setLoading(false);
      });
  }, [role]);

  if (loading) return <div className="p-12 text-center text-gray-500">Loading analytics data...</div>;
  if (error) return <div className="p-8"><div className="p-4 bg-red-50 text-red-600 rounded-lg">{error}</div></div>;
  if (!stats) return <div className="p-12 text-center text-gray-500">No data available</div>;

  // Derive mock charts data from the real dashboard endpoint if exact breakdown endpoints don't exist yet
  // In a real scenario, this would hit `/analytics/activities-by-month` etc.
  const statusData = [
    { name: 'Approved', value: role === 'admin' ? stats.approved_activities || 0 : stats.approved_count || 0 },
    { name: 'Pending', value: role === 'admin' ? stats.pending_approvals || 0 : stats.under_review_count || 0 },
  ];

  const barData = [
    { name: 'Activities', count: role === 'admin' ? stats.total_activities : stats.my_activities_count },
    { name: 'Publications', count: role === 'admin' ? stats.total_faculty : stats.my_publications_count }, // stats reuse for placeholder
  ];

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Analytics Overview</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        
        {/* Status Distribution */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Status Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Volume Comparison */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Data Volume</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: '#F3F4F6' }} />
                <Bar dataKey="count" fill="#4F46E5" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}
