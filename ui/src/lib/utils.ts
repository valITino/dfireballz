import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const API_BASE = 'http://localhost:8800';

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function generateCaseNumber(): string {
  const now = new Date();
  const year = now.getFullYear();
  const seq = Math.floor(Math.random() * 9000) + 1000;
  return `DFIR-${year}-${seq}`;
}

export function truncateHash(hash: string, len = 12): string {
  if (hash.length <= len) return hash;
  return `${hash.slice(0, len)}...`;
}

export type CaseSeverity = 'critical' | 'high' | 'medium' | 'low';
export type CaseStatus = 'open' | 'in_progress' | 'closed' | 'archived';

export interface Case {
  id: string;
  case_number: string;
  title: string;
  description: string;
  case_type: string;
  classification: string;
  severity: CaseSeverity;
  status: CaseStatus;
  investigator: string;
  created_at: string;
  updated_at: string;
  ioc_count?: number;
  finding_count?: number;
  evidence_count?: number;
}

export interface IoC {
  id: string;
  case_id: string;
  type: string;
  value: string;
  source: string;
  severity: CaseSeverity;
  tags: string[];
  enrichment?: Record<string, unknown>;
  first_seen: string;
  last_seen: string;
}

export interface Finding {
  id: string;
  case_id: string;
  title: string;
  description: string;
  severity: CaseSeverity;
  category: string;
  evidence_refs: string[];
  created_at: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  source: string;
  event_type: string;
  description: string;
  severity?: CaseSeverity;
  artifact_ref?: string;
}

export interface Evidence {
  id: string;
  case_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  sha256: string;
  md5: string;
  sha1: string;
  uploaded_at: string;
  analysis_status: string;
}

export interface Playbook {
  id: string;
  name: string;
  description: string;
  category: string;
  tools: string[];
  estimated_duration: string;
  severity_target: CaseSeverity[];
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
