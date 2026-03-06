import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  ArrowLeft,
  Clock,
  FileText,
  Search,
  Activity,
  BookOpen,
  Download,
  Loader2,
  AlertTriangle,
  User,
  Tag,
  Shield,
} from 'lucide-react';
import {
  API_BASE,
  type Case,
  type IoC,
  type Finding,
  type TimelineEvent,
  type Evidence,
  formatDate,
  cn,
} from '../lib/utils';
import Timeline from '../components/Timeline';
import ArtifactViewer from '../components/ArtifactViewer';
import IoCTable from '../components/IoCTable';
import ReportExport from '../components/ReportExport';

const tabs = [
  { id: 'overview', label: 'Overview', icon: FileText },
  { id: 'timeline', label: 'Timeline', icon: Clock },
  { id: 'evidence', label: 'Evidence', icon: Search },
  { id: 'iocs', label: 'IOCs', icon: AlertTriangle },
  { id: 'findings', label: 'Findings', icon: Activity },
  { id: 'playbooks', label: 'Playbook Runs', icon: BookOpen },
  { id: 'report', label: 'Report', icon: Download },
] as const;

type TabId = (typeof tabs)[number]['id'];

const severityBadge: Record<string, string> = {
  critical: 'badge-severity-critical',
  high: 'badge-severity-high',
  medium: 'badge-severity-medium',
  low: 'badge-severity-low',
};

const statusColors: Record<string, string> = {
  open: 'bg-accent text-accent',
  in_progress: 'bg-warning text-warning',
  closed: 'bg-success text-success',
  archived: 'bg-text-muted text-text-muted',
};

// Demo data for when API is unavailable
const demoCase: Case = {
  id: 'demo-1',
  case_number: 'DFIR-2026-0001',
  title: 'Ransomware Incident - Finance Dept',
  description:
    'Suspected LockBit ransomware detected on multiple workstations in the finance department. Initial detection via EDR alert on WS-FIN-04. Evidence of lateral movement through PsExec and compromised service accounts.',
  case_type: 'ransomware',
  classification: 'Confidential',
  severity: 'critical',
  status: 'in_progress',
  investigator: 'analyst@dfireballz.io',
  created_at: '2026-03-05T14:30:00Z',
  updated_at: '2026-03-06T09:15:00Z',
  ioc_count: 47,
  finding_count: 12,
  evidence_count: 8,
};

const demoTimeline: TimelineEvent[] = [
  { id: '1', timestamp: '2026-03-05T14:30:00Z', source: 'EDR', event_type: 'alert', description: 'CrowdStrike alert: Suspicious PowerShell execution on WS-FIN-04', severity: 'critical' },
  { id: '2', timestamp: '2026-03-05T14:35:00Z', source: 'SIEM', event_type: 'correlation', description: 'Correlated lateral movement attempts from WS-FIN-04 to DC-01', severity: 'critical' },
  { id: '3', timestamp: '2026-03-05T14:45:00Z', source: 'Firewall', event_type: 'network', description: 'Outbound connection to C2: 185.220.101.42:443', severity: 'high' },
  { id: '4', timestamp: '2026-03-05T15:00:00Z', source: 'AD', event_type: 'auth', description: 'Service account svc_backup used from unusual source', severity: 'high' },
  { id: '5', timestamp: '2026-03-05T15:30:00Z', source: 'File System', event_type: 'modification', description: 'Ransom note README.txt dropped in multiple directories', severity: 'critical' },
  { id: '6', timestamp: '2026-03-05T16:00:00Z', source: 'Analyst', event_type: 'action', description: 'Workstation WS-FIN-04 isolated from network', severity: 'medium' },
];

