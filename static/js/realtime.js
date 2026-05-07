/**
 * Firestore real-time listener for the security dashboard.
 * Uses onSnapshot to update the dashboard without page reloads.
 */

// This file is loaded by the dashboard template.
// Firebase is initialized in the template before this script runs.

function initRealtimeDashboard() {
    if (typeof firebase === 'undefined' || !firebase.apps.length) {
        console.warn('Firebase not initialized for realtime dashboard.');
        return;
    }

    const db = firebase.firestore();

    // Listen for changes in active entries (status = 'entered')
    db.collection('security_logs')
      .where('status', '==', 'entered')
      .onSnapshot((snapshot) => {
          const count = snapshot.size;
          
          // Update "currently inside" counter if it exists
          const insideCounters = document.querySelectorAll('[data-stat="currently-inside"]');
          insideCounters.forEach(el => {
              el.textContent = count;
              // Flash animation
              el.classList.add('scale-110');
              setTimeout(() => el.classList.remove('scale-110'), 300);
          });

          console.log(`[Realtime] ${count} guardias adentro.`);
      }, (error) => {
          console.error('Realtime listener error:', error);
      });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRealtimeDashboard);
} else {
    initRealtimeDashboard();
}
