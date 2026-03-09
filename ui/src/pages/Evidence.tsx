import { useState, useCallback, useRef, useEffect } from 'react';
import axios from 'axios';
import {
  Upload,
  FileText,
  X,
  Loader2,
  CheckCircle,
  AlertTriangle,
  Hash,
  HardDrive,
  Download,
  Search,
  Filter,
  RefreshCw,
} from 'lucide-react';
import { API_BASE, formatFileSize, cn } from '../lib/utils';

interface UploadedFile {
  file: File;
  sha256: string;
  status: 'hashing' | 'ready' | 'uploading' | 'done' | 'error';
  error?: string;
}

interface EvidenceItem {
  id: string;
  filename: string;
  file_size: number;
  sha256: string;
  evidence_type: string;
  case_id: string;
  uploaded_at: string;
}

async function computeHash(file: File, algorithm: string): Promise<string> {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest(algorithm, buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

export default function Evidence() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCase, setSelectedCase] = useState('');
  const [cases, setCases] = useState<Array<{ id: string; title: string }>>([]);

  useEffect(() => {
    loadEvidence();
    loadCases();
  }, []);

  const loadEvidence = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/cases`);
      const allEvidence: EvidenceItem[] = [];
      for (const c of res.data) {
        try {
          const evRes = await axios.get(`${API_BASE}/cases/${c.id}/evidence`);
          if (Array.isArray(evRes.data)) {
            allEvidence.push(...evRes.data.map((e: EvidenceItem) => ({ ...e, case_id: c.id })));
          }
        } catch {
          // Case may not have evidence
        }
      }
      setEvidence(allEvidence);
    } catch {
      // API not reachable
    }
    setLoading(false);
  };

  const loadCases = async () => {
    try {
      const res = await axios.get(`${API_BASE}/cases`);
      setCases(res.data || []);
    } catch {
      // API not reachable
    }
  };

  const processFiles = useCallback(async (fileList: FileList | File[]) => {
    const newFiles: UploadedFile[] = Array.from(fileList).map((file) => ({
      file,
      sha256: '',
      status: 'hashing' as const,
    }));

    setFiles((prev) => [...prev, ...newFiles]);

    for (const f of newFiles) {
      try {
        const sha256 = await computeHash(f.file, 'SHA-256');
        setFiles((prev) =>
          prev.map((pf) =>
            pf.file === f.file ? { ...pf, sha256, status: 'ready' } : pf
          )
        );
      } catch {
        setFiles((prev) =>
          prev.map((pf) => (pf.file === f.file ? { ...pf, status: 'error', error: 'Hash failed' } : pf))
        );
      }
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (e.dataTransfer.files.length > 0) {
        processFiles(e.dataTransfer.files);
      }
    },
    [processFiles]
  );

  const uploadFile = async (f: UploadedFile) => {
    if (!selectedCase) return;

    setFiles((prev) =>
      prev.map((pf) => (pf.file === f.file ? { ...pf, status: 'uploading' } : pf))
    );

    try {
      const formData = new FormData();
      formData.append('file', f.file);

      await axios.post(`${API_BASE}/cases/${selectedCase}/evidence`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setFiles((prev) =>
        prev.map((pf) => (pf.file === f.file ? { ...pf, status: 'done' } : pf))
      );

      loadEvidence();
    } catch (err) {
      setFiles((prev) =>
        prev.map((pf) =>
          pf.file === f.file ? { ...pf, status: 'error', error: 'Upload failed' } : pf
        )
      );
    }
  };

  const uploadAll = async () => {
    const readyFiles = files.filter((f) => f.status === 'ready');
    for (const f of readyFiles) {
      await uploadFile(f);
    }
  };

  const removeFile = (file: File) => {
    setFiles((prev) => prev.filter((f) => f.file !== file));
  };

  const filteredEvidence = evidence.filter(
    (e) =>
      e.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.sha256?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
            <HardDrive className="w-7 h-7 text-accent" />
            Evidence Management
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Upload, manage, and track digital evidence with chain of custody
          </p>
        </div>
        <button
          onClick={loadEvidence}
          className="btn-outline flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Upload Section */}
      <div className="card-forensic space-y-4">
        <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider">
          Upload Evidence
        </h2>

        <div className="flex items-center gap-4 mb-3">
          <label className="text-xs text-text-muted font-medium">Target Case:</label>
          <select
            value={selectedCase}
            onChange={(e) => setSelectedCase(e.target.value)}
            className="input-field flex-1 max-w-md"
          >
            <option value="">Select a case...</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.title || c.id}
              </option>
            ))}
          </select>
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all',
            dragOver
              ? 'border-accent bg-accent/5'
              : 'border-surface-border hover:border-accent/50 hover:bg-surface-hover'
          )}
        >
          <Upload className="w-10 h-10 text-text-muted mx-auto mb-3" />
          <p className="text-sm text-text-primary font-medium">
            Drop evidence files here or click to browse
          </p>
          <p className="text-xs text-text-muted mt-1">
            Disk images, memory dumps, PCAPs, executables, documents, logs — any file type
          </p>
          <p className="text-xs text-text-muted mt-1">
            SHA256 hashes are computed automatically before upload
          </p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => e.target.files && processFiles(e.target.files)}
          />
        </div>

        {files.length > 0 && (
          <>
            <div className="space-y-3">
              {files.map((f, i) => (
                <div key={i} className="bg-background rounded-lg border border-surface-border p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-accent shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-text-primary">{f.file.name}</p>
                        <p className="text-xs text-text-muted">{formatFileSize(f.file.size)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {f.status === 'hashing' && (
                        <span className="text-xs text-accent flex items-center gap-1">
                          <Loader2 className="w-3 h-3 animate-spin" /> Hashing...
                        </span>
                      )}
                      {f.status === 'ready' && (
                        <CheckCircle className="w-4 h-4 text-success" />
                      )}
                      {f.status === 'uploading' && (
                        <span className="text-xs text-accent flex items-center gap-1">
                          <Loader2 className="w-3 h-3 animate-spin" /> Uploading...
                        </span>
                      )}
                      {f.status === 'done' && (
                        <span className="text-xs text-success flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" /> Uploaded
                        </span>
                      )}
                      {f.status === 'error' && (
                        <span className="text-xs text-critical flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" /> {f.error}
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={() => removeFile(f.file)}
                        className="p-1 hover:bg-surface-hover rounded"
                      >
                        <X className="w-4 h-4 text-text-muted" />
                      </button>
                    </div>
                  </div>

                  {f.sha256 && (
                    <div className="mt-2 flex items-center gap-2">
                      <Hash className="w-3 h-3 text-text-muted" />
                      <span className="text-[10px] text-text-muted w-12">SHA256</span>
                      <span className="hash-display flex-1 truncate">{f.sha256}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-end">
              <button
                onClick={uploadAll}
                disabled={!selectedCase || files.filter((f) => f.status === 'ready').length === 0}
                className={cn(
                  'btn-primary flex items-center gap-2',
                  (!selectedCase || files.filter((f) => f.status === 'ready').length === 0) &&
                    'opacity-50 cursor-not-allowed'
                )}
              >
                <Upload className="w-4 h-4" />
                Upload All ({files.filter((f) => f.status === 'ready').length} files)
              </button>
            </div>
          </>
        )}
      </div>

      {/* Evidence Library */}
      <div className="card-forensic space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider">
            Evidence Library ({evidence.length})
          </h2>
          <div className="relative">
            <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by filename or hash..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-9 w-64"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 text-accent animate-spin" />
          </div>
        ) : filteredEvidence.length === 0 ? (
          <div className="text-center py-12 text-text-muted">
            <HardDrive className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No evidence files found</p>
            <p className="text-xs mt-1">Upload evidence above to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border">
                  <th className="text-left py-2 px-3 text-text-muted font-medium text-xs">Filename</th>
                  <th className="text-left py-2 px-3 text-text-muted font-medium text-xs">Type</th>
                  <th className="text-left py-2 px-3 text-text-muted font-medium text-xs">Size</th>
                  <th className="text-left py-2 px-3 text-text-muted font-medium text-xs">SHA256</th>
                  <th className="text-left py-2 px-3 text-text-muted font-medium text-xs">Uploaded</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvidence.map((e) => (
                  <tr key={e.id} className="border-b border-surface-border/50 hover:bg-surface-hover">
                    <td className="py-2 px-3 font-medium text-text-primary flex items-center gap-2">
                      <FileText className="w-4 h-4 text-accent shrink-0" />
                      {e.filename}
                    </td>
                    <td className="py-2 px-3 text-text-secondary">{e.evidence_type || 'unknown'}</td>
                    <td className="py-2 px-3 text-text-secondary">{formatFileSize(e.file_size)}</td>
                    <td className="py-2 px-3">
                      <span className="hash-display truncate max-w-[200px] inline-block">
                        {e.sha256}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-text-muted text-xs">
                      {new Date(e.uploaded_at).toLocaleDateString()}
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
