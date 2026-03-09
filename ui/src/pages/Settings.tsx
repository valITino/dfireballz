import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Settings as SettingsIcon,
  Server,
  Key,
  Heart,
  CheckCircle,
  XCircle,
  Loader2,
  Save,
  RefreshCw,
  Cpu,
  Database,
  Globe,
  Terminal,
  AlertTriangle,
  ExternalLink,
} from 'lucide-react';
import { API_BASE, cn } from '../lib/utils';

interface MCPHost {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  status: 'connected' | 'disconnected' | 'checking';
}

interface HealthStatus {
  service: string;
  status: 'healthy' | 'degraded' | 'down' | 'checking';
  latency?: number;
  version?: string;
  icon: React.ElementType;
}

interface ApiKeyStatus {
  configured: boolean;
  masked_value: string;
  env_var: string;
}

const API_KEY_INFO: Record<string, { label: string; signupUrl: string; description: string }> = {
  virustotal: {
    label: 'VirusTotal',
    signupUrl: 'https://www.virustotal.com/gui/my-apikey',
    description: 'File, hash, and URL reputation lookups',
  },
  shodan: {
    label: 'Shodan',
    signupUrl: 'https://account.shodan.io/',
    description: 'Internet-connected device search',
  },
  abuseipdb: {
    label: 'AbuseIPDB',
    signupUrl: 'https://www.abuseipdb.com/account/api',
    description: 'IP address reputation checks',
  },
  urlscan: {
    label: 'URLScan.io',
    signupUrl: 'https://urlscan.io/user/signup',
    description: 'URL scanning and analysis',
  },
  anthropic: {
    label: 'Anthropic',
    signupUrl: 'https://console.anthropic.com/settings/keys',
    description: 'Required for Claude Code in Docker (make claude-code)',
  },
};

