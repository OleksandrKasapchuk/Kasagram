const globalSocket = new WebSocket(
    (window.location.protocol === 'https:' ? 'wss://' : 'ws://') 
    + window.location.host 
    + '/ws/global/'
);

globalSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'user_status_change') {
        // Шукаємо крапку статусу саме цього юзера за ID або username
        const statusDot = document.getElementById(`status-${data.username}`);
        if (statusDot) {
            if (data.is_online) {
                statusDot.classList.add('online');
                statusDot.classList.remove('offline');
            } else {
                statusDot.classList.add('offline');
                statusDot.classList.remove('online');
            }
        }
    }

    if (data.type === 'new_notification') {

        const badge = document.getElementById('new-notification-icon');
        if (badge) {
            badge.innerText = data.unread_count;
            badge.style.display = data.unread_count > 0 ? 'inline' : 'none';
        }

        const list = document.getElementById('notifications-list');
        if (list && data.actor_name) {
            injectNewNotification(list, data);

            if (window.location.pathname.includes('/notifications/')) {
                // Робимо невеличку затримку, щоб юзер встиг побачити, що щось прийшло
                setTimeout(() => {
                    markAsRead(); // Той самий твій POST запит
                }, 2000);
            }
        }
    }
}

function injectNewNotification(container, data) {
    const newBox = document.createElement('h4');
    
    newBox.innerHTML = `
        <a href="${data.actor_url}">
            <img src="${data.actor_avatar}" class="sidebar-avatar">
            ${data.actor_name}
        </a>
        <a href="${data.target_url}"> ${data.message}, View</a>
    `;
    container.prepend(newBox);
}