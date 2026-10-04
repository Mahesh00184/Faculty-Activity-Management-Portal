import React, { useEffect, useState } from 'react';
import { api, API_BASE_URL } from '../services/api';

export default function Publications() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<any>({});
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const role = localStorage.getItem('role') || 'faculty';
  
  const loadData = () => {
    setLoading(true);
    api.get('/publications/')
      .then(data => { setItems(data); setLoading(false); })
      .catch(err => { console.error(err); setLoading(false); });
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await fetch(`${API_BASE_URL}/publications/${editingId}`, {
          method: 'PUT',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}` 
          },
          body: JSON.stringify(formData)
        });
      } else {
        await api.post('/publications/', formData);
      }
      setIsModalOpen(false);
      setFormData({});
      setEditingId(null);
      loadData();
    } catch(err) {
      alert("Error saving publication");
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this publication?")) return;
    try {
      await fetch(`${API_BASE_URL}/publications/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      loadData();
    } catch(err) {
      alert("Error deleting publication");
    }
  };

  const handleStatusChange = async (id: number, newStatus: string) => {
    let comments = "";
    if (newStatus === "CORRECTION REQUIRED" || newStatus === "REJECTED") {
      comments = window.prompt(`Reason for ${newStatus}:`) || "";
      if (!comments) return;
    }
    try {
      await fetch(`${API_BASE_URL}/publications/${id}/status`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}` 
        },
        body: JSON.stringify({ status: newStatus, comments })
      });
      loadData();
    } catch (err: any) {
      alert("Failed to update status");
    }
  };

  const openModal = (pub?: any) => {
    if (pub) {
      setEditingId(pub.id);
      setFormData(pub);
    } else {
      setEditingId(null);
      setFormData({});
    }
    setIsModalOpen(true);
  };

  const filtered = items.filter(i => {
    const matchSearch = (i.title || '').toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'All' || i.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Publications</h2>
        <button onClick={() => openModal()} className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700">+ New Publication</button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b flex gap-4">
          <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search publications..." className="px-3 py-2 border rounded-md text-sm w-64" />
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
         {loading ? <div className="p-12 text-center text-gray-500">Loading...</div> : filtered.length === 0 ? <div className="p-12 text-center text-gray-500">No publications found.</div> : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[800px]">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-sm">
                  <th className="px-6 py-3 font-medium">Title</th>
                  <th className="px-6 py-3 font-medium">Type</th>
                  <th className="px-6 py-3 font-medium">Month</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {filtered.map((pub, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">{pub.title}</td>
                    <td className="px-6 py-4 text-gray-600">{pub.publication_type}</td>
                    <td className="px-6 py-4 text-gray-600">{pub.month}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800`}>
                        {pub.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right flex justify-end gap-2">
                      <button onClick={() => openModal(pub)} className="text-indigo-600 hover:text-indigo-900 font-medium text-sm">Edit</button>
                      <button onClick={() => handleDelete(pub.id)} className="text-red-600 hover:text-red-900 font-medium text-sm">Delete</button>
                      {role === 'admin' && (pub.status === 'SUBMITTED' || pub.status === 'UNDER REVIEW') && (
                        <>
                          <button onClick={() => handleStatusChange(pub.id, 'APPROVED')} className="text-green-600 hover:text-green-900 font-medium text-sm">Approve</button>
                          <button onClick={() => handleStatusChange(pub.id, 'CORRECTION REQUIRED')} className="text-amber-600 hover:text-amber-900 font-medium text-sm">Revise</button>
                          <button onClick={() => handleStatusChange(pub.id, 'REJECTED')} className="text-red-600 hover:text-red-900 font-medium text-sm">Reject</button>
                        </>
                      )}
                      {role === 'faculty' && (pub.status === 'DRAFT' || pub.status === 'CORRECTION REQUIRED') && (
                          <button onClick={() => handleStatusChange(pub.id, 'SUBMITTED')} className="text-blue-600 hover:text-blue-900 font-medium text-sm">Submit</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-xl w-full">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h3 className="text-lg font-semibold">{editingId ? 'Edit Publication' : 'Add Publication'}</h3>
              <button onClick={() => { setIsModalOpen(false); setEditingId(null); setFormData({}); }} className="text-gray-400 hover:text-gray-600">×</button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                <input required type="text" value={formData.title || ''} onChange={e => setFormData({...formData, title: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Publication Type *</label>
                <input required type="text" value={formData.publication_type || ''} placeholder="e.g. Book, Journal" onChange={e => setFormData({...formData, publication_type: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Month/Year</label>
                <input type="text" value={formData.month || ''} onChange={e => setFormData({...formData, month: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => { setIsModalOpen(false); setEditingId(null); setFormData({}); }} className="px-4 py-2 border rounded-md text-sm font-medium text-gray-700">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
