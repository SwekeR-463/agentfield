import { describe, it, expect } from 'vitest';
import { Agent } from '../src/agent/Agent.js';
import { AgentRouter } from '../src/router/AgentRouter.js';

describe('Agent', () => {
  it('registers reasoners and skills directly', () => {
    const agent = new Agent({ nodeId: 'test-agent', devMode: true });
    agent.reasoner('hello', async () => ({ ok: true }));
    agent.skill('format', () => ({ upper: 'X' }));

    expect(agent.reasoners.all().map((r) => r.name)).toContain('hello');
    expect(agent.skills.all().map((s) => s.name)).toContain('format');
  });

  it('includes routers with prefixes', () => {
    const router = new AgentRouter({ prefix: 'simulation' });
    router.reasoner('run', async () => ({}));
    router.skill('format', () => ({}));

    const agent = new Agent({ nodeId: 'test-agent', devMode: true });
    agent.includeRouter(router);

    expect(agent.reasoners.all().map((r) => r.name)).toContain('simulation/run');
    expect(agent.skills.all().map((s) => s.name)).toContain('simulation/format');
  });

  it('calls local reasoner via agent.call when target matches node id', async () => {
    const agent = new Agent({ nodeId: 'local', devMode: true });
    agent.reasoner('echo', async (ctx) => ({ echo: ctx.input.msg }));

    const result = await agent.call('local.echo', { msg: 'hi' });
    expect(result).toEqual({ echo: 'hi' });
  });
});
