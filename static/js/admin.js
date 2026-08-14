// Admin Helper JavaScript for Campus to Career

document.addEventListener('DOMContentLoaded', function () {
  const titleInput = document.getElementById('title');
  const slugPreview = document.getElementById('slug-preview');
  
  if (titleInput && slugPreview) {
    titleInput.addEventListener('input', function () {
      const title = this.value;
      const slug = title.toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .trim()
        .replace(/[-\s]+/g, '-');
      slugPreview.textContent = slug || 'auto-generated-slug';
    });
  }

  // Pre-publish checklist logic
  const checkCompany = document.getElementById('company_id');
  const checkTitle = document.getElementById('title');
  const checkLocation = document.getElementById('location');
  const checkEligibility = document.getElementById('eligibility');
  const checkAppUrl = document.getElementById('application_url');
  const checkDescription = document.getElementById('description');

  function updateChecklist() {
    setItemState('chk-company', checkCompany && checkCompany.value > 0);
    setItemState('chk-title', checkTitle && checkTitle.value.trim().length > 3);
    setItemState('chk-location', checkLocation && checkLocation.value.trim().length > 0);
    setItemState('chk-eligibility', checkEligibility && checkEligibility.value.trim().length > 5);
    setItemState('chk-appurl', checkAppUrl && checkAppUrl.value.trim().length > 8);
    setItemState('chk-description', checkDescription && checkDescription.value.trim().length > 20);
  }

  function setItemState(id, isValid) {
    const el = document.getElementById(id);
    if (!el) return;
    if (isValid) {
      el.classList.remove('text-muted', 'text-danger');
      el.classList.add('text-success');
      el.querySelector('.check-icon').className = 'bi bi-check-circle-fill check-icon me-2';
    } else {
      el.classList.remove('text-success');
      el.classList.add('text-muted');
      el.querySelector('.check-icon').className = 'bi bi-dash-circle check-icon me-2';
    }
  }

  const inputs = [checkCompany, checkTitle, checkLocation, checkEligibility, checkAppUrl, checkDescription];
  inputs.forEach(input => {
    if (input) {
      input.addEventListener('input', updateChecklist);
      input.addEventListener('change', updateChecklist);
    }
  });

  updateChecklist();
});
