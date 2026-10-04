import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const role = localStorage.getItem('role') || 'faculty';

  useEffect(() => {
    const endpoint = role === 'admin' ? '/analytics/dashboard/admin' : '/analytics/dashboard/faculty';
    api.get(endpoint)
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching data: ", err);
        setLoading(false);
      });
  }, [role]);

  return (
    <div className="p-8">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard overview</h2>
      
      {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="text-sm font-medium text-gray-500 mb-1">{role === 'admin' ? 'Total Activities' : 'My Activities'}</div>
              <div className="text-3xl font-bold text-gray-900">{loading ? '-' : (role === 'admin' ? stats?.total_activities : stats?.my_activities_count) || 0}</div>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="text-sm font-medium text-gray-500 mb-1">Approved</div>
              <div className="text-3xl font-bold text-green-600">{loading ? '-' : (role === 'admin' ? stats?.approved_activities : stats?.approved_count) || 0}</div>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="text-sm font-medium text-gray-500 mb-1">Pending Review</div>
              <div className="text-3xl font-bold text-amber-500">{loading ? '-' : (role === 'admin' ? stats?.pending_approvals : stats?.under_review_count) || 0}</div>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="text-sm font-medium text-gray-500 mb-1">{role === 'admin' ? 'Total Faculty' : 'My Publications'}</div>
              <div className="text-3xl font-bold text-indigo-600">{loading ? '-' : (role === 'admin' ? stats?.total_faculty : stats?.my_publications_count) || 0}</div>
            </div>
          </div>

          {/* Activities List */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h3 className="font-semibold text-gray-900">Recent Activities</h3>
              <Link to="/activities" className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition">
                View All
              </Link>
            </div>
            
            {loading ? (
              <div className="p-6 text-center text-gray-500">Loading activities...</div>
            ) : (!stats?.recent_activities || stats.recent_activities.length === 0) ? (
              <div className="p-12 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h4 className="text-lg font-medium text-gray-900 mb-1">No recent activities</h4>
                <p className="text-gray-500 mb-4">Check back later.</p>
              </div>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-gray-500 text-sm">
                    <th className="px-6 py-3 font-medium">Title</th>
                    <th className="px-6 py-3 font-medium">Organization</th>
                    <th className="px-6 py-3 font-medium">Type</th>
                    <th className="px-6 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-sm">
                  {stats.recent_activities.map((activity: any) => (
                    <tr key={activity.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">{activity.title}</td>
                      <td className="px-6 py-4 text-gray-600">{activity.organization}</td>
                      <td className="px-6 py-4 text-gray-600">{activity.event_type}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                          ${activity.status === 'APPROVED' ? 'bg-green-100 text-green-800' : 
                            (activity.status === 'PENDING' || activity.status === 'UNDER REVIEW') ? 'bg-amber-100 text-amber-800' : 
                            'bg-gray-100 text-gray-800'}`}>
                          {activity.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
    </div>
  );
}
