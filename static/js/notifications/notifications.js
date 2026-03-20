function markAsRead() {
    const url = window.DjangoConfig.markNotifReadUrl;
    const csrf = window.DjangoConfig.csrfToken;

    if (!url) return; // Захист, якщо URL не передали

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf,
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Сповіщення успішно прочитані.');
        }
    })
    .catch(error => console.error('Помилка:', error));
}

markAsRead();