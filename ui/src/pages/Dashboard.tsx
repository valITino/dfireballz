import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  FolderOpen,
  AlertTriangle,
  Search,
  FileText,
  Activity,
  ArrowRight,
  Clock,
  Shield,
  Zap,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { API_BASE, type Case, type CaseSeverity, formatDate, cn } from '../lib/utils';

const severityColor: Record<CaseSeverity, string> = {
  critical: 'text-critical',
  high: 'text-warning',
  medium: 'text-accent',
  low: 'text-success',
};

const severityBadge: Record<CaseSeverity, string> = {
  critical: 'badge-severity-critical',
  high: 'badge-severity-high',
  medium: 'badge-severity-medium',
  low: 'badge-severity-low',
};

const statusColor: Record<string, string> = {
  open: 'bg-accent',
  in_progress: 'bg-warning',
  closed: 'bg-success',
  archived: 'bg-text-muted',
};

interface QuickStat {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  change?: string;
}

const quickPlaybooks = [
  { name: 'Triage Analysis', icon: Zap, description: 'Quick evidence triage' },
  { name: 'Malware Analysis', icon: Shield, description: 'Analyze suspicious files' },
  { name: 'Network Forensics', icon: Activity, description: 'Network traffic analysis' },
  { name: 'Memory Forensics', icon: Search, description: 'RAM dump analysis' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_BASE}/cases`);
      setCases(Array.isArray(res.data) ? res.data : res.data.cases || []);
    } catch (err) {
      console.error('Failed to fetch cases:', err);
      setError('Failed to connect to API. Showing sample data.');
      setCases([
        {
          id: 'demo-1',
          case_number: 'DFIR-2026-0001',
          title: 'Ransomware Incident - Finance Dept',
          description: 'Suspected LockBit ransomware detected on multiple workstations',
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
        },
        {
          id: 'demo-2',
          case_number: 'DFIR-2026-0002',
          title: 'Phishing Campaign Investigation',
          description: 'Credential harvesting campaign targeting executive team',
          case_type: 'phishing',
          classification: 'Internal',
          severity: 'high',
          status: 'open',
          investigator: 'analyst@dfireballz.io',
          created_at: '2026-03-04T08:00:00Z',
          updated_at: '2026-03-06T07:45:00Z',
          ioc_count: 23,
          finding_count: 5,
          evidence_count: 3,
        },
        {
          id: 'demo-3',
          case_number: 'DFIR-2026-0003',
          title: 'Insider Threat - Data Exfiltration',
          description: 'Unusual data transfer patterns detected from HR systems',
          case_type: 'insider_threat',
          classification: 'Restricted',
          severity: 'high',
          status: 'in_progress',
          investigator: 'senior.analyst@dfireballz.io',
          created_at: '2026-03-03T11:20:00Z',
          updated_at: '2026-03-05T16:00:00Z',
          ioc_count: 15,
          finding_count: 8,
          evidence_count: 12,
        },
        {
          id: 'demo-4',
          case_number: 'DFIR-2026-0004',
          title: 'Suspicious Login Activity',
          description: 'Multiple failed login attempts from foreign IPs',
          case_type: 'unauthorized_access',
          classification: 'Internal',
          severity: 'medium',
          status: 'open',
          investigator: 'analyst@dfireballz.io',
          created_at: '2026-03-06T02:15:00Z',
          updated_at: '2026-03-06T02:15:00Z',
          ioc_count: 8,
          finding_count: 2,
          evidence_count: 1,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const openCases = cases.filter((c) => c.status === 'open' || c.status === 'in_progress');
  const totalIocs = cases.reduce((sum, c) => sum + (c.ioc_count || 0), 0);
  const totalFindings = cases.reduce((sum, c) => sum + (c.finding_count || 0), 0);

  const stats: QuickStat[] = [
    { label: 'Total Cases', value: cases.length, icon: FolderOpen, color: 'text-accent', change: '+2 this week' },
    { label: 'Open Cases', value: openCases.length, icon: AlertTriangle, color: 'text-warning', change: `${openCases.length} active` },
    { label: 'IOCs Found', value: totalIocs, icon: Search, color: 'text-critical', change: 'Across all cases' },
    { label: 'Findings', value: totalFindings, icon: FileText, color: 'text-success', change: 'This week' },
  ];

  const recentActivity = [
    { time: '2 min ago', text: 'New IOC detected: 185.220.101.42 (Tor exit node)', severity: 'critical' as CaseSeverity },
    { time: '15 min ago', text: 'Playbook "Malware Triage" completed on DFIR-2026-0001', severity: 'medium' as CaseSeverity },
    { time: '1 hour ago', text: 'Evidence uploaded: memory_dump_ws04.raw (4.2 GB)', severity: 'low' as CaseSeverity },
    { time: '2 hours ago', text: 'Finding added: Lateral movement via PsExec detected', severity: 'high' as CaseSeverity },
    { time: '3 hours ago', text: 'Case DFIR-2026-0003 escalated to critical', severity: 'critical' as CaseSeverity },
  ];

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Investigation Dashboard</h1>
          <p className="text-sm text-text-secondary mt-1">
            Overview of active forensic investigations
          </p>
        </div>
        <button onClick={fetchCases} className="btn-outline flex items-center gap-2 text-sm">
          <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-warning/10 border border-warning/30 rounded-lg px-4 py-3 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-warning shrink-0" />
          <span className="text-sm text-warning">{error}</span>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="stat-card">
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-muted uppercase tracking-wider font-medium">
                {stat.label}
              </span>
              <stat.icon className={cn('w-5 h-5', stat.color)} />
            </div>
            <span className="text-3xl font-bold text-text-primary">{stat.value}</span>
            <span className="text-xs text-text-muted">{stat.change}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Cases */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-accent" />
            Active Cases
          </h2>

          {loading ? (
            <div className="flex items-center justify-center h-48 card-forensic">
              <Loader2 className="w-8 h-8 text-accent animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {cases.map((c) => (
                <button
                  key={c.id}
                  onClick={() => navigate(`/cases/${c.id}`)}
                  className="card-forensic text-left group cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="font-mono text-xs text-text-muted">{c.case_number}</span>
                    <span className={severityBadge[c.severity]}>{c.severity}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-text-primary group-hover:text-accent transition-colors line-clamp-1">
                    {c.title}
                  </h3>
                  <p className="text-xs text-text-secondary mt-1 line-clamp-2">{c.description}</p>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-surface-border">
                    <div className="flex items-center gap-2">
                      <div className={cn('w-2 h-2 rounded-full', statusColor[c.status])} />
                      <span className="text-xs text-text-muted capitalize">
                        {c.status.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-text-muted">
                      <span>{c.ioc_count || 0} IOCs</span>
                      <span>{c.finding_count || 0} findings</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 mt-2 text-xs text-text-muted">
                    <Clock className="w-3 h-3" />
                    {formatDate(c.updated_at)}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Recent Activity */}
          <div>
            <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-accent" />
              Recent Activity
            </h2>
            <div className="card-forensic space-y-3">
              {recentActivity.map((item, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 pb-3 border-b border-surface-border last:border-0 last:pb-0"
                >
                  <div
                    className={cn(
                      'w-2 h-2 rounded-full mt-1.5 shrink-0',
                      item.severity === 'critical'
                        ? 'bg-critical'
                        : item.severity === 'high'
                        ? 'bg-warning'
                        : item.severity === 'medium'
                        ? 'bg-accent'
                        : 'bg-success'
                    )}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-text-primary leading-relaxed">{item.text}</p>
                    <span className="text-[10px] text-text-muted">{item.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick-Launch Playbooks */}
          <div>
            <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2 mb-4">
              <Zap className="w-5 h-5 text-warning" />
              Quick Launch
            </h2>
            <div className="space-y-2">
              {quickPlaybooks.map((pb) => (
                <button
                  key={pb.name}
                  onClick={() => navigate('/playbooks')}
                  className="card-forensic w-full flex items-center gap-3 group cursor-pointer"
                >
                  <div className="w-9 h-9 rounded-md bg-accent/10 flex items-center justify-center shrink-0">
                    <pb.icon className="w-4 h-4 text-accent" />
                  </div>
                  <div className="flex-1 text-left">
                    <p className="text-sm font-medium text-text-primary group-hover:text-accent transition-colors">
                      {pb.name}
                    </p>
                    <p className="text-xs text-text-muted">{pb.description}</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-text-muted group-hover:text-accent transition-colors" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
