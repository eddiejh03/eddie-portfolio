  (() => {
    // 9A. Update the footer year.
    document.getElementById('year').textContent =
      new Date().getFullYear();


    // 9B. Filter certificates by organisation.
    const filters = [
      ...document.querySelectorAll('.cert-filters [data-filter]')
    ];

    const cards = [
      ...document.querySelectorAll('.cert-grid .cert-card')
    ];

    const filterCount =
      document.getElementById('filter-count');

    function applyFilter(selectedButton) {
      const selectedIssuer = selectedButton.dataset.filter;

      filters.forEach(button => {
        button.setAttribute(
          'aria-pressed',
          String(button === selectedButton)
        );
      });

      let visibleCount = 0;

      cards.forEach(card => {
        const visible =
          selectedIssuer === 'ALL' ||
          card.dataset.issuer === selectedIssuer;

        card.hidden = !visible;

        if (visible) {
          visibleCount++;
        }
      });

      filterCount.textContent =
        `${visibleCount} qualification${visibleCount === 1 ? '' : 's'}`;
    }

    filters.forEach(button => {
      button.addEventListener('click', () => {
        applyFilter(button);
      });
    });

    applyFilter(filters[0]);


    // 9C. Open certificate previews.
    const modal =
      document.getElementById('certificate-modal');

    const frame =
      document.getElementById('certificate-frame');

    const image =
      document.getElementById('certificate-image');

    const openLink =
      document.getElementById('certificate-open');

    const closeButton =
      document.getElementById('certificate-close');

    let trigger;

    document.querySelectorAll('.cert-view').forEach(button => {
      button.addEventListener('click', () => {
        trigger = button;

        const url = button.dataset.pdf;
        const title = button.dataset.title;

        const isImage =
          /\.(jpe?g|png|webp)(?:[?#]|$)/i.test(url);

        document.getElementById('certificate-title').textContent =
          title;

        openLink.href = url;

        image.hidden = !isImage;
        frame.hidden = isImage;

        if (isImage) {
          image.src = url;
          image.alt = title;
        } else {
          frame.src = url;
          frame.title = title;
        }

        modal.showModal();
        document.body.classList.add('viewer-open');
      });
    });


    // 9D. Close the viewer and restore keyboard focus.
    closeButton.addEventListener('click', () => {
      modal.close();
    });

    modal.addEventListener('click', event => {
      if (event.target !== modal) {
        return;
      }

      const bounds = modal.getBoundingClientRect();

      const clickedOutside =
        event.clientX < bounds.left ||
        event.clientX > bounds.right ||
        event.clientY < bounds.top ||
        event.clientY > bounds.bottom;

      if (clickedOutside) {
        modal.close();
      }
    });

    modal.addEventListener('close', () => {
      frame.removeAttribute('src');
      image.removeAttribute('src');

      openLink.href = '#';

      document.body.classList.remove('viewer-open');

      if (trigger) {
        trigger.focus();
      }
    });
  })();