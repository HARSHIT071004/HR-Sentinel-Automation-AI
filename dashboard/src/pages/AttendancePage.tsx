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
    <div className="p-3 sm:p-6 space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-lg sm:text-2xl font-bold text-foreground">Attendance Upload</h1>
          <p className="text-sm text-muted-foreground">Upload Excel files to process attendance data</p>
        </div>
        <button
          onClick={() => navigate('/ai')}
          className="w-full sm:w-auto px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          AI Insights
        </button>
      </div>

      <div className="bg-card border border-border rounded-xl p-4 sm:p-6">
        <h2 className="font-semibold text-foreground mb-4">Upload Attendance File</h2>
        <div className="border-2 border-dashed border-border rounded-xl p-6 sm:p-8 text-center hover:border-primary transition-colors">
          <input type="file" accept=".xlsx,.xls,.csv" onChange={handleUpload} className="hidden" id="file-upload" />
          <label htmlFor="file-upload" className="cursor-pointer block">
            <div className="text-3xl sm:text-4xl mb-2 text-muted-foreground">+</div>
            <p className="text-sm sm:text-base text-muted-foreground">Click to upload .xlsx file</p>
            <p className="text-xs text-muted-foreground/60 mt-1">Max 10MB</p>
          </label>
        </div>
        {uploadMutation.isPending && (
          <div className="mt-4 flex items-center gap-2 text-primary">
            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
            Processing...
          </div>
        )}
        {error && <p className="mt-4 text-destructive text-sm">{error}</p>}
        {uploadResult && (
          <div className="mt-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
            <p className="text-green-500 font-medium">Upload Complete</p>
            <div className="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
              <div><span className="text-muted-foreground">Records:</span> <span className="text-foreground font-medium">{uploadResult.records_created}</span></div>
              <div><span className="text-muted-foreground">Warnings:</span> <span className="text-foreground font-medium">{uploadResult.warnings_detected}</span></div>
              <div className="col-span-2 sm:col-span-1"><span className="text-muted-foreground">Status:</span> <span className="text-green-500 font-medium">{uploadResult.status}</span></div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <button onClick={() => navigate('/')} className="px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-xs font-medium hover:bg-primary/90">
                View Dashboard
              </button>
              <button onClick={() => navigate('/employees')} className="px-3 py-1.5 bg-secondary text-secondary-foreground rounded-lg text-xs font-medium hover:bg-secondary/80">
                View Employees
              </button>
              <button onClick={() => navigate('/ai')} className="px-3 py-1.5 bg-primary/20 text-primary rounded-lg text-xs font-medium hover:bg-primary/30">
                AI Insights
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="bg-card border border-border rounded-xl overflow-hidden">
        <div className="px-4 sm:px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="font-semibold text-foreground text-sm sm:text-base">Upload History</h2>
          <span className="text-xs text-muted-foreground">{files?.length || 0} files</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[550px]">
            <thead>
              <tr className="text-left text-xs text-muted-foreground border-b border-border">
                <th className="px-4 sm:px-6 py-3">File</th>
                <th className="px-4 sm:px-6 py-3">Status</th>
                <th className="px-4 sm:px-6 py-3">Rows</th>
                <th className="px-4 sm:px-6 py-3">Records</th>
                <th className="px-4 sm:px-6 py-3">Uploaded</th>
                <th className="px-4 sm:px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {files?.map((file) => (
                <tr key={file.id} className="border-b border-border hover:bg-muted">
                  <td className="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm font-medium text-foreground truncate max-w-[150px] sm:max-w-none">{file.file_name}</td>
                  <td className="px-4 sm:px-6 py-3 sm:py-4">
                    <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                      file.status === 'completed' ? 'bg-green-500/20 text-green-500' : 'bg-yellow-500/20 text-yellow-500'
                    }`}>{file.status}</span>
                  </td>
                  <td className="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-muted-foreground">{file.row_count}</td>
                  <td className="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-muted-foreground">{file.records_created}</td>
                  <td className="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-muted-foreground whitespace-nowrap">{new Date(file.uploaded_at).toLocaleString()}</td>
                  <td className="px-4 sm:px-6 py-3 sm:py-4">
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
                <tr><td colSpan={6} className="px-4 sm:px-6 py-8 text-center text-muted-foreground text-sm">No uploads yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
