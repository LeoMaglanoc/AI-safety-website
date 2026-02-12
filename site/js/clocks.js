/**
 * Pure elapsed-time logic and DOM rendering for AI Safety Clocks.
 */

function computeElapsed(incidentDate, now) {
  const diffMs = now.getTime() - incidentDate.getTime();
  if (diffMs <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0 };
  }
  const totalSeconds = Math.floor(diffMs / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return { days, hours, minutes, seconds };
}

function formatElapsed(elapsed) {
  const h = String(elapsed.hours).padStart(2, '0');
  const m = String(elapsed.minutes).padStart(2, '0');
  const s = String(elapsed.seconds).padStart(2, '0');
  return `${elapsed.days}d ${h}h ${m}m ${s}s`;
}

function getColorClass(days) {
  if (days >= 30) return 'status-green';
  if (days >= 7) return 'status-yellow';
  return 'status-red';
}

function renderClock(clockData, containerEl) {
  if (!clockData || !clockData.last_incident) {
    containerEl.innerHTML = '<div class="clock-card"><p>No incident data available.</p></div>';
    return null;
  }

  const incidentDate = new Date(clockData.last_incident.date);
  const elapsed = computeElapsed(incidentDate, new Date());
  const colorClass = getColorClass(elapsed.days);

  containerEl.innerHTML = `
    <div class="clock-card ${colorClass}">
      <h2>${clockData.clock_name}</h2>
      <p class="clock-description">${clockData.description}</p>
      <div class="clock-counter" data-incident-date="${clockData.last_incident.date}">
        ${formatElapsed(elapsed)}
      </div>
      <div class="clock-details">
        <p class="incident-title">${clockData.last_incident.title}</p>
        <p class="incident-date">Last incident: ${incidentDate.toLocaleDateString()}</p>
        <p class="data-source">Source: ${clockData.data_source.name}</p>
      </div>
    </div>
  `;

  return containerEl.querySelector('.clock-counter');
}

function tickClock(counterEl) {
  const dateStr = counterEl.getAttribute('data-incident-date');
  const incidentDate = new Date(dateStr);
  const elapsed = computeElapsed(incidentDate, new Date());
  counterEl.textContent = formatElapsed(elapsed);

  const card = counterEl.closest('.clock-card');
  if (card) {
    card.classList.remove('status-green', 'status-yellow', 'status-red');
    card.classList.add(getColorClass(elapsed.days));
  }
}

function startClocks(counterElements) {
  return setInterval(() => {
    counterElements.forEach(tickClock);
  }, 1000);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { computeElapsed, formatElapsed, getColorClass, renderClock, tickClock, startClocks };
}
