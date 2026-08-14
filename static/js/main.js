// Main Client JavaScript for Campus to Career

document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss alert toasts after 5 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });
});

// Copy link utility function
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(function() {
    alert('Job link copied to clipboard!');
  }).catch(function(err) {
    console.error('Could not copy text: ', err);
  });
}
