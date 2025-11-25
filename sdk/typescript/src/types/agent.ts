import type { ReasonerDefinition } from './reasoner.js';
import type { SkillDefinition } from './skill.js';
import type { MemoryChangeEvent, MemoryWatchHandler } from '../memory/MemoryInterface.js';

export interface AgentConfig {
  nodeId: string;
  version?: string;
  teamId?: string;
  agentFieldUrl?: string;
  port?: number;
  publicUrl?: string;
  aiConfig?: AIConfig;
  memoryConfig?: MemoryConfig;
  didEnabled?: boolean;
  devMode?: boolean;
  heartbeatIntervalMs?: number;
}

export interface AIConfig {
  provider?: 'openai' | 'anthropic' | 'openrouter' | 'ollama';
  model?: string;
  apiKey?: string;
  baseUrl?: string;
  temperature?: number;
  maxTokens?: number;
}

export interface MemoryConfig {
  defaultScope?: MemoryScope;
  ttl?: number;
}

export type MemoryScope = 'workflow' | 'session' | 'agent' | 'global';

export interface AgentCapability {
  agentId: string;
  baseUrl: string;
  version: string;
  healthStatus: string;
  reasoners: ReasonerCapability[];
}

export interface ReasonerCapability {
  id: string;
  description?: string;
  tags: string[];
  inputSchema?: any;
  outputSchema?: any;
  invocationTarget: string;
}

export interface DiscoveryResponse {
  discoveredAt: Date;
  totalAgents: number;
  totalReasoners: number;
  capabilities: AgentCapability[];
}

export interface AgentState {
  reasoners: Map<string, ReasonerDefinition>;
  skills: Map<string, SkillDefinition>;
  memoryWatchers: Array<{ pattern: string; handler: MemoryWatchHandler }>;
}

export interface HealthStatus {
  status: 'ok';
  nodeId: string;
  version?: string;
}

export type Awaitable<T> = T | Promise<T>;
