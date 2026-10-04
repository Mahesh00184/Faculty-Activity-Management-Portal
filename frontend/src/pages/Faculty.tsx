import React, { useEffect, useState } from 'react';
import { api, API_BASE_URL } from '../services/api';


interface FacultyProfile {
  id: number;
  name: string;
  employee_code: string;
  designation: string;
  email: string;
  phone: string;
  phd_status: string;
  specialization: string;
  experience: string;
  au_id: string;
  date_of_joining: string;
  activities_count?: number;
}

export default function Faculty() {
  const [facultyList, setFacultyList] = useState<FacultyProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<Partial<FacultyProfile>>({});
  const [formError, setFormError] = useState('');
  const [formSubmitting, setFormSubmitting] = useState(false);

  const loadFaculty = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.get('/faculty/');
      setFacultyList(data);
    } catch (err: any) {
      setError(err.message || "Failed to load faculty");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFaculty();
  }, []);

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this faculty member?")) return;
    try {
      const res = await fetch(`${API_BASE_URL}/faculty/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (!res.ok) throw new Error("Failed to delete");
      loadFaculty();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const openModal = (faculty?: FacultyProfile) => {
    setFormError('');
    if (faculty) {
      setEditingId(faculty.id);
      setFormData(faculty);
    } else {
      setEditingId(null);
      setFormData({});
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setFormData({});
    setEditingId(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormSubmitting(true);
    setFormError('');
    try {
      if (editingId) {
        await fetch(`${API_BASE_URL}/faculty/${editingId}`, {
          method: 'PUT',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}` 
          },
          body: JSON.stringify(formData)
        });
      } else {
        await api.post('/faculty/', formData);
      }
      closeModal();
      loadFaculty();
    } catch (err: any) {
      setFormError(err.message || "Failed to save faculty");
    } finally {
      setFormSubmitting(false);
    }
  };

  const filteredFaculty = facultyList.filter(f => 
    (f.name || '').toLowerCase().includes(search.toLowerCase()) || 
    (f.employee_code || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Faculty Management</h2>
        <button onClick={() => openModal()} className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 shadow-sm">+ Add Faculty</button>
      </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
             <div className="p-4 border-b">
               <input 
                 type="text" 
                 placeholder="Search by name or code..." 
                 value={search}
                 onChange={e => setSearch(e.target.value)}
                 className="w-full md:w-64 px-3 py-2 border rounded-md text-sm"
               />
             </div>
             {error && <div className="p-4 text-red-600 bg-red-50 border-b border-red-100">{error}</div>}
             {loading ? (
              <div className="p-12 text-center text-gray-500">Loading faculty...</div>
            ) : filteredFaculty.length === 0 ? (
              <div className="p-12 text-center text-gray-500">No faculty members found.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[800px]">
                  <thead>
                    <tr className="bg-gray-50 text-gray-500 text-sm">
                      <th className="px-6 py-3 font-medium">Name</th>
                      <th className="px-6 py-3 font-medium">Emp Code</th>
                      <th className="px-6 py-3 font-medium">Designation</th>
                      <th className="px-6 py-3 font-medium">Email</th>
                      <th className="px-6 py-3 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-sm">
                    {filteredFaculty.map(fac => (
                      <tr key={fac.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 font-medium text-gray-900">{fac.name}</td>
                        <td className="px-6 py-4 text-gray-600">{fac.employee_code}</td>
                        <td className="px-6 py-4 text-gray-600">{fac.designation}</td>
                        <td className="px-6 py-4 text-gray-600">{fac.email}</td>
                        <td className="px-6 py-4 text-right">
                           <button onClick={() => openModal(fac)} className="text-indigo-600 hover:text-indigo-900 font-medium text-sm mr-4">Edit</button>
                           <button onClick={() => handleDelete(fac.id)} className="text-red-600 hover:text-red-900 font-medium text-sm">Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>


      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h3 className="text-lg font-semibold">{editingId ? 'Edit Faculty' : 'Add Faculty'}</h3>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600">×</button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {formError && <div className="p-3 bg-red-50 text-red-600 text-sm rounded">{formError}</div>}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input required type="text" value={formData.name || ''} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Employee Code *</label>
                  <input required type="text" value={formData.employee_code || ''} onChange={e => setFormData({...formData, employee_code: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input type="email" value={formData.email || ''} onChange={e => setFormData({...formData, email: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Designation</label>
                  <input type="text" value={formData.designation || ''} onChange={e => setFormData({...formData, designation: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">PhD Status</label>
                  <input type="text" value={formData.phd_status || ''} onChange={e => setFormData({...formData, phd_status: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Specialization</label>
                  <input type="text" value={formData.specialization || ''} onChange={e => setFormData({...formData, specialization: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={closeModal} className="px-4 py-2 border rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
                <button type="submit" disabled={formSubmitting} className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
                  {formSubmitting ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
