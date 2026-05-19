export type SecurityThreat = {
  id: string;
  detection_run_id: string | null;
  user_id: string | null;
  threat_type: string;
  category: string;
  severity: string;
  threat_score: number;
  title: string;
  description: string;
  status: string;
  fingerprint: string;
  source_event_type: string | null;
  detected_at: string;
  resolved_at: string | null;
  metadata_json: Record<string, unknown> | null;
};

export type SecurityEventLog = {
  id: string;
  user_id: string | null;
  threat_id: string | null;
  event_type: string;
  threat_type: string | null;
  severity: string;
  message: string;
  payload_json: Record<string, unknown> | null;
  created_at: string;
};

export type ThreatDashboard = {
  open_threats: SecurityThreat[];
  open_total: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  security_posture: number;
  latest_run: {
    id: string;
    threats_found: number;
    completed_at: string | null;
  } | null;
};

export type UserBehaviorItem = {
  user_id: string;
  threat_count: number;
  avg_threat_score: number;
  risk_level: string;
};
