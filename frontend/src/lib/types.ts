export interface IntentIR {
  app_name: string;
  app_type: string;
  description: string;
  assumptions: string[];
}

export interface StageTrace {
  stage: string;
  status: 'success' | 'failed' | 'repaired' | 'skipped';
  latency_ms: number;
  repair_attempts: number;
  notes: string[];
}

export interface FinalAppConfig {
  metadata: any;
  intent: IntentIR;
  architecture: any;
  database: any;
  api: any;
  ui: any;
  auth: any;
  business_logic: any;
  validation_report: any;
  repair_report: any;
  runtime_report: any;
  pipeline_trace: StageTrace[];
}

export interface GenerateResponse {
  success: boolean;
  trace_id: string;
  config_hash: string;
  final_config: FinalAppConfig;
  validation_report: any;
  repair_report: any;
  runtime_report: any;
  metrics: any;
}
