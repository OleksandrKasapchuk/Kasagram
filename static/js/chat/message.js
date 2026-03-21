
function deleteMessage(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }
    chatSocket.send(JSON.stringify({
        'action': 'delete',
        'message_id': messageId
    }));
}



const chatId = window.ChatConfig.chatId;
const currentUser = window.ChatConfig.currentUser;

// 1. Створюємо підключення
const chatSocket = new WebSocket(
    (window.location.protocol === 'https:' ? 'wss://' : 'ws://') 
    + window.location.host 
    + '/ws/chat/' + chatId + '/'
);

// 2. Отримання повідомлення
chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'delete_message') {
        const messageDiv = document.getElementById(`message-${data.message_id}`);
        if (messageDiv) messageDiv.remove();
        return;
    }
    const chatMessages = document.getElementById('chat-messages');
    
    const isMe = data.username === currentUser;
    
    const messageHtml = `
        <article class="d-flex mx-3 ${isMe ? 'flex-row-reverse' : ''}" id="message-temp">
            <p class="message mb-1 px-3 py-2 d-flex flex-wrap ${isMe ? 'bg-info' : ''}">
                ${data.message}
            </p>
            ${isMe ? `<span class="material-symbols-outlined pointer p-2 delete-btn">delete</span>` : ''}
        </article>
    `;
    
    chatMessages.insertAdjacentHTML('beforeend', messageHtml);
    
    // Автоматичний скрол вниз
    chatMessages.scrollTop = chatMessages.scrollHeight;
};

// 3. Відправка повідомлення
function SendMessage() {
    const messageInput = document.getElementById('message-content');
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