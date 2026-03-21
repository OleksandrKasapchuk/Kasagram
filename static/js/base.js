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
        if (badge && data.unread_count !== undefined) {
            badge.innerText = data.unread_count;
            badge.style.display = 'inline'; // Показуємо, якщо був прихований
        }
    }
};