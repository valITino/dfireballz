import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BookOpen,
  Play,
  Clock,
  Shield,
  Zap,
  Activity,
  Search,
  HardDrive,
  Network,
  Bug,
  FileSearch,
  Lock,
  Loader2,
  CheckCircle,
  AlertTriangle,
  FolderOpen,
} from 'lucide-react';
import { API_BASE, cn, type Playbook, type CaseSeverity } from '../lib/utils';

const severityBadge: Record<CaseSeverity, string> = {
  critical: 'badge-severity-critical',
  high: 'badge-severity-high',
  medium: 'badge-severity-medium',
  low: 'badge-severity-low',
};

const categoryIcons: Record<string, React.ElementType> = {
  triage: Zap,
  malware: Bug,
  network: Network,
  memory: HardDrive,
  disk: FileSearch,
  threat_intel: Shield,
  log_analysis: Activity,
  incident_response: Lock,
};

interface CaseOption {
  id: string;
  case_number: string;
  title: string;
  evidence_count: number;
}

const playbooks: Playbook[] = [
  {
    id: 'pb-triage',
    name: 'Quick Triage',
    description:
      'Rapid initial assessment of evidence. Extracts basic system info, running processes, network connections, and recent file modifications.',
    category: 'triage',
    tools: ['volatility3', 'sleuthkit', 'yara'],
    estimated_duration: '5-10 min',
    severity_target: ['critical', 'high', 'medium', 'low'],
  },
  {
    id: 'pb-malware',
    name: 'Malware Analysis',
    description:
      'Deep analysis of suspicious executables. Static analysis, PE header parsing, string extraction, YARA signature matching, and behavioral indicators.',
    category: 'malware',
    tools: ['yara', 'pe-tools', 'strings', 'capa'],
    estimated_duration: '15-30 min',
    severity_target: ['critical', 'high'],
  },
  {
    id: 'pb-memory',
    name: 'Memory Forensics',
    description:
      'Comprehensive RAM dump analysis. Process tree, DLL injection detection, network connections, registry hives, and credential extraction.',
    category: 'memory',
    tools: ['volatility3', 'rekall', 'yara'],
    estimated_duration: '30-60 min',
    severity_target: ['critical', 'high', 'medium'],
  },
  {
    id: 'pb-network',
    name: 'Network Forensics',
    description:
      'PCAP and network log analysis. Protocol analysis, DNS queries, HTTP sessions, TLS certificate inspection, and C2 beacon detection.',
    category: 'network',
    tools: ['zeek', 'suricata', 'tshark', 'networkx'],
    estimated_duration: '20-45 min',
    severity_target: ['critical', 'high', 'medium'],
  },
  {
    id: 'pb-disk',
    name: 'Disk Image Analysis',
    description:
      'Full disk forensic examination. File system timeline, deleted file recovery, registry analysis, browser artifacts, and persistence mechanisms.',
    category: 'disk',
    tools: ['sleuthkit', 'autopsy', 'plaso', 'regripper'],
    estimated_duration: '45-90 min',
    severity_target: ['critical', 'high'],
  },
  {
    id: 'pb-threat-intel',
    name: 'Threat Intel Enrichment',
    description:
      'Enrich IOCs with threat intelligence. VirusTotal lookups, AbuseIPDB checks, MITRE ATT&CK mapping, and reputation scoring.',
    category: 'threat_intel',
    tools: ['virustotal-api', 'abuseipdb', 'mitre-attack', 'otx'],
    estimated_duration: '5-15 min',
    severity_target: ['critical', 'high', 'medium', 'low'],
  },
  {
    id: 'pb-logs',
    name: 'Log Analysis',
    description:
      'Windows Event Log and syslog analysis. Authentication events, process creation, PowerShell logging, and lateral movement detection.',
    category: 'log_analysis',
    tools: ['evtx-parser', 'sigma', 'chainsaw', 'plaso'],
    estimated_duration: '15-30 min',
    severity_target: ['critical', 'high', 'medium'],
  },
  {
    id: 'pb-ir',
    name: 'Incident Response',
    description:
      'Full IR workflow. Containment verification, scope assessment, root cause analysis, timeline reconstruction, and remediation recommendations.',
    category: 'incident_response',
    tools: ['volatility3', 'sleuthkit', 'plaso', 'yara', 'sigma'],
    estimated_duration: '60-120 min',
    severity_target: ['critical'],
  },
];

