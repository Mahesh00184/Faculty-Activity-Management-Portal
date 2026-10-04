import { useEffect, useState } from 'react';
import { api, API_BASE_URL } from '../services/api';

export default function Certificates() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    setLoading(true);
    api.get('/certificates/')
      .then(data => { setItems(data); setLoading(false); })
      .catch(err => { console.error(err); setLoading(false); });
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this certificate?")) return;
    try {
      await fetch(`${API_BASE_URL}/certificates/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      loadData();
    } catch(err) {
      alert("Error deleting certificate");
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Certificates</h2>
        <div>
          <input type="file" id="cert-upload" className="hidden" onChange={e => {
              if (e.target.files && e.target.files[0]) {
                  const formData = new FormData();
                  formData.append('file', e.target.files[0]);
                  formData.append('title', e.target.files[0].name);
                  fetch(`${API_BASE_URL}/certificates/upload`, {
                      method: 'POST',
                      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
                      body: formData
                  }).then(() => {
                      loadData();
                  }).catch(() => alert("Failed to upload certificate"));
              }
          }} />
          <button onClick={() => document.getElementById('cert-upload')?.click()} className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700">Upload Certificate</button>
        </div>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
         {loading ? <div className="p-12 text-center text-gray-500">Loading...</div> : items.length === 0 ? <div className="p-12 text-center text-gray-500">No certificates found.</div> : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[800px]">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-sm">
                  <th className="px-6 py-3 font-medium">Title</th>
                  <th className="px-6 py-3 font-medium">File Name</th>
                  <th className="px-6 py-3 font-medium">Uploaded At</th>
                  <th className="px-6 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {items.map((cert, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">{cert.title}</td>
                    <td className="px-6 py-4 text-gray-600">{cert.file_name}</td>
                    <td className="px-6 py-4 text-gray-600">{new Date(cert.uploaded_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-right flex justify-end gap-3">
                        {cert.file_path && <a href={`${API_BASE_URL.replace("/api", "")}/${cert.file_path}`} target="_blank" rel="noreferrer" className="text-indigo-600 font-medium hover:underline">View</a>}
                        <button onClick={() => handleDelete(cert.id)} className="text-red-600 font-medium hover:underline">Delete</button>
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