const demoEvidence: Evidence[] = [
  { id: 'e1', case_id: 'demo-1', filename: 'memory_dump_ws04.raw', file_type: 'memory_dump', file_size: 4294967296, sha256: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2', md5: 'a1b2c3d4e5f6a1b2c3d4e5f6', sha1: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4', uploaded_at: '2026-03-05T16:30:00Z', analysis_status: 'completed' },
  { id: 'e2', case_id: 'demo-1', filename: 'ws04_disk_image.e01', file_type: 'disk_image', file_size: 107374182400, sha256: 'b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3', md5: 'b2c3d4e5f6a1b2c3d4e5f6a1', sha1: 'b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5', uploaded_at: '2026-03-05T18:00:00Z', analysis_status: 'in_progress' },
  { id: 'e3', case_id: 'demo-1', filename: 'suspicious.exe', file_type: 'executable', file_size: 2457600, sha256: 'c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4', md5: 'c3d4e5f6a1b2c3d4e5f6a1b2', sha1: 'c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6', uploaded_at: '2026-03-05T17:15:00Z', analysis_status: 'completed' },
];

const demoIocs: IoC[] = [
  { id: 'ioc1', case_id: 'demo-1', type: 'ip', value: '185.220.101.42', source: 'Firewall Logs', severity: 'critical', tags: ['tor-exit', 'c2'], first_seen: '2026-03-05T14:45:00Z', last_seen: '2026-03-05T15:30:00Z', enrichment: { country: 'DE', asn: 'AS205100', reputation: 'malicious' } },
  { id: 'ioc2', case_id: 'demo-1', type: 'hash_sha256', value: 'c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4', source: 'Disk Image', severity: 'critical', tags: ['lockbit', 'ransomware'], first_seen: '2026-03-05T15:00:00Z', last_seen: '2026-03-05T15:00:00Z' },
  { id: 'ioc3', case_id: 'demo-1', type: 'domain', value: 'evil-c2-server.xyz', source: 'DNS Logs', severity: 'high', tags: ['c2', 'dga'], first_seen: '2026-03-05T14:30:00Z', last_seen: '2026-03-05T15:30:00Z', enrichment: { registrar: 'Namecheap', created: '2026-02-28' } },
  { id: 'ioc4', case_id: 'demo-1', type: 'email', value: 'attacker@proton.me', source: 'Ransom Note', severity: 'high', tags: ['ransomware', 'contact'], first_seen: '2026-03-05T15:30:00Z', last_seen: '2026-03-05T15:30:00Z' },
  { id: 'ioc5', case_id: 'demo-1', type: 'file_path', value: 'C:\\Windows\\Temp\\svchost_update.exe', source: 'EDR', severity: 'critical', tags: ['dropper', 'masquerade'], first_seen: '2026-03-05T14:28:00Z', last_seen: '2026-03-05T14:28:00Z' },
];

const demoFindings: Finding[] = [
  { id: 'f1', case_id: 'demo-1', title: 'Initial Access via Phishing Email', description: 'User clicked malicious link in spear-phishing email, downloading trojanized Excel macro.', severity: 'critical', category: 'Initial Access', evidence_refs: ['e3'], created_at: '2026-03-05T17:00:00Z' },
  { id: 'f2', case_id: 'demo-1', title: 'Lateral Movement via PsExec', description: 'Attacker used PsExec with compromised service account to move laterally to 3 additional workstations.', severity: 'critical', category: 'Lateral Movement', evidence_refs: ['e1', 'e2'], created_at: '2026-03-05T18:30:00Z' },
  { id: 'f3', case_id: 'demo-1', title: 'Privilege Escalation - Service Account', description: 'svc_backup account compromised via Kerberoasting attack.', severity: 'high', category: 'Privilege Escalation', evidence_refs: ['e1'], created_at: '2026-03-05T19:00:00Z' },
  { id: 'f4', case_id: 'demo-1', title: 'Data Exfiltration Before Encryption', description: 'Approximately 2.3 GB of data exfiltrated to C2 server prior to ransomware deployment.', severity: 'critical', category: 'Exfiltration', evidence_refs: ['e2'], created_at: '2026-03-06T08:00:00Z' },
];

