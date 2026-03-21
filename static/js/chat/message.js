
function deleteMessage(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }
    chatSocket.send(JSON.stringify({
        'action': 'delete',
        'message_id': messageId
    }));
}

let typingTimeout;
let isCurrentlyTyping = false;
const messageInput = document.getElementById('message-content');

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
    
    if (data.type === 'user_typing') {
        const typingIndicator = document.getElementById('typing-indicator');
        if (data.typing && data.username !== currentUser) {
            typingIndicator.innerText = `${data.username} is typing...`;
        } else {
            typingIndicator.innerText = '';
        }
        return;
    } else if (data.type === 'delete_message') {
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