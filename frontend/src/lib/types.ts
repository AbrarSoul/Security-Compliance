export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface UserMe extends User {
  roles: string[];
  permissions: string[];
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface FileMetadata {
  row_count: number | null;
  column_count: number | null;
  schema?: unknown;
  preview?: unknown;
  extra?: Record<string, unknown>;
  analyzed_at: string;
}

export interface UploadedFile {
  id: string;
  original_name: string;
  file_type: string;
  content_type: string | null;
  size_bytes: number;
  checksum_sha256: string | null;
  status: string;
  created_at: string;
  metadata: FileMetadata | null;
}

export interface ScanFinding {
  id: string;
  finding_type: string;
  severity: string;
  column_name: string | null;
  sample_count: number;
  match_rate: number | null;
  evidence: Record<string, unknown> | null;
  created_at: string;
}

export interface Recommendation {
  id: string;
  priority: string;
  title: string;
  description: string;
  action_type: string;
  finding_type: string | null;
  column_name: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface FindingContribution {
  finding_type: string;
  severity: string;
  column_name: string | null;
  base_points: number;
  density_points: number;
  type_weight_points: number;
  total_points: number;
  match_rate: number;
}

export interface ComplianceScore {
  risk_score: number;
  compliance_status: string;
  classification: string;
  highest_severity: string | null;
  total_findings: number;
  contributions?: FindingContribution[];
  adjustments?: Record<string, unknown>[];
  thresholds_applied?: Record<string, number>;
}

export interface Scan {
  id: string;
  file_id: string;
  status: string;
  risk_score: number | null;
  compliance_status: string | null;
  classification: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
  findings_count?: number;
  findings?: ScanFinding[];
  recommendations?: Recommendation[];
  compliance_score?: ComplianceScore | null;
}

export interface Report {
  id: string;
  scan_id: string;
  created_at: string;
  executive_summary?: {
    risk_score?: number;
    compliance_status?: string;
    classification?: string;
    total_findings?: number;
    highest_severity?: string;
  };
  summary?: Record<string, unknown>;
  has_json_export?: boolean;
  has_pdf_export?: boolean;
}
