document.addEventListener('DOMContentLoaded', function () {
  const btn = document.getElementById('loadMoreBtn');
  const list = document.getElementById('blogCardList');
  if (!btn || !list) return;

  btn.addEventListener('click', function () {
    const page = btn.dataset.nextPage;
    btn.disabled = true;
    btn.textContent = 'Loading...';

    const url = new URL(window.location.href);
    url.searchParams.set('page', page);
    url.searchParams.set('ajax', '1');

    fetch(url.toString())
      .then(function (resp) { return resp.text(); })
      .then(function (html) {
        const temp = document.createElement('div');
        temp.innerHTML = html;

        const info = temp.querySelector('#pageInfo');
        const cards = temp.querySelectorAll('.blog-card');
        cards.forEach(function (card) { list.appendChild(card); });

        if (info && info.dataset.hasNext === 'true') {
          btn.dataset.nextPage = info.dataset.nextPage;
          btn.disabled = false;
          btn.textContent = 'Read More';
        } else {
          btn.remove();
        }
      })
      .catch(function () {
        btn.disabled = false;
        btn.textContent = 'Read More';
      });
  });
});