export default function Settings() {
  const [selectedHost, setSelectedHost] = useState('claude-code');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  const [apiKeys, setApiKeys] = useState<Record<string, string>>({
    virustotal: '',
    shodan: '',
    abuseipdb: '',
    urlscan: '',
    anthropic: '',
  });

  const [apiKeyStatus, setApiKeyStatus] = useState<Record<string, ApiKeyStatus>>({});

  const [health, setHealth] = useState<HealthStatus[]>([
    { service: 'DFIReballz API', status: 'checking', icon: Server },
    { service: 'MCP Servers', status: 'checking', icon: Cpu },
    { service: 'Database', status: 'checking', icon: Database },
    { service: 'Redis Cache', status: 'checking', icon: Globe },
  ]);

  const mcpHosts: MCPHost[] = [
    {
      id: 'claude-code',
      name: 'Claude Code',
      description: 'Anthropic Claude Code CLI with native MCP support. Best for development workflows.',
      icon: Terminal,
      status: selectedHost === 'claude-code' ? 'connected' : 'disconnected',
    },
    {
      id: 'claude-desktop',
      name: 'Claude Desktop',
      description: 'Claude Desktop app with MCP integration. GUI-based interaction with tools.',
      icon: Cpu,
      status: selectedHost === 'claude-desktop' ? 'connected' : 'disconnected',
    },
    {
      id: 'mcphost-ollama',
      name: 'MCPHost + Ollama',
      description: 'Local LLM via Ollama with MCPHost bridge. Fully offline, privacy-first.',
      icon: Server,
      status: selectedHost === 'mcphost-ollama' ? 'connected' : 'disconnected',
    },
    {
      id: 'openwebui-ollama',
      name: 'Open WebUI + Ollama',
      description: 'Open WebUI frontend with Ollama backend. Self-hosted with web interface.',
      icon: Globe,
      status: selectedHost === 'openwebui-ollama' ? 'connected' : 'disconnected',
    },
  ];

  // Load settings from orchestrator on mount
  useEffect(() => {
    loadSettings();
    checkHealth();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/settings`, { timeout: 5000 });
      if (res.data.mcp_host) {
        setSelectedHost(res.data.mcp_host);
      }
      if (res.data.api_keys) {
        setApiKeyStatus(res.data.api_keys);
      }
    } catch {
      // API may be down — show empty state
    }
    setLoading(false);
  };

  const checkHealth = async () => {
    setHealth((prev) => prev.map((h) => ({ ...h, status: 'checking' as const })));

    // Check API + services via /health endpoint
    try {
      const start = Date.now();
      const res = await axios.get(`${API_BASE}/health`, { timeout: 5000 });
      const latency = Date.now() - start;
      const services = res.data?.services || {};

      setHealth((prev) =>
        prev.map((h) => {
          if (h.service === 'DFIReballz API') {
            return { ...h, status: 'healthy', latency, version: res.data?.version || '1.0.0' };
          }
          if (h.service === 'Database') {
            return { ...h, status: services.database === 'up' ? 'healthy' : 'down', latency };
          }
          if (h.service === 'Redis Cache') {
            return { ...h, status: services.redis === 'up' ? 'healthy' : 'down', latency };
          }
          return h;
        })
      );
    } catch {
      setHealth((prev) =>
        prev.map((h) =>
          ['DFIReballz API', 'Database', 'Redis Cache'].includes(h.service)
            ? { ...h, status: 'down' }
            : h
        )
      );
    }

    // Check MCP servers via /settings/mcp-status
    try {
      const res = await axios.get(`${API_BASE}/settings/mcp-status`, { timeout: 15000 });
      const statuses = Object.values(res.data) as Array<{ status: string }>;
      const healthyCount = statuses.filter((s) => s.status === 'healthy').length;
      const totalCount = statuses.length;

      setHealth((prev) =>
        prev.map((h) => {
          if (h.service === 'MCP Servers') {
            if (healthyCount === totalCount) return { ...h, status: 'healthy' };
            if (healthyCount > 0) return { ...h, status: 'degraded' };
            return { ...h, status: 'down' };
          }
          return h;
        })
      );
    } catch {
      setHealth((prev) =>
        prev.map((h) => (h.service === 'MCP Servers' ? { ...h, status: 'down' } : h))
      );
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Only send keys that the user actually typed (non-empty)
      const keysToSend: Record<string, string> = {};
      for (const [key, value] of Object.entries(apiKeys)) {
        if (value.trim()) {
          keysToSend[key] = value.trim();
        }
      }

      await axios.post(`${API_BASE}/settings`, {
        mcp_host: selectedHost,
        api_keys: keysToSend,
      });

      // Reload to get updated masked values
      await loadSettings();

      // Clear the input fields after successful save
      setApiKeys((prev) => {
        const cleared: Record<string, string> = {};
        for (const key of Object.keys(prev)) {
          cleared[key] = '';
        }
        return cleared;
      });

      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // Settings save may fail if API is down
    }
    setSaving(false);
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-success" />;
      case 'degraded':
        return <AlertTriangle className="w-4 h-4 text-warning" />;
      case 'down':
      case 'disconnected':
        return <XCircle className="w-4 h-4 text-critical" />;
      case 'checking':
        return <Loader2 className="w-4 h-4 text-accent animate-spin" />;
      default:
        return null;
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return 'border-success/30 bg-success/5';
      case 'degraded':
        return 'border-warning/30 bg-warning/5';
      case 'down':
      case 'disconnected':
        return 'border-critical/30 bg-critical/5';
      default:
        return 'border-surface-border';
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
          <SettingsIcon className="w-7 h-7 text-accent" />
          Settings
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Configure MCP host, API keys, and system preferences
        </p>
      </div>

      {/* System Health */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <Heart className="w-4 h-4 text-critical" />
            System Health
          </h2>
          <button onClick={checkHealth} className="btn-outline text-xs flex items-center gap-1.5 px-2 py-1">
            <RefreshCw className="w-3 h-3" />
            Refresh
          </button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {health.map((h) => (
            <div
              key={h.service}
              className={cn('card-forensic border', statusColor(h.status))}
            >
              <div className="flex items-center justify-between mb-2">
                <h.icon className="w-5 h-5 text-text-muted" />
                {statusIcon(h.status)}
              </div>
              <p className="text-sm font-medium text-text-primary">{h.service}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-text-muted capitalize">{h.status}</span>
                {h.latency !== undefined && (
                  <span className="text-xs text-text-muted">{h.latency}ms</span>
                )}
              </div>
              {h.version && (
                <span className="text-[10px] text-text-muted font-mono mt-1 block">
                  v{h.version}
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* MCP Host Selector */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
          <Server className="w-4 h-4 text-accent" />
          MCP Host Configuration
        </h2>
        <p className="text-xs text-text-muted">
          The AI chat runs in your MCP host (not in this browser UI). This dashboard is for case management, evidence, and reports.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {mcpHosts.map((host) => (
            <button
              key={host.id}
              onClick={() => setSelectedHost(host.id)}
              className={cn(
                'card-forensic text-left transition-all cursor-pointer',
                selectedHost === host.id
                  ? 'border-accent ring-1 ring-accent/30'
                  : 'hover:border-accent/30'
              )}
            >
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    'w-10 h-10 rounded-lg flex items-center justify-center shrink-0',
                    selectedHost === host.id ? 'bg-accent/15' : 'bg-surface-hover'
                  )}
                >
                  <host.icon
                    className={cn(
                      'w-5 h-5',
                      selectedHost === host.id ? 'text-accent' : 'text-text-muted'
                    )}
                  />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-text-primary">{host.name}</p>
                    {selectedHost === host.id && (
                      <span className="text-[10px] bg-accent/15 text-accent px-1.5 py-0.5 rounded-full font-medium">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                    {host.description}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* API Keys */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
          <Key className="w-4 h-4 text-warning" />
          API Keys
        </h2>
        <p className="text-xs text-text-muted">
          Keys entered during <code className="bg-surface-hover px-1 rounded">make setup</code> are loaded automatically.
          You can update them here — changes apply immediately but won't persist across container restarts unless you also update <code className="bg-surface-hover px-1 rounded">.env</code>.
        </p>
        <div className="card-forensic space-y-5">
          {loading ? (
            <div className="flex items-center gap-2 py-4 justify-center text-text-muted">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Loading API key status...</span>
            </div>
          ) : (
            Object.entries(API_KEY_INFO).map(([key, info]) => {
              const status = apiKeyStatus[key];
              const isConfigured = status?.configured ?? false;

              return (
                <div key={key}>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs text-text-muted font-medium flex items-center gap-2">
                      {info.label} API Key
                      {isConfigured ? (
                        <span className="inline-flex items-center gap-1 text-[10px] text-success bg-success/10 px-1.5 py-0.5 rounded-full">
                          <CheckCircle className="w-2.5 h-2.5" />
                          Configured
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[10px] text-warning bg-warning/10 px-1.5 py-0.5 rounded-full">
                          <AlertTriangle className="w-2.5 h-2.5" />
                          Not set
                        </span>
                      )}
                    </label>
                    <a
                      href={info.signupUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-accent hover:underline flex items-center gap-0.5"
                    >
                      Get key <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  </div>
                  <p className="text-[10px] text-text-muted mb-1.5">{info.description}</p>
                  <input
                    type="password"
                    value={apiKeys[key] || ''}
                    onChange={(e) => setApiKeys((prev) => ({ ...prev, [key]: e.target.value }))}
                    placeholder={
                      isConfigured
                        ? `Current: ${status.masked_value} (enter new value to replace)`
                        : `Enter ${info.label} API key...`
                    }
                    className="input-field w-full font-mono text-sm"
                  />
                </div>
              );
            })
          )}
        </div>
      </section>

      {/* Save */}
      <div className="flex items-center justify-end gap-3 pb-8">
        <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
          {saving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : saved ? (
            <CheckCircle className="w-4 h-4" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {saved ? 'Saved!' : saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}
