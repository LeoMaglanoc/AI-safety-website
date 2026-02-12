/**
 * Fetch clock JSON data and initialize the live clocks.
 * In browser: clocks.js is loaded first, globals are available.
 * In Node/Jest: use require.
 */

/* eslint-disable no-undef */
var _clocks = (typeof require !== 'undefined') ? require('./clocks.js') : { renderClock: renderClock, startClocks: startClocks };

var CLOCK_URLS = [
  'data/clock1_av_collisions.json',
  'data/clock2_cyber_incidents.json',
];

async function fetchAllClocks() {
  var results = [];
  for (var i = 0; i < CLOCK_URLS.length; i++) {
    var resp = await fetch(CLOCK_URLS[i]);
    if (!resp.ok) {
      throw new Error('Failed to fetch ' + CLOCK_URLS[i] + ': ' + resp.status);
    }
    results.push(await resp.json());
  }
  return results;
}

async function initialize() {
  var containers = [
    document.getElementById('clock1'),
    document.getElementById('clock2'),
  ];
  var errorEl = document.getElementById('error-message');

  try {
    var clocks = await fetchAllClocks();
    var counterElements = [];

    clocks.forEach(function(clockData, i) {
      if (containers[i]) {
        var counterEl = _clocks.renderClock(clockData, containers[i]);
        if (counterEl) counterElements.push(counterEl);
      }
    });

    if (counterElements.length > 0) {
      _clocks.startClocks(counterElements);
    }
  } catch (err) {
    console.error('Failed to load clock data:', err);
    if (errorEl) {
      errorEl.style.display = 'block';
      errorEl.textContent = 'Failed to load clock data. Please try refreshing the page.';
    }
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { fetchAllClocks: fetchAllClocks, initialize: initialize };
}
