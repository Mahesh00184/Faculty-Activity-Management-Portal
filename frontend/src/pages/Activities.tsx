import { useEffect, useState } from 'react';
import { api, API_BASE_URL } from '../services/api';


interface Activity {
  id: number;
  title: string;
  organization: string;
  status: string;
  event_type: string;
  month: string;
  start_date: string;
  end_date: string;
}

export default function Activities() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const role = localStorage.getItem('role');

  const loadActivities = () => {
    setLoading(true);
    api.get('/activities/')
      .then(data => {
        setActivities(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching data: ", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadActivities();
  }, []);

  const handleStatusChange = async (id: number, newStatus: string) => {
    let comments = "";
    if (newStatus === "CORRECTION REQUIRED" || newStatus === "REJECTED") {
      comments = window.prompt(`Please provide a reason for marking this as ${newStatus}:`) || "";
      if (!comments) return; // cancel if empty
    }
    
    try {
      await fetch(`${API_BASE_URL}/activities/${id}/status`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}` 
        },
        body: JSON.stringify({ status: newStatus, comments })
      });
      loadActivities();
    } catch (err: any) {
      alert("Failed to update status: " + err.message);
    }
  };

  const filtered = activities.filter(a => {
    const matchSearch = (a.title || '').toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'All' || a.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Activities Management</h2>
        <button className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition shadow-sm">
          + New Activity
        </button>
      </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-4 border-b flex gap-4">
              <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search activities..." className="px-3 py-2 border rounded-md text-sm w-64" />
              <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="px-3 py-2 border rounded-md text-sm text-gray-600">
                <option value="All">All Statuses</option>
                <option value="DRAFT">DRAFT</option>
                <option value="SUBMITTED">SUBMITTED</option>
                <option value="UNDER REVIEW">UNDER REVIEW</option>
                <option value="APPROVED">APPROVED</option>
                <option value="CORRECTION REQUIRED">CORRECTION REQUIRED</option>
                <option value="REJECTED">REJECTED</option>
              </select>
            </div>
            
            {loading ? (
              <div className="p-12 text-center text-gray-500">Loading activities...</div>
            ) : filtered.length === 0 ? (
              <div className="p-12 text-center text-gray-500">No activities found.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[800px]">
                  <thead>
                    <tr className="bg-gray-50 text-gray-500 text-sm">
                      <th className="px-6 py-3 font-medium">Title</th>
                      <th className="px-6 py-3 font-medium">Type</th>
                      <th className="px-6 py-3 font-medium">Date</th>
                      <th className="px-6 py-3 font-medium">Status</th>
                      <th className="px-6 py-3 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-sm">
                    {filtered.map(activity => (
                      <tr key={activity.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 font-medium text-gray-900">{activity.title}</td>
                        <td className="px-6 py-4 text-gray-600">{activity.event_type}</td>
                        <td className="px-6 py-4 text-gray-600">{activity.start_date}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800`}>
                            {activity.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right flex justify-end gap-2">
                           <button className="text-indigo-600 hover:text-indigo-900 font-medium text-sm">Edit</button>
                           {role === 'admin' && (activity.status === 'SUBMITTED' || activity.status === 'UNDER REVIEW') && (
                             <>
                               <button onClick={() => handleStatusChange(activity.id, 'APPROVED')} className="text-green-600 hover:text-green-900 font-medium text-sm">Approve</button>
                               <button onClick={() => handleStatusChange(activity.id, 'CORRECTION REQUIRED')} className="text-amber-600 hover:text-amber-900 font-medium text-sm">Revise</button>
                               <button onClick={() => handleStatusChange(activity.id, 'REJECTED')} className="text-red-600 hover:text-red-900 font-medium text-sm">Reject</button>
                             </>
                           )}
                           {role === 'faculty' && (activity.status === 'DRAFT' || activity.status === 'CORRECTION REQUIRED') && (
                               <button onClick={() => handleStatusChange(activity.id, 'SUBMITTED')} className="text-blue-600 hover:text-blue-900 font-medium text-sm">Submit</button>
                           )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
    </div>
  );
}
