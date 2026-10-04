import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const role = localStorage.getItem('role') || 'faculty';

  const logout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const navItemClass = (path: string) => 
    `block px-4 py-2 rounded-md ${location.pathname.startsWith(path) ? 'text-indigo-600 bg-indigo-50 font-medium' : 'text-gray-600 hover:bg-gray-50'}`;

  const mobileNavClass = (path: string) =>
    `flex flex-col items-center ${location.pathname.startsWith(path) ? 'text-indigo-600' : 'text-gray-500'}`;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Navbar */}
      <nav className="bg-white shadow-sm border-b px-6 py-4 flex justify-between items-center z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-md flex items-center justify-center text-white font-bold">FA</div>
          <h1 className="text-xl font-semibold text-gray-900 hidden sm:block">Faculty Portal</h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm font-medium text-gray-600 capitalize">{role} Account</div>
          <button onClick={logout} className="text-sm font-medium text-red-600 hover:text-red-800">Logout</button>
        </div>
      </nav>

      <div className="flex-1 flex overflow-hidden pb-16 md:pb-0">
        {/* Desktop Sidebar */}
        <aside className="w-64 bg-white border-r hidden md:block overflow-y-auto">
          <nav className="p-4 space-y-2">
            <Link to="/dashboard" className={navItemClass('/dashboard')}>Dashboard</Link>
            <Link to="/activities" className={navItemClass('/activities')}>Activities</Link>
            <Link to="/publications" className={navItemClass('/publications')}>Publications</Link>
            <Link to="/certificates" className={navItemClass('/certificates')}>Certificates</Link>
            <Link to="/notifications" className={navItemClass('/notifications')}>Notifications</Link>
            {role === 'admin' && (
              <>
                <Link to="/faculty" className={navItemClass('/faculty')}>Faculty</Link>
                <Link to="/analytics" className={navItemClass('/analytics')}>Analytics</Link>
                <Link to="/reports" className={navItemClass('/reports')}>Reports</Link>
              </>
            )}
          </nav>
        </aside>

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      
      {/* Mobile Bottom Nav */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t flex justify-around p-3 z-10 safe-area-bottom">
        <Link to="/dashboard" className={mobileNavClass('/dashboard')}>
           <svg className="w-6 h-6 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
           <span className="text-[10px] font-medium">Home</span>
        </Link>
        <Link to="/activities" className={mobileNavClass('/activities')}>
           <svg className="w-6 h-6 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
           <span className="text-[10px] font-medium">Activity</span>
        </Link>
        <Link to="/publications" className={mobileNavClass('/publications')}>
           <svg className="w-6 h-6 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
           <span className="text-[10px] font-medium">Publish</span>
        </Link>
        {role === 'admin' && (
          <Link to="/faculty" className={mobileNavClass('/faculty')}>
             <svg className="w-6 h-6 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
             <span className="text-[10px] font-medium">Faculty</span>
          </Link>
        )}
      </div>
    </div>
  );
}
