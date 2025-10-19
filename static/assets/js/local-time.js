document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.local-time').forEach(el => {
    const utc = el.getAttribute('data-utc');
    if (!utc) return;
    const date = new Date(utc);
    const options = {year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false};
    el.textContent = date.toLocaleString('zh-CN', options);
  });
});