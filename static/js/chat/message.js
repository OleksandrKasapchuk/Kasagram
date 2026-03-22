const chatId = window.ChatConfig.chatId;
const currentUser = window.ChatConfig.currentUser;

// 1. Створюємо підключення
const chatSocket = new WebSocket(
    (window.location.protocol === 'https:' ? 'wss://' : 'ws://') 
    + window.location.host 
    + '/ws/chat/' + chatId + '/'
);
let typingTimeout;
let isCurrentlyTyping = false;
const messageInput = document.getElementById('message-content');

chatSocket.onopen = function(e) {
    console.log("Connected to chat! " + currentUser);
    chatSocket.send(JSON.stringify({
        'action': 'mark_as_read'
    }));
};

function deleteMessage(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }
    chatSocket.send(JSON.stringify({
        'action': 'delete',
        'message_id': messageId
    }));
}


messageInput.addEventListener('input', () => {
    if (!isCurrentlyTyping) {
        isCurrentlyTyping = true;
        chatSocket.send(JSON.stringify({
            'action': 'typing',
            'typing': true
        }));
    }

    // Очищаємо старий таймер
    clearTimeout(typingTimeout);

    // Якщо юзер замовк на 2 секунди — шлемо сигнал "перестав"
    typingTimeout = setTimeout(() => {
        chatSocket.send(JSON.stringify({
            'action': 'typing',
            'typing': false
        }));
        isCurrentlyTyping = false; 
    }, 2000);
});


chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    // Пріоритет на is_me від сервера, якщо немає - порівнюємо по старінці
    const isMe = data.is_me !== undefined ? data.is_me : (data.username === currentUser);

    if (data.type === 'user_typing') {
        const typingIndicator = document.getElementById('typing-indicator');
        if (data.typing && !isMe) {
            typingIndicator.innerText = `${data.username} is typing...`;
        } else {
            typingIndicator.innerText = '';
        }
        return;
    } 
    
    if (data.type === 'delete_message') {
        const messageDiv = document.getElementById(`message-${data.message_id}`);
        if (messageDiv) messageDiv.remove();
        return;
    } 
    
    if (data.type === 'messages_read') {
        // Синіють тільки ЯКЩО прочитав ІНШИЙ (не я)
        if (!isMe) {
            document.querySelectorAll('.message-status .material-symbols-outlined').forEach(el => {
                if (el.innerText.trim() === 'check') {
                    el.innerText = 'done_all';
                    el.style.color = '#3498db';
                }
            });
        }
        return;
    }

    // 2. Логіка відображення повідомлення (якщо прийшло нове повідомлення)
    if (data.message) {
        const chatMessages = document.getElementById('chat-messages');
        
        // Якщо повідомлення від іншого — шлемо сигнал "прочитано"
        if (!isMe) {
            chatSocket.send(JSON.stringify({ 'action': 'mark_as_read' }));
        }

        const messageHtml = `
            <article class="d-flex mx-3 mb-2 ${isMe ? 'flex-row-reverse' : 'flex-row'}" id="message-${data.message_id}">
                <div class="message-wrapper position-relative ${isMe ? 'sent' : 'received'}">
                    <div class="message-content px-3 py-2">
                        ${data.message}
                        <span class="status-spacer"></span> 
                    </div>
                    ${isMe ? `
                        <div class="message-status">
                            <span class="material-symbols-outlined">check</span>
                        </div>
                    ` : ''}
                </div>
                ${isMe ? `
                    <span onclick="deleteMessage(${data.message_id})" 
                          class="material-symbols-outlined pointer p-2 delete-btn align-self-center">
                        delete
                    </span>
                ` : ''}
            </article>
        `;

        chatMessages.insertAdjacentHTML('beforeend', messageHtml);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
};

function SendMessage() {
    const content = messageInput.value.trim();

    if (content !== "") {
        chatSocket.send(JSON.stringify({
            'message': content,
            'username': currentUser
        }));
        messageInput.value = '';
    }
}

// Обробка натискання Enter (без Shift)
document.getElementById('message-content').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        SendMessage();
    }
});

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};