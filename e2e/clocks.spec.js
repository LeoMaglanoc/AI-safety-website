const { test, expect } = require('@playwright/test');

test.describe('AI Safety Clocks', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('page loads with correct title', async ({ page }) => {
    await expect(page).toHaveTitle('AI Safety Clocks');
  });

  test('displays two clock cards', async ({ page }) => {
    const cards = page.locator('.clock-card');
    await expect(cards).toHaveCount(2);
  });

  test('clock 1 shows Physical AI Safety Clock', async ({ page }) => {
    const clock1 = page.locator('#clock1');
    await expect(clock1.locator('h2')).toHaveText('Physical AI Safety Clock');
  });

  test('clock 2 shows Digital AI Safety Clock', async ({ page }) => {
    const clock2 = page.locator('#clock2');
    await expect(clock2.locator('h2')).toHaveText('Digital AI Safety Clock');
  });

  test('clock counters display elapsed time format', async ({ page }) => {
    const counters = page.locator('.clock-counter');
    await expect(counters.first()).toHaveText(/\d+d \d{2}h \d{2}m \d{2}s/);
    await expect(counters.last()).toHaveText(/\d+d \d{2}h \d{2}m \d{2}s/);
  });

  test('clocks tick after 1 second', async ({ page }) => {
    const counter = page.locator('.clock-counter').first();
    const initial = await counter.textContent();

    // Wait just over 1 second for the tick
    await page.waitForTimeout(1500);

    const updated = await counter.textContent();
    expect(updated).not.toBe(initial);
  });

  test('clock cards have color status classes', async ({ page }) => {
    const cards = page.locator('.clock-card');
    const firstCard = cards.first();

    // Should have one of the status classes
    const classList = await firstCard.getAttribute('class');
    const hasStatus = classList.includes('status-green') ||
                      classList.includes('status-yellow') ||
                      classList.includes('status-red');
    expect(hasStatus).toBe(true);
  });

  test('incident details are shown', async ({ page }) => {
    const details = page.locator('.incident-title').first();
    await expect(details).not.toBeEmpty();
  });

  test('data source is shown', async ({ page }) => {
    const source = page.locator('.data-source').first();
    await expect(source).toContainText('Source:');
  });

  test('footer contains data source links', async ({ page }) => {
    const footer = page.locator('footer');
    await expect(footer.locator('a')).toHaveCount(2);
  });

  test('footnote about date approximation is visible', async ({ page }) => {
    const footnote = page.locator('.footnote');
    await expect(footnote).toContainText('15th');
  });
});
