import {
  Clock,
  AlertTriangle,
  Shield,
  Network,
  User,
  FileText,
  Server,
  Filter,
} from 'lucide-react';
import { useState } from 'react';
import { type TimelineEvent, type CaseSeverity, formatDate, cn } from '../lib/utils';

const severityDot: Record<CaseSeverity, string> = {
  critical: 'bg-critical shadow-critical/50 shadow-sm',
  high: 'bg-warning shadow-warning/50 shadow-sm',
  medium: 'bg-accent shadow-accent/50 shadow-sm',
  low: 'bg-success',
};

const sourceIcons: Record<string, React.ElementType> = {
  EDR: Shield,
  SIEM: Server,
  Firewall: Network,
  AD: User,
  'File System': FileText,
  Analyst: User,
  DNS: Network,
};

interface TimelineProps {
  events: TimelineEvent[];
}

export default function Timeline({ events }: TimelineProps) {
  const [filter, setFilter] = useState<string>('all');

  const sources = ['all', ...new Set(events.map((e) => e.source))];
  const filtered = filter === 'all' ? events : events.filter((e) => e.source === filter);
  const sorted = [...filtered].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  if (events.length === 0) {
    return (
      <div className="card-forensic text-center py-12">
        <Clock className="w-10 h-10 text-text-muted mx-auto mb-3" />
        <p className="text-text-secondary">No timeline events available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="w-4 h-4 text-text-muted" />
        {sources.map((src) => (
          <button
            key={src}
            onClick={() => setFilter(src)}
            className={cn(
              'px-2.5 py-1 rounded-md text-xs font-medium transition-colors',
              filter === src
                ? 'bg-accent text-white'
                : 'bg-surface border border-surface-border text-text-secondary hover:border-accent/30'
            )}
          >
            {src === 'all' ? 'All Sources' : src}
          </button>
        ))}
        <span className="text-xs text-text-muted ml-auto">{sorted.length} events</span>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-[19px] top-0 bottom-0 w-px bg-surface-border" />

        <div className="space-y-1">
          {sorted.map((event, i) => {
            const Icon = sourceIcons[event.source] || AlertTriangle;
            const severity = event.severity || 'low';

            return (
              <div key={event.id || i} className="relative flex gap-4 group">
                {/* Dot on timeline */}
                <div className="relative z-10 flex items-center justify-center w-10 shrink-0">
                  <div
                    className={cn(
                      'w-3 h-3 rounded-full ring-4 ring-background',
                      severityDot[severity]
                    )}
                  />
                </div>

                {/* Content */}
                <div className="flex-1 card-forensic mb-2 group-hover:border-accent/20">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded bg-surface-hover flex items-center justify-center">
                        <Icon className="w-3.5 h-3.5 text-text-muted" />
                      </div>
                      <span className="text-xs font-medium text-accent">{event.source}</span>
                      <span className="text-xs text-text-muted bg-background px-1.5 py-0.5 rounded">
                        {event.event_type}
                      </span>
                    </div>
                    <span className="text-xs text-text-muted whitespace-nowrap flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDate(event.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-text-primary mt-2 leading-relaxed">
                    {event.description}
                  </p>
                  {event.artifact_ref && (
                    <div className="mt-2">
                      <span className="hash-display">{event.artifact_ref}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
