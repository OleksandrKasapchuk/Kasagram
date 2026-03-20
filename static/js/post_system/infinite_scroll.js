let page = 1;
let emptyPage = false;
let blockRequest = false;

window.onscroll = function() {
    let margin = document.body.clientHeight - window.innerHeight - 200;
    if (window.pageYOffset > margin && !emptyPage && !blockRequest) {
        blockRequest = true;
        page += 1;
        
        // Додаємо параметр категорії, якщо він є в URL
        const urlParams = new URLSearchParams(window.location.search);
        const category = urlParams.get('category') || 'for_you';

        fetch(`?category=${category}&page=${page}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.text())
        .then(html => {
            if (html.trim() === "") {
                emptyPage = true;
            } else {
                const container = document.getElementById('post-container');
                container.insertAdjacentHTML('beforeend', html);
                blockRequest = false;
            }
        });
    }
};