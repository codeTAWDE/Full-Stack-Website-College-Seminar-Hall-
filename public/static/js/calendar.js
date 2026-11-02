/**
 * Agnel Polytechnic SHMS - Calendar Integration Engine
 */
document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('shmsCalendar');
  const hallFilter = document.getElementById('hallFilterSelect');
  const modalEl = document.getElementById('eventDetailsModal');

  if (!calendarEl) return;

  function getInitialView() {
    return window.innerWidth < 768 ? 'listMonth' : 'dayGridMonth';
  }

  // Initialize FullCalendar instance
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: getInitialView(),
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,listMonth'
    },
    buttonText: {
      today: 'Today',
      month: 'Month',
      week: 'Week',
      list: 'Agenda'
    },
    themeSystem: 'standard',
    events: function (info, successCallback, failureCallback) {
      let url = `/api/calendar/events?start=${info.startStr}&end=${info.endStr}`;
      if (hallFilter && hallFilter.value) {
        url += `&hall_id=${hallFilter.value}`;
      }

      fetch(url)
        .then(response => {
          if (!response.ok) throw new Error('Network error');
          return response.json();
        })
        .then(data => successCallback(data))
        .catch(err => {
          console.error('Failed to load events:', err);
          failureCallback(err);
        });
    },
    eventClick: function (info) {
      const props = info.event.extendedProps;
      const titleEl = document.getElementById('modalEventTitle');
      const bodyEl = document.getElementById('modalEventBody');

      if (titleEl && bodyEl && modalEl) {
        titleEl.textContent = info.event.title;
        bodyEl.innerHTML = `
          <p><strong>Hall:</strong> ${props.hallName || 'N/A'} (${props.hallLocation || ''})</p>
          <p><strong>Time:</strong> ${info.event.start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - ${info.event.end ? info.event.end.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'N/A'}</p>
          <p><strong>Organizer:</strong> ${props.organizer || 'Academic Faculty'}</p>
          <p><strong>Department:</strong> ${props.department || 'Agnel Complex'}</p>
          <p><strong>Reference:</strong> <code>${props.reference || 'N/A'}</code></p>
          ${props.description ? `<p><strong>Description:</strong> ${props.description}</p>` : ''}
        `;
        modalEl.style.display = 'block';
      }
    },
    windowResize: function () {
      calendar.changeView(getInitialView());
    }
  });

  calendar.render();

  // Reload events when filtering by hall
  if (hallFilter) {
    hallFilter.addEventListener('change', function () {
      calendar.refetchEvents();
    });
  }

  // Modal Dismiss handler
  const closeBtn = document.getElementById('modalCloseBtn');
  if (closeBtn && modalEl) {
    closeBtn.addEventListener('click', () => modalEl.style.display = 'none');
    window.addEventListener('click', (e) => {
      if (e.target === modalEl) modalEl.style.display = 'none';
    });
  }
});