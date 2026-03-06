import { useState, useMemo } from 'react';
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  Filter,
  Copy,
  CheckCircle,
  ExternalLink,
  Globe,
  Hash,
  Mail,
  FileText,
  Network,
} from 'lucide-react';
import { type IoC, type CaseSeverity, formatDate, cn } from '../lib/utils';

const severityBadge: Record<CaseSeverity, string> = {
  critical: 'badge-severity-critical',
  high: 'badge-severity-high',
  medium: 'badge-severity-medium',
  low: 'badge-severity-low',
};

const severityOrder: Record<CaseSeverity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

const typeIcons: Record<string, React.ElementType> = {
  ip: Network,
  domain: Globe,
  hash_sha256: Hash,
  hash_md5: Hash,
  hash_sha1: Hash,
  email: Mail,
  file_path: FileText,
  url: ExternalLink,
};

type SortField = 'type' | 'value' | 'severity' | 'source' | 'first_seen';
type SortDir = 'asc' | 'desc';

interface IoCTableProps {
  iocs: IoC[];
}

export default function IoCTable({ iocs }: IoCTableProps) {
  const [sortField, setSortField] = useState<SortField>('severity');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [copiedValue, setCopiedValue] = useState<string | null>(null);

  const types = useMemo(() => ['all', ...new Set(iocs.map((i) => i.type))], [iocs]);

  const filtered = useMemo(() => {
    let result = [...iocs];
    if (typeFilter !== 'all') {
      result = result.filter((i) => i.type === typeFilter);
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (i) =>
          i.value.toLowerCase().includes(q) ||
          i.source.toLowerCase().includes(q) ||
          i.tags.some((t) => t.toLowerCase().includes(q))
      );
    }
    return result;
  }, [iocs, typeFilter, searchQuery]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case 'severity':
          cmp = severityOrder[a.severity] - severityOrder[b.severity];
          break;
        case 'type':
          cmp = a.type.localeCompare(b.type);
          break;
        case 'value':
          cmp = a.value.localeCompare(b.value);
          break;
        case 'source':
          cmp = a.source.localeCompare(b.source);
          break;
        case 'first_seen':
          cmp = new Date(a.first_seen).getTime() - new Date(b.first_seen).getTime();
          break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [filtered, sortField, sortDir]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ArrowUpDown className="w-3 h-3 text-text-muted" />;
    return sortDir === 'asc' ? (
      <ArrowUp className="w-3 h-3 text-accent" />
    ) : (
      <ArrowDown className="w-3 h-3 text-accent" />
    );
  };

  const copyValue = (val: string) => {
    navigator.clipboard.writeText(val);
    setCopiedValue(val);
    setTimeout(() => setCopiedValue(null), 1500);
  };

  if (iocs.length === 0) {
    return (
      <div className="card-forensic text-center py-12">
        <Search className="w-10 h-10 text-text-muted mx-auto mb-3" />
        <p className="text-text-secondary">No IOCs identified yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search IOCs..."
            className="input-field w-full pl-9 text-sm"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={cn(
                'px-2 py-1 rounded text-xs font-medium transition-colors',
                typeFilter === t
                  ? 'bg-accent text-white'
                  : 'bg-surface border border-surface-border text-text-secondary hover:border-accent/30'
              )}
            >
              {t === 'all' ? 'All' : t.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
        <span className="text-xs text-text-muted ml-auto">{sorted.length} indicators</span>
      </div>

      {/* Table */}
      <div className="card-forensic p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-border">
                {(
                  [
                    ['type', 'Type'],
                    ['value', 'Value'],
                    ['severity', 'Severity'],
                    ['source', 'Source'],
                    ['first_seen', 'First Seen'],
                  ] as [SortField, string][]
                ).map(([field, label]) => (
                  <th
                    key={field}
                    onClick={() => toggleSort(field)}
                    className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider cursor-pointer hover:text-text-primary transition-colors select-none"
                  >
                    <div className="flex items-center gap-1.5">
                      {label}
                      <SortIcon field={field} />
                    </div>
                  </th>
                ))}
                <th className="px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                  Tags
                </th>
                <th className="px-4 py-3 w-10" />
              </tr>
            </thead>
            <tbody>
              {sorted.map((ioc) => {
                const TypeIcon = typeIcons[ioc.type] || Search;
                return (
                  <tr
                    key={ioc.id}
                    className="border-b border-surface-border last:border-0 hover:bg-surface-hover transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <TypeIcon className="w-3.5 h-3.5 text-text-muted" />
                        <span className="text-xs text-text-secondary capitalize">
                          {ioc.type.replace(/_/g, ' ')}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <code className="font-mono text-xs text-text-primary break-all">
                        {ioc.value}
                      </code>
                      {ioc.enrichment && (
                        <div className="flex items-center gap-2 mt-1">
                          {Object.entries(ioc.enrichment).map(([k, v]) => (
                            <span
                              key={k}
                              className="text-[10px] text-text-muted bg-background px-1.5 py-0.5 rounded"
                            >
                              {k}: {String(v)}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={severityBadge[ioc.severity]}>{ioc.severity}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-text-secondary">{ioc.source}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-text-muted whitespace-nowrap">
                        {formatDate(ioc.first_seen)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {ioc.tags.map((tag) => (
                          <span
                            key={tag}
                            className="text-[10px] text-accent bg-accent/10 px-1.5 py-0.5 rounded-full font-medium"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => copyValue(ioc.value)}
                        className="p-1 rounded hover:bg-surface transition-colors"
                        title="Copy value"
                      >
                        {copiedValue === ioc.value ? (
                          <CheckCircle className="w-3.5 h-3.5 text-success" />
                        ) : (
                          <Copy className="w-3.5 h-3.5 text-text-muted" />
                        )}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
