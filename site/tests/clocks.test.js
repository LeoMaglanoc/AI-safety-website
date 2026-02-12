/**
 * @jest-environment jsdom
 */

const { computeElapsed, formatElapsed } = require('../js/clocks.js');

describe('computeElapsed', () => {
  test('returns correct days/hours/minutes/seconds', () => {
    const incident = new Date('2025-12-10T00:00:00Z');
    // 5 days, 3 hours, 30 minutes, 15 seconds later
    const now = new Date('2025-12-15T03:30:15Z');
    const result = computeElapsed(incident, now);
    expect(result.days).toBe(5);
    expect(result.hours).toBe(3);
    expect(result.minutes).toBe(30);
    expect(result.seconds).toBe(15);
  });

  test('with zero elapsed', () => {
    const date = new Date('2025-12-10T00:00:00Z');
    const result = computeElapsed(date, date);
    expect(result.days).toBe(0);
    expect(result.hours).toBe(0);
    expect(result.minutes).toBe(0);
    expect(result.seconds).toBe(0);
  });

  test('with future date returns all zeros', () => {
    const incident = new Date('2026-01-01T00:00:00Z');
    const now = new Date('2025-12-10T00:00:00Z');
    const result = computeElapsed(incident, now);
    expect(result.days).toBe(0);
    expect(result.hours).toBe(0);
    expect(result.minutes).toBe(0);
    expect(result.seconds).toBe(0);
  });

  test('one-second difference', () => {
    const incident = new Date('2025-12-10T00:00:00Z');
    const now = new Date('2025-12-10T00:00:01Z');
    const result = computeElapsed(incident, now);
    expect(result.days).toBe(0);
    expect(result.hours).toBe(0);
    expect(result.minutes).toBe(0);
    expect(result.seconds).toBe(1);
  });
});

describe('formatElapsed', () => {
  test('pads single digits', () => {
    const result = formatElapsed({ days: 3, hours: 5, minutes: 9, seconds: 2 });
    expect(result).toBe('3d 05h 09m 02s');
  });

  test('handles large day counts', () => {
    const result = formatElapsed({ days: 365, hours: 12, minutes: 0, seconds: 0 });
    expect(result).toBe('365d 12h 00m 00s');
  });
});
