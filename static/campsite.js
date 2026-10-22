/* ==========================================================
   PORTFOLIO OBJECT INTERACTIONS
   Dictionary → Education panel
   ========================================================== */

(() => {
  const book = document.getElementById('education-book');
  const dialog = document.getElementById('education-dialog');
  const closeButton = document.getElementById(
    'education-dialog-close'
  );

  // Only run when all required elements exist.
  if (!book || !dialog || !closeButton) return;


  /* 1. Open the Education panel */

  book.addEventListener('click', () => {
    if (dialog.open) return;

    dialog.showModal();
    document.body.classList.add('camp-dialog-open');
  });


  /* 2. Close using the × button */

  closeButton.addEventListener('click', () => {
    dialog.close();
  });


  /* 3. Close when clicking outside the panel */

  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;

    const bounds = dialog.getBoundingClientRect();

    const clickedOutside =
      event.clientX < bounds.left ||
      event.clientX > bounds.right ||
      event.clientY < bounds.top ||
      event.clientY > bounds.bottom;

    if (clickedOutside) {
      dialog.close();
    }
  });


  /* 4. Restore scrolling and focus after closing */

  dialog.addEventListener('close', () => {
    document.body.classList.remove('camp-dialog-open');
    book.focus();
  });
})();