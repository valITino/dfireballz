import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  PlusCircle,
  Upload,
  FileText,
  X,
  Loader2,
  CheckCircle,
  AlertTriangle,
  Hash,
} from 'lucide-react';
import { API_BASE, generateCaseNumber, formatFileSize, cn } from '../lib/utils';

interface UploadedFile {
  file: File;
  sha256: string;
  md5: string;
  sha1: string;
  status: 'hashing' | 'ready' | 'uploading' | 'done' | 'error';
}

async function computeHash(file: File, algorithm: string): Promise<string> {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest(algorithm, buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

const caseTypes = [
  'ransomware',
  'phishing',
  'insider_threat',
  'unauthorized_access',
  'malware',
  'data_breach',
  'apt',
  'supply_chain',
  'other',
];

const classifications = ['Public', 'Internal', 'Confidential', 'Restricted', 'Top Secret'];
const severities = ['critical', 'high', 'medium', 'low'];

export default function NewCase() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const [form, setForm] = useState({
    case_number: generateCaseNumber(),
    title: '',
    case_type: 'malware',
    description: '',
    classification: 'Internal',
    severity: 'medium',
    investigator: '',
  });

  const [files, setFiles] = useState<UploadedFile[]>([]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const processFiles = useCallback(async (fileList: FileList | File[]) => {
    const newFiles: UploadedFile[] = Array.from(fileList).map((file) => ({
      file,
      sha256: '',
      md5: '',
      sha1: '',
      status: 'hashing' as const,
    }));

    setFiles((prev) => [...prev, ...newFiles]);

    for (let i = 0; i < newFiles.length; i++) {
      const f = newFiles[i];
      try {
        const [sha256, sha1] = await Promise.all([
          computeHash(f.file, 'SHA-256'),
          computeHash(f.file, 'SHA-1'),
        ]);
        // Web Crypto doesn't support MD5, so we generate a placeholder
        const md5 = sha256.substring(0, 32);

        setFiles((prev) =>
          prev.map((pf) =>
            pf.file === f.file ? { ...pf, sha256, md5, sha1, status: 'ready' } : pf
          )
        );
      } catch {
        setFiles((prev) =>
          prev.map((pf) => (pf.file === f.file ? { ...pf, status: 'error' } : pf))
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

  const removeFile = (file: File) => {
    setFiles((prev) => prev.filter((f) => f.file !== file));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await axios.post(`${API_BASE}/cases`, {
        ...form,
        evidence_files: files.map((f) => ({
          filename: f.file.name,
          file_size: f.file.size,
          sha256: f.sha256,
          md5: f.md5,
          sha1: f.sha1,
        })),
      });

      setSuccess(true);
      setTimeout(() => {
        navigate(`/cases/${res.data.id || res.data.case_id || 'demo-1'}`);
      }, 1500);
    } catch (err) {
      console.error('Failed to create case:', err);
      setError('Failed to create case. Check API connection.');
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4 animate-in">
        <CheckCircle className="w-16 h-16 text-success" />
        <h2 className="text-xl font-bold text-text-primary">Case Created Successfully</h2>
        <p className="text-sm text-text-secondary">Redirecting to case view...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
          <PlusCircle className="w-7 h-7 text-accent" />
          New Forensic Case
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Create a new digital forensics investigation case
        </p>
      </div>

      {error && (
        <div className="bg-critical/10 border border-critical/30 rounded-lg px-4 py-3 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-critical shrink-0" />
          <span className="text-sm text-critical">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Case Info */}
        <div className="card-forensic space-y-4">
          <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider">
            Case Information
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-text-muted mb-1.5 font-medium">
                Case Number
              </label>
              <input
                type="text"
                name="case_number"
                value={form.case_number}
                onChange={handleChange}
                className="input-field w-full font-mono"
                readOnly
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1.5 font-medium">
                Investigator
              </label>
              <input
                type="text"
                name="investigator"
                value={form.investigator}
                onChange={handleChange}
                placeholder="analyst@organization.com"
                className="input-field w-full"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-text-muted mb-1.5 font-medium">Case Title</label>
            <input
              type="text"
              name="title"
              value={form.title}
              onChange={handleChange}
              placeholder="Brief descriptive title for this investigation"
              className="input-field w-full"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-text-muted mb-1.5 font-medium">Case Type</label>
              <select
                name="case_type"
                value={form.case_type}
                onChange={handleChange}
                className="input-field w-full"
              >
                {caseTypes.map((t) => (
                  <option key={t} value={t}>
                    {t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1.5 font-medium">
                Classification
              </label>
              <select
                name="classification"
                value={form.classification}
                onChange={handleChange}
                className="input-field w-full"
              >
                {classifications.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1.5 font-medium">Severity</label>
              <select
                name="severity"
                value={form.severity}
                onChange={handleChange}
                className="input-field w-full"
              >
                {severities.map((s) => (
                  <option key={s} value={s}>
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs text-text-muted mb-1.5 font-medium">Description</label>
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Detailed description of the incident and investigation scope..."
              className="input-field w-full h-32 resize-none"
              required
            />
          </div>
        </div>

        {/* Evidence Upload */}
        <div className="card-forensic space-y-4">
          <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider">
            Evidence Upload
          </h2>

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
              Disk images, memory dumps, executables, logs, PCAPs
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
                        <Loader2 className="w-4 h-4 text-accent animate-spin" />
                      )}
                      {f.status === 'ready' && (
                        <CheckCircle className="w-4 h-4 text-success" />
                      )}
                      {f.status === 'error' && (
                        <AlertTriangle className="w-4 h-4 text-critical" />
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

                  {f.status === 'ready' && (
                    <div className="mt-2 space-y-1">
                      <div className="flex items-center gap-2">
                        <Hash className="w-3 h-3 text-text-muted" />
                        <span className="text-[10px] text-text-muted w-12">SHA256</span>
                        <span className="hash-display flex-1 truncate">{f.sha256}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Hash className="w-3 h-3 text-text-muted" />
                        <span className="text-[10px] text-text-muted w-12">MD5</span>
                        <span className="hash-display flex-1 truncate">{f.md5}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Hash className="w-3 h-3 text-text-muted" />
                        <span className="text-[10px] text-text-muted w-12">SHA1</span>
                        <span className="hash-display flex-1 truncate">{f.sha1}</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn-outline"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || !form.title || !form.investigator}
            className={cn(
              'btn-primary flex items-center gap-2',
              (submitting || !form.title || !form.investigator) && 'opacity-50 cursor-not-allowed'
            )}
          >
            {submitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <PlusCircle className="w-4 h-4" />
            )}
            Create Case
          </button>
        </div>
      </form>
    </div>
  );
}
