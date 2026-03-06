import { useState } from 'react';
import {
  FileText,
  HardDrive,
  Cpu,
  FileCode,
  Download,
  Eye,
  CheckCircle,
  Clock,
  Loader2,
  Copy,
  Hash,
} from 'lucide-react';
import { type Evidence, formatFileSize, formatDate, cn } from '../lib/utils';

const typeIcons: Record<string, React.ElementType> = {
  memory_dump: Cpu,
  disk_image: HardDrive,
  executable: FileCode,
  pcap: FileText,
  log: FileText,
};

const analysisStatusConfig: Record<string, { color: string; icon: React.ElementType }> = {
  completed: { color: 'text-success', icon: CheckCircle },
  in_progress: { color: 'text-accent', icon: Loader2 },
  pending: { color: 'text-text-muted', icon: Clock },
};

interface ArtifactViewerProps {
  evidence: Evidence[];
}

export default function ArtifactViewer({ evidence }: ArtifactViewerProps) {
  const [selected, setSelected] = useState<Evidence | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const copyHash = (hash: string, label: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(label);
    setTimeout(() => setCopiedHash(null), 1500);
  };

  if (evidence.length === 0) {
    return (
      <div className="card-forensic text-center py-12">
        <FileText className="w-10 h-10 text-text-muted mx-auto mb-3" />
        <p className="text-text-secondary">No evidence items uploaded yet</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Evidence list */}
      <div className="lg:col-span-1 space-y-2">
        <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
          Evidence Items ({evidence.length})
        </h3>
        {evidence.map((e) => {
          const Icon = typeIcons[e.file_type] || FileText;
          const statusConf = analysisStatusConfig[e.analysis_status] || analysisStatusConfig.pending;
          const isSelected = selected?.id === e.id;

          return (
            <button
              key={e.id}
              onClick={() => setSelected(e)}
              className={cn(
                'card-forensic w-full text-left flex items-center gap-3 cursor-pointer',
                isSelected && 'border-accent ring-1 ring-accent/20'
              )}
            >
              <div
                className={cn(
                  'w-10 h-10 rounded-lg flex items-center justify-center shrink-0',
                  isSelected ? 'bg-accent/15' : 'bg-surface-hover'
                )}
              >
                <Icon className={cn('w-5 h-5', isSelected ? 'text-accent' : 'text-text-muted')} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">{e.filename}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-text-muted">{formatFileSize(e.file_size)}</span>
                  <statusConf.icon
                    className={cn(
                      'w-3 h-3',
                      statusConf.color,
                      e.analysis_status === 'in_progress' && 'animate-spin'
                    )}
                  />
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Detail panel */}
      <div className="lg:col-span-2">
        {selected ? (
          <div className="card-forensic space-y-5">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-text-primary">{selected.filename}</h3>
                <p className="text-xs text-text-muted mt-1">
                  Uploaded {formatDate(selected.uploaded_at)}
                </p>
              </div>
              <div className="flex gap-2">
                <button className="btn-outline text-xs flex items-center gap-1.5 px-2 py-1.5">
                  <Eye className="w-3 h-3" />
                  Preview
                </button>
                <button className="btn-primary text-xs flex items-center gap-1.5 px-2 py-1.5">
                  <Download className="w-3 h-3" />
                  Download
                </button>
              </div>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <span className="text-xs text-text-muted block mb-1">File Type</span>
                <span className="text-sm text-text-primary capitalize">
                  {selected.file_type.replace(/_/g, ' ')}
                </span>
              </div>
              <div>
                <span className="text-xs text-text-muted block mb-1">File Size</span>
                <span className="text-sm text-text-primary">
                  {formatFileSize(selected.file_size)}
                </span>
              </div>
              <div>
                <span className="text-xs text-text-muted block mb-1">Analysis</span>
                <span
                  className={cn(
                    'text-sm capitalize',
                    analysisStatusConfig[selected.analysis_status]?.color || 'text-text-primary'
                  )}
                >
                  {selected.analysis_status.replace(/_/g, ' ')}
                </span>
              </div>
            </div>

            {/* Hashes */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider flex items-center gap-1.5">
                <Hash className="w-3.5 h-3.5" />
                File Hashes
              </h4>
              {[
                { label: 'SHA-256', value: selected.sha256 },
                { label: 'MD5', value: selected.md5 },
                { label: 'SHA-1', value: selected.sha1 },
              ].map((hash) => (
                <div
                  key={hash.label}
                  className="flex items-center gap-3 bg-background rounded-lg border border-surface-border p-3"
                >
                  <span className="text-xs text-text-muted font-medium w-16 shrink-0">
                    {hash.label}
                  </span>
                  <code className="font-mono text-xs text-text-primary flex-1 select-all break-all">
                    {hash.value}
                  </code>
                  <button
                    onClick={() => copyHash(hash.value, hash.label)}
                    className="p-1.5 rounded hover:bg-surface-hover transition-colors shrink-0"
                    title="Copy hash"
                  >
                    {copiedHash === hash.label ? (
                      <CheckCircle className="w-3.5 h-3.5 text-success" />
                    ) : (
                      <Copy className="w-3.5 h-3.5 text-text-muted" />
                    )}
                  </button>
                </div>
              ))}
            </div>

            {/* Quick actions */}
            <div className="pt-3 border-t border-surface-border">
              <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
                Quick Actions
              </h4>
              <div className="flex flex-wrap gap-2">
                <button className="btn-outline text-xs">Search VirusTotal</button>
                <button className="btn-outline text-xs">Run YARA Scan</button>
                <button className="btn-outline text-xs">Extract Strings</button>
                <button className="btn-outline text-xs">Generate Timeline</button>
              </div>
            </div>
          </div>
        ) : (
          <div className="card-forensic flex flex-col items-center justify-center py-16 text-center">
            <Eye className="w-10 h-10 text-text-muted mb-3" />
            <p className="text-text-secondary">Select an evidence item to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}
