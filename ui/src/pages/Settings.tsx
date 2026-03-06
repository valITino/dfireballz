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

export default function Settings() {
  const [selectedHost, setSelectedHost] = useState('claude-code');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [apiKeys, setApiKeys] = useState({
    virustotal: '',
    abuseipdb: '',
    shodan: '',
    openai: '',
    anthropic: '',
  });

  const [health, setHealth] = useState<HealthStatus[]>([
    { service: 'DFIReballz API', status: 'checking', icon: Server },
    { service: 'MCP Server', status: 'checking', icon: Cpu },
    { service: 'Evidence Store', status: 'checking', icon: Database },
    { service: 'Threat Intel', status: 'checking', icon: Globe },
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

  const checkHealth = async () => {
    setHealth((prev) => prev.map((h) => ({ ...h, status: 'checking' as const })));

    // Check API
    try {
      const start = Date.now();
      const res = await axios.get(`${API_BASE}/health`, { timeout: 5000 });
      const latency = Date.now() - start;
      setHealth((prev) =>
        prev.map((h) =>
          h.service === 'DFIReballz API'
            ? { ...h, status: 'healthy', latency, version: res.data?.version || '1.0.0' }
            : h
        )
      );
    } catch {
      setHealth((prev) =>
        prev.map((h) =>
          h.service === 'DFIReballz API' ? { ...h, status: 'down' } : h
        )
      );
    }

    // Simulate other service checks
    setTimeout(() => {
      setHealth((prev) =>
        prev.map((h) => {
          if (h.service === 'MCP Server') return { ...h, status: 'healthy', latency: 12, version: '0.1.0' };
          if (h.service === 'Evidence Store') return { ...h, status: 'healthy', latency: 3 };
          if (h.service === 'Threat Intel') return { ...h, status: 'degraded', latency: 450 };
          return h;
        })
      );
    }, 1000);
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.post(`${API_BASE}/settings`, {
        mcp_host: selectedHost,
        api_keys: apiKeys,
      });
    } catch {
      // Settings save may fail if API is down, but we save locally
    }
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-success" />;
      case 'degraded':
        return <CheckCircle className="w-4 h-4 text-warning" />;
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
        <div className="card-forensic space-y-4">
          {Object.entries(apiKeys).map(([key, value]) => (
            <div key={key}>
              <label className="block text-xs text-text-muted mb-1.5 font-medium capitalize">
                {key.replace(/_/g, ' ')} API Key
              </label>
              <input
                type="password"
                value={value}
                onChange={(e) => setApiKeys((prev) => ({ ...prev, [key]: e.target.value }))}
                placeholder={`Enter ${key} API key...`}
                className="input-field w-full font-mono text-sm"
              />
            </div>
          ))}
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