export default function CaseView() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [iocs, setIocs] = useState<IoC[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [caseRes, timelineRes, evidenceRes, iocRes, findingRes] = await Promise.allSettled([
          axios.get(`${API_BASE}/cases/${caseId}`),
          axios.get(`${API_BASE}/cases/${caseId}/timeline`),
          axios.get(`${API_BASE}/cases/${caseId}/evidence`),
          axios.get(`${API_BASE}/cases/${caseId}/iocs`),
          axios.get(`${API_BASE}/cases/${caseId}/findings`),
        ]);

        if (caseRes.status === 'fulfilled') setCaseData(caseRes.value.data);
        else setCaseData(demoCase);

        if (timelineRes.status === 'fulfilled') setTimeline(timelineRes.value.data);
        else setTimeline(demoTimeline);

        if (evidenceRes.status === 'fulfilled') setEvidence(Array.isArray(evidenceRes.value.data) ? evidenceRes.value.data : []);
        else setEvidence(demoEvidence);

        if (iocRes.status === 'fulfilled') setIocs(Array.isArray(iocRes.value.data) ? iocRes.value.data : []);
        else setIocs(demoIocs);

        if (findingRes.status === 'fulfilled') setFindings(Array.isArray(findingRes.value.data) ? findingRes.value.data : []);
        else setFindings(demoFindings);
      } catch {
        setCaseData(demoCase);
        setTimeline(demoTimeline);
        setEvidence(demoEvidence);
        setIocs(demoIocs);
        setFindings(demoFindings);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [caseId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-10 h-10 text-accent animate-spin" />
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertTriangle className="w-12 h-12 text-warning" />
        <p className="text-text-secondary">Case not found</p>
        <button onClick={() => navigate('/')} className="btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex items-start gap-4">
        <button
          onClick={() => navigate('/')}
          className="mt-1 p-2 rounded-md hover:bg-surface-hover text-text-muted hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-mono text-sm text-text-muted">{caseData.case_number}</span>
            <span className={severityBadge[caseData.severity]}>{caseData.severity}</span>
            <span
              className={cn(
                'text-xs font-medium px-2 py-0.5 rounded-full bg-opacity-15',
                statusColors[caseData.status]
              )}
              style={{
                backgroundColor: `color-mix(in srgb, currentColor 15%, transparent)`,
              }}
            >
              {caseData.status.replace('_', ' ')}
            </span>
          </div>
          <h1 className="text-xl font-bold text-text-primary mt-1">{caseData.title}</h1>
          <p className="text-sm text-text-secondary mt-1 max-w-3xl">{caseData.description}</p>
          <div className="flex items-center gap-4 mt-3 text-xs text-text-muted">
            <span className="flex items-center gap-1">
              <User className="w-3 h-3" />
              {caseData.investigator}
            </span>
            <span className="flex items-center gap-1">
              <Tag className="w-3 h-3" />
              {caseData.case_type}
            </span>
            <span className="flex items-center gap-1">
              <Shield className="w-3 h-3" />
              {caseData.classification}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Updated {formatDate(caseData.updated_at)}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-surface-border">
        <div className="flex gap-1 overflow-x-auto pb-px">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
                activeTab === tab.id
                  ? 'border-accent text-accent'
                  : 'border-transparent text-text-muted hover:text-text-secondary hover:border-surface-border'
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="animate-in">
        {activeTab === 'overview' && (
          <OverviewTab caseData={caseData} findings={findings} iocs={iocs} evidence={evidence} />
        )}
        {activeTab === 'timeline' && <Timeline events={timeline} />}
        {activeTab === 'evidence' && <ArtifactViewer evidence={evidence} />}
        {activeTab === 'iocs' && <IoCTable iocs={iocs} />}
        {activeTab === 'findings' && <FindingsTab findings={findings} />}
        {activeTab === 'playbooks' && <PlaybookRunsTab />}
        {activeTab === 'report' && (
          <ReportExport caseData={caseData} findings={findings} iocs={iocs} timeline={timeline} />
        )}
      </div>
    </div>
  );
}

