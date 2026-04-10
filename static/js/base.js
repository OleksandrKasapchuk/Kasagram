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
        const lastSeen = document.getElementById(`last-seen-${data.username}`)
        
        if (data.is_online) {
            if (statusDot) {
                statusDot.classList.add('online');
                statusDot.classList.remove('offline');
            }
            if (lastSeen) {
                lastSeen.innerText = ''
            }
        } else {
            if (statusDot) {
                statusDot.classList.add('offline');
                statusDot.classList.remove('online');
            }
            if (lastSeen) {
                lastSeen.innerText = 'last seen ' + data.last_seen
            }
        }
    }
    

    else if (data.type === 'new_notification') {

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
                    markAsRead();
                }, 2000);
            }
        }
    } else if (data.action === "new_message") {
    // 1. Оновлюємо бейдж (лічильник)
    const badge = document.getElementById(`unread-count-${data.chat_id}`);
    if (badge) {
        // Якщо сервер прислав готове число — ставимо його, інакше +1
        const currentCount = parseInt(badge.innerText) || 0;
        badge.innerText = data.unread_count !== undefined ? data.unread_count : (currentCount + 1);
        badge.style.display = 'inline-block';
    }

    // 2. Шукаємо картку чату
    const chatCard = document.querySelector(`[data-chat-id="${data.chat_id}"]`);
    const container = document.querySelector('.chat-list-container');

    if (chatCard && container) {
        // Оновлюємо текст повідомлення (прев'ю)
        const preview = chatCard.querySelector('.last-msg-preview');
        if (preview) {
            preview.innerText = data.message;
            preview.classList.remove('text-muted', 'italic'); // Прибираємо стиль "No messages yet"
        } else {
            console.log("no preview found")
        }

        // Оновлюємо час
        const timeDisplay = chatCard.querySelector('.last-msg-time');
        if (timeDisplay) {
            timeDisplay.innerText = "Just now";
        }

        // Переміщуємо вгору списку (після заголовка h2)
        const header = container.querySelector('h2');
        if (header) {
            header.after(chatCard); 
        } else {
            container.prepend(chatCard);
        }
        
        // Можна додати ефект "підсвічування"
        chatCard.classList.add('chat-item-new-anim');
        setTimeout(() => chatCard.classList.remove('chat-item-new-anim'), 2000);
    }
}
};

function injectNewNotification(container, data) {
    // Створюємо головний контейнер картки
    const newNotif = document.createElement('div');
    newNotif.className = 'notif-card unread position-relative'; // Додаємо 'unread' за замовчуванням

    // Формуємо внутрішній HTML, копіюючи структуру з шаблону
    newNotif.innerHTML = `
        <div class="d-flex align-items-center p-3">
            <a href="${data.actor_url}" class="notif-avatar-link me-3">
                <img src="${data.actor_avatar || '/static/images/default_avatar.jpg'}" 
                     class="notif-avatar" alt="avatar">
            </a>

            <div class="flex-grow-1">
                <p class="mb-0">
                    <a href="${data.actor_url}" class="fw-bold notif-username">${data.actor_name}</a> 
                    <span class="gray-text ms-1">${data.message}</span>
                </p>
                <small class="gray-text">Just now</small>
                
                <a href="${data.target_url}" class="stretched-link"></a>
            </div>

            <div class="notif-dot"></div>
        </div>
    `;

    // Додаємо в початок списку (prepend)
    container.prepend(newNotif);

    // Видаляємо напис "No notifications yet", якщо він є
    const emptyMsg = container.querySelector('.text-center.py-5');
    if (emptyMsg) emptyMsg.remove();
}