export default function Playbooks() {
  const [launching, setLaunching] = useState<string | null>(null);
  const [launched, setLaunched] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<string>('all');
  const [selectedCase, setSelectedCase] = useState<string>('');
  const [cases, setCases] = useState<CaseOption[]>([]);
  const [loadingCases, setLoadingCases] = useState(true);
  const [launchError, setLaunchError] = useState<string | null>(null);

  const categories = ['all', ...new Set(playbooks.map((p) => p.category))];

  const filtered =
    filter === 'all' ? playbooks : playbooks.filter((p) => p.category === filter);

  // Load cases on mount
  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    setLoadingCases(true);
    try {
      const res = await axios.get(`${API_BASE}/cases`, { timeout: 5000 });
      const caseList = (Array.isArray(res.data) ? res.data : []).map(
        (c: { id: string; case_number?: string; title: string; evidence_count?: number }) => ({
          id: c.id,
          case_number: c.case_number || c.id.slice(0, 8),
          title: c.title,
          evidence_count: c.evidence_count ?? 0,
        })
      );
      setCases(caseList);
    } catch {
      setCases([]);
    }
    setLoadingCases(false);
  };

  const handleLaunch = async (playbookId: string) => {
    if (!selectedCase) {
      setLaunchError('Select a case before launching a playbook.');
      setTimeout(() => setLaunchError(null), 4000);
      return;
    }

    const selected = cases.find((c) => c.id === selectedCase);
    if (selected && selected.evidence_count === 0) {
      setLaunchError('The selected case has no evidence. Upload evidence first.');
      setTimeout(() => setLaunchError(null), 4000);
      return;
    }

    setLaunching(playbookId);
    setLaunchError(null);
    try {
      const pb = playbooks.find((p) => p.id === playbookId);
      await axios.post(`${API_BASE}/cases/${selectedCase}/playbooks/run`, {
        playbook_name: pb?.name || playbookId,
      });
      setLaunched((prev) => new Set(prev).add(playbookId));
    } catch {
      setLaunchError('Failed to launch playbook. Check that the orchestrator and MCP servers are healthy.');
      setTimeout(() => setLaunchError(null), 5000);
    }
    setLaunching(null);
  };

  return (
    <div className="space-y-6 animate-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
          <BookOpen className="w-7 h-7 text-accent" />
          Investigation Playbooks
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Automated forensic analysis workflows powered by MCP tools
        </p>
      </div>

      {/* Case Selector */}
      <div className="card-forensic">
        <div className="flex items-center gap-2 mb-2">
          <FolderOpen className="w-4 h-4 text-accent" />
          <h3 className="text-sm font-semibold text-text-primary">Target Case</h3>
        </div>
        <p className="text-xs text-text-muted mb-3">
          Select the case to run playbooks against. The case must have evidence uploaded.
        </p>
        {loadingCases ? (
          <div className="flex items-center gap-2 text-text-muted text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading cases...
          </div>
        ) : cases.length === 0 ? (
          <div className="flex items-center gap-2 text-warning text-sm">
            <AlertTriangle className="w-4 h-4" />
            No cases found. Create a case and upload evidence first.
          </div>
        ) : (
          <select
            value={selectedCase}
            onChange={(e) => {
              setSelectedCase(e.target.value);
              setLaunchError(null);
            }}
            className="input-field w-full text-sm"
          >
            <option value="">-- Select a case --</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.case_number} — {c.title} ({c.evidence_count} evidence item{c.evidence_count !== 1 ? 's' : ''})
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Error Banner */}
      {launchError && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-critical/10 border border-critical/30 text-critical text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {launchError}
        </div>
      )}

      {/* Category filter */}
      <div className="flex gap-2 flex-wrap">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={cn(
              'px-3 py-1.5 rounded-md text-xs font-medium transition-colors capitalize',
              filter === cat
                ? 'bg-accent text-white'
                : 'bg-surface border border-surface-border text-text-secondary hover:text-text-primary hover:border-accent/30'
            )}
          >
            {cat.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Playbook Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((pb) => {
          const Icon = categoryIcons[pb.category] || Search;
          const isLaunching = launching === pb.id;
          const isLaunched = launched.has(pb.id);
          const canLaunch = !!selectedCase;

          return (
            <div key={pb.id} className="card-forensic flex flex-col">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
                  <Icon className="w-5 h-5 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-text-primary">{pb.name}</h3>
                  <span className="text-xs text-text-muted capitalize">
                    {pb.category.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>

              <p className="text-xs text-text-secondary leading-relaxed flex-1">
                {pb.description}
              </p>

              {/* Tools */}
              <div className="flex flex-wrap gap-1.5 mt-3">
                {pb.tools.map((tool) => (
                  <span
                    key={tool}
                    className="font-mono text-[10px] text-text-muted bg-background px-1.5 py-0.5 rounded border border-surface-border"
                  >
                    {tool}
                  </span>
                ))}
              </div>

              {/* Severity targets */}
              <div className="flex items-center gap-1.5 mt-3">
                <span className="text-[10px] text-text-muted">Targets:</span>
                {pb.severity_target.map((s) => (
                  <span key={s} className={cn(severityBadge[s], 'text-[10px] px-1.5 py-0')}>
                    {s}
                  </span>
                ))}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-surface-border">
                <div className="flex items-center gap-1 text-xs text-text-muted">
                  <Clock className="w-3 h-3" />
                  {pb.estimated_duration}
                </div>
                <button
                  onClick={() => handleLaunch(pb.id)}
                  disabled={isLaunching || !canLaunch}
                  title={!canLaunch ? 'Select a case first' : undefined}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
                    !canLaunch
                      ? 'bg-surface-hover text-text-muted cursor-not-allowed opacity-60'
                      : isLaunched
                      ? 'bg-success/15 text-success'
                      : isLaunching
                      ? 'bg-accent/15 text-accent'
                      : 'bg-accent hover:bg-accent-hover text-white'
                  )}
                >
                  {isLaunching ? (
                    <>
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Launching...
                    </>
                  ) : isLaunched ? (
                    <>
                      <CheckCircle className="w-3 h-3" />
                      Launched
                    </>
                  ) : (
                    <>
                      <Play className="w-3 h-3" />
                      Launch
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
