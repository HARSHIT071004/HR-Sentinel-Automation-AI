import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import { useNavigate } from 'react-router-dom';

interface UploadLog {
  id: string;
  file_name: string;
  status: string;
  row_count: number;
  records_created: number;
  uploaded_at: string;
}

export default function AttendancePage() {
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data: files } = useQuery<UploadLog[]>({
    queryKey: ['upload-logs'],
    queryFn: async () => {
      const res = await apiClient.get('/attendance/files');
      return res.data;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiClient.post('/attendance/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
    onSuccess: (data) => {
      setUploadResult(data);
      setError('');
      queryClient.invalidateQueries({ queryKey: ['upload-logs'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-feed'] });
      queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Upload failed');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (fileId: string) => {
      await apiClient.delete(`/attendance/files/${fileId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['upload-logs'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-feed'] });
      queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
  });

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Attendance Upload</h1>
          <p className="text-[#a1a1aa]">Upload Excel files to process attendance data</p>
        </div>
        <button
          onClick={() => navigate('/ai')}
          className="px-4 py-2 bg-[#6366f1] text-white rounded-lg text-sm font-medium hover:bg-[#5558e6] transition-colors"
        >
          AI Insights
        </button>
      </div>

      <div className="bg-[#0f0f17] border border-[#1e1e2e] rounded-xl p-6">
        <h2 className="font-semibold text-white mb-4">Upload Attendance File</h2>
        <div className="border-2 border-dashed border-[#1e1e2e] rounded-xl p-8 text-center hover:border-[#6366f1] transition-colors">
          <input type="file" accept=".xlsx,.xls,.csv" onChange={handleUpload} className="hidden" id="file-upload" />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="text-4xl mb-2 text-[#a1a1aa]">+</div>
            <p className="text-[#a1a1aa]">Click to upload .xlsx file</p>
            <p className="text-xs text-[#a1a1aa]/60 mt-1">Max 10MB</p>
          </label>
        </div>
        {uploadMutation.isPending && (
          <div className="mt-4 flex items-center gap-2 text-[#6366f1]">
            <div className="w-4 h-4 border-2 border-[#6366f1] border-t-transparent rounded-full animate-spin"></div>
            Processing...
          </div>
        )}
        {error && <p className="mt-4 text-[#ef4444] text-sm">{error}</p>}
        {uploadResult && (
          <div className="mt-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
            <p className="text-green-500 font-medium">Upload Complete</p>
            <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
              <div><span className="text-[#a1a1aa]">Records:</span> <span className="text-white font-medium">{uploadResult.records_created}</span></div>
              <div><span className="text-[#a1a1aa]">Warnings:</span> <span className="text-white font-medium">{uploadResult.warnings_detected}</span></div>
              <div><span className="text-[#a1a1aa]">Status:</span> <span className="text-green-500 font-medium">{uploadResult.status}</span></div>
            </div>
            <div className="mt-3 flex gap-2">
              <button onClick={() => navigate('/')} className="px-3 py-1.5 bg-[#6366f1] text-white rounded-lg text-xs font-medium hover:bg-[#5558e6]">
                View Dashboard
              </button>
              <button onClick={() => navigate('/employees')} className="px-3 py-1.5 bg-[#1a1a2e] text-[#a1a1aa] rounded-lg text-xs font-medium hover:bg-[#252540]">
                View Employees
              </button>
              <button onClick={() => navigate('/ai')} className="px-3 py-1.5 bg-[#8b5cf6]/20 text-[#a78bfa] rounded-lg text-xs font-medium hover:bg-[#8b5cf6]/30">
                AI Insights
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="bg-[#0f0f17] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[#1e1e2e] flex items-center justify-between">
          <h2 className="font-semibold text-white">Upload History</h2>
          <span className="text-xs text-[#a1a1aa]">{files?.length || 0} files</span>
        </div>
        <table className="w-full">
          <thead>
            <tr className="text-left text-xs text-[#a1a1aa] border-b border-[#1e1e2e]">
              <th className="px-6 py-3">File</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Rows</th>
              <th className="px-6 py-3">Records</th>
              <th className="px-6 py-3">Uploaded</th>
              <th className="px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {files?.map((file) => (
              <tr key={file.id} className="border-b border-[#1e1e2e] hover:bg-[#1a1a2e]">
                <td className="px-6 py-4 text-sm font-medium text-white">{file.file_name}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                    file.status === 'completed' ? 'bg-green-500/20 text-green-500' : 'bg-yellow-500/20 text-yellow-500'
                  }`}>{file.status}</span>
                </td>
                <td className="px-6 py-4 text-sm text-[#a1a1aa]">{file.row_count}</td>
                <td className="px-6 py-4 text-sm text-[#a1a1aa]">{file.records_created}</td>
                <td className="px-6 py-4 text-sm text-[#a1a1aa]">{new Date(file.uploaded_at).toLocaleString()}</td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => {
                      if (confirm('Delete this file?')) {
                        deleteMutation.mutate(file.id);
                      }
                    }}
                    className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs hover:bg-red-500/30"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {(!files || files.length === 0) && (
              <tr><td colSpan={6} className="px-6 py-8 text-center text-[#a1a1aa]">No uploads yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
