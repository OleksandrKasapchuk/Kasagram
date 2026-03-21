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
};