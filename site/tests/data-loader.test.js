/**
 * @jest-environment jsdom
 */

const { fetchAllClocks, initialize } = require('../js/data-loader.js');

// Mock clocks module
jest.mock('../js/clocks.js', () => ({
  renderClock: jest.fn(() => {
    const el = global.document.createElement('div');
    return el;
  }),
  startClocks: jest.fn(),
}));

const { renderClock, startClocks } = require('../js/clocks.js');

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch = jest.fn();
});

describe('fetchAllClocks', () => {
  test('resolves with two entries', async () => {
    const clock1 = { clock_id: 'av_collisions', last_incident: { date: '2025-12-10T00:00:00Z' } };
    const clock2 = { clock_id: 'cyber_incidents', last_incident: { date: '2026-02-01T00:00:00Z' } };

    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(clock1) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(clock2) });

    const result = await fetchAllClocks();
    expect(result).toHaveLength(2);
    expect(result[0].clock_id).toBe('av_collisions');
    expect(result[1].clock_id).toBe('cyber_incidents');
  });

  test('rejects on HTTP error', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500 });

    await expect(fetchAllClocks()).rejects.toThrow();
  });
});

describe('initialize', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="clock1"></div>
      <div id="clock2"></div>
      <div id="error-message" style="display:none"></div>
    `;
  });

  test('calls renderClock and startClocks on success', async () => {
    const clock1 = { clock_id: 'av_collisions', last_incident: { date: '2025-12-10T00:00:00Z' } };
    const clock2 = { clock_id: 'cyber_incidents', last_incident: { date: '2026-02-01T00:00:00Z' } };

    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(clock1) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(clock2) });

    await initialize();

    expect(renderClock).toHaveBeenCalledTimes(2);
    expect(startClocks).toHaveBeenCalledTimes(1);
  });

  test('shows error message on failure', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    await initialize();

    const errorEl = document.getElementById('error-message');
    expect(errorEl.style.display).not.toBe('none');
  });
});
