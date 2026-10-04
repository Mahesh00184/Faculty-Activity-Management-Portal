import { useEffect, useState } from 'react';
import { api, API_BASE_URL } from '../services/api';

export default function Notifications() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadNotifications = () => {
    setLoading(true);
    // Since we are operating off limited backend scope context, if the backend lacks notifications, we fallback cleanly
    api.get('/notifications/')
      .then(data => {
        setNotifications(data || []);
        setLoading(false);
      })
      .catch(err => {
        console.warn("Notifications API might not exist yet", err);
        setNotifications([]);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const handleMarkAsRead = async (id: number) => {
    try {
      await fetch(`${API_BASE_URL}/notifications/${id}/read`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      loadNotifications();
    } catch(err) {
      console.error(err);
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Notifications</h2>
        {notifications.length > 0 && (
          <button className="text-sm font-medium text-indigo-600 hover:text-indigo-800">
            Mark all as read
          </button>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-500">Loading notifications...</div>
        ) : notifications.length === 0 ? (
          <div className="p-12 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 bg-gray-50 text-gray-400 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No notifications</h3>
            <p className="text-sm text-gray-500">You're all caught up! Check back later.</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {notifications.map((n, idx) => (
              <li key={idx} className={`p-4 flex items-start gap-4 hover:bg-gray-50 transition ${!n.is_read ? 'bg-indigo-50/30' : ''}`}>
                <div className={`mt-1 w-2.5 h-2.5 rounded-full flex-shrink-0 ${!n.is_read ? 'bg-indigo-600' : 'bg-transparent'}`}></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{n.message}</p>
                  <p className="text-xs text-gray-500 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                </div>
                {!n.is_read && (
                  <button onClick={() => handleMarkAsRead(n.id)} className="text-xs font-medium text-indigo-600 hover:text-indigo-800">
                    Mark as read
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