function OverviewTab({
  caseData,
  findings,
  iocs,
  evidence,
}: {
  caseData: Case;
  findings: Finding[];
  iocs: IoC[];
  evidence: Evidence[];
}) {
  const overviewStats = [
    { label: 'Evidence Items', value: evidence.length, icon: Search },
    { label: 'IOCs Identified', value: iocs.length, icon: AlertTriangle },
    { label: 'Findings', value: findings.length, icon: FileText },
    { label: 'Timeline Events', value: '-', icon: Clock },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {overviewStats.map((s) => (
          <div key={s.label} className="stat-card">
            <s.icon className="w-5 h-5 text-accent mb-1" />
            <span className="text-2xl font-bold text-text-primary">{s.value}</span>
            <span className="text-xs text-text-muted">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card-forensic">
          <h3 className="text-sm font-semibold text-text-primary mb-3">Recent Findings</h3>
          <div className="space-y-3">
            {findings.slice(0, 4).map((f) => (
              <div key={f.id} className="flex items-start gap-3 pb-3 border-b border-surface-border last:border-0">
                <span className={cn(severityBadge[f.severity], 'mt-0.5 shrink-0')}>{f.severity}</span>
                <div>
                  <p className="text-sm font-medium text-text-primary">{f.title}</p>
                  <p className="text-xs text-text-muted mt-0.5">{f.category}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card-forensic">
          <h3 className="text-sm font-semibold text-text-primary mb-3">Top IOCs</h3>
          <div className="space-y-3">
            {iocs.slice(0, 5).map((ioc) => (
              <div key={ioc.id} className="flex items-center gap-3 pb-3 border-b border-surface-border last:border-0">
                <span className={cn(severityBadge[ioc.severity], 'shrink-0')}>{ioc.type}</span>
                <span className="font-mono text-xs text-text-primary truncate">{ioc.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function FindingsTab({ findings }: { findings: Finding[] }) {
  return (
    <div className="space-y-4">
      {findings.length === 0 ? (
        <div className="card-forensic text-center py-12">
          <FileText className="w-10 h-10 text-text-muted mx-auto mb-3" />
          <p className="text-text-secondary">No findings recorded yet</p>
        </div>
      ) : (
        findings.map((f) => (
          <div key={f.id} className="card-forensic">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <span className={severityBadge[f.severity]}>{f.severity}</span>
                <span className="text-xs text-text-muted bg-background px-2 py-0.5 rounded">{f.category}</span>
              </div>
              <span className="text-xs text-text-muted">{formatDate(f.created_at)}</span>
            </div>
            <h3 className="text-sm font-semibold text-text-primary">{f.title}</h3>
            <p className="text-sm text-text-secondary mt-1">{f.description}</p>
            {f.evidence_refs.length > 0 && (
              <div className="flex items-center gap-2 mt-3">
                <span className="text-xs text-text-muted">Evidence:</span>
                {f.evidence_refs.map((ref) => (
                  <span key={ref} className="font-mono text-xs text-accent bg-accent/10 px-2 py-0.5 rounded">
                    {ref}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

function PlaybookRunsTab() {
  const runs = [
    { id: 'r1', name: 'Malware Triage', status: 'completed', started: '2026-03-05T17:00:00Z', duration: '12 min', findings_generated: 3 },
    { id: 'r2', name: 'Memory Analysis', status: 'completed', started: '2026-03-05T18:00:00Z', duration: '45 min', findings_generated: 5 },
    { id: 'r3', name: 'Network IOC Extraction', status: 'running', started: '2026-03-06T08:30:00Z', duration: '-', findings_generated: 0 },
  ];

  return (
    <div className="space-y-4">
      {runs.map((run) => (
        <div key={run.id} className="card-forensic flex items-center gap-4">
          <div
            className={cn(
              'w-10 h-10 rounded-lg flex items-center justify-center',
              run.status === 'completed' ? 'bg-success/15' : 'bg-accent/15'
            )}
          >
            {run.status === 'running' ? (
              <Loader2 className="w-5 h-5 text-accent animate-spin" />
            ) : (
              <BookOpen className="w-5 h-5 text-success" />
            )}
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-text-primary">{run.name}</p>
            <p className="text-xs text-text-muted">
              Started {formatDate(run.started)} | Duration: {run.duration}
            </p>
          </div>
          <div className="text-right">
            <span
              className={cn(
                'text-xs font-medium px-2 py-1 rounded-full',
                run.status === 'completed'
                  ? 'bg-success/15 text-success'
                  : 'bg-accent/15 text-accent'
              )}
            >
              {run.status}
            </span>
            {run.findings_generated > 0 && (
              <p className="text-xs text-text-muted mt-1">{run.findings_generated} findings</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
