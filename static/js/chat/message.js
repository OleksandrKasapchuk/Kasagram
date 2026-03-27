const chatId = window.ChatConfig.chatId;
const currentUser = window.ChatConfig.currentUser;
const chatMessages = document.getElementById("chat-messages");
let typingTimeout;
let isCurrentlyTyping = false;
const messageInput = document.getElementById('message-content');
let isFetching = false; // Прапорець, щоб не слати 100 запитів одночасно

// 1. Створюємо підключення
const chatSocket = new WebSocket(
    (window.location.protocol === 'https:' ? 'wss://' : 'ws://') 
    + window.location.host 
    + '/ws/chat/' + chatId + '/'
);

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

let currentReplyId = null;

function prepareMessageReply(messageId, username, content) {
    currentReplyId = messageId;
    document.getElementById('reply-parent-id').value = messageId;
    document.getElementById('reply-to-username').innerText = `@${username}`;
    document.getElementById('reply-to-content').innerText = content;
    
    const preview = document.getElementById('reply-preview');
    preview.classList.remove('d-none');
    document.getElementById('message-content').focus();
}

function cancelMessageReply() {
    currentReplyId = null;
    document.getElementById('reply-parent-id').value = "";
    document.getElementById('reply-preview').classList.add('d-none');
}

// Онови функцію SendMessage (додай parent_id в JSON)
function SendMessage() {
    const input = document.getElementById('message-content');
    const content = input.value.trim();
    const parentId = document.getElementById('reply-parent-id').value;

    if (content !== "") {
        chatSocket.send(JSON.stringify({
            'message': content,
            'username': window.ChatConfig.currentUser,
            'parent_id': parentId ? parentId : null // ПЕРЕДАЄМО ID БАТЬКА
        }));
        
        input.value = '';
        cancelMessageReply(); // Скидаємо реплай після відправки
    }
}

// Додаткова фіча: скрол до оригінального повідомлення при кліку на реплай
function scrollToMessage(id) {
    const element = document.getElementById(`message-${id}`);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        element.classList.add('highlight-message');
        setTimeout(() => element.classList.remove('highlight-message'), 2000);
    }
}

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    const isMe = data.is_me !== undefined ? data.is_me : (data.username === currentUser);

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
    } else if (data.message) {
        const chatMessages = document.getElementById('chat-messages');
        
        if (!isMe) {
            chatSocket.send(JSON.stringify({ 'action': 'mark_as_read' }));
        }

        const msgTime = data.timestamp || new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        // ПЕРЕВІРКА: Чи є в повідомленні реплай?
        let replyHtml = '';
        console.log("parent: " + data.parent_content)
        if (data.parent_content) {
            replyHtml = `
                <div class="reply-in-message border-start ps-2 mb-1" 
                     style="border-left: 3px solid #007bff !important; background: rgba(0,0,0,0.05); cursor: pointer;"
                     onclick="scrollToMessage(${data.parent_id || ''})">
                    <small class="fw-bold d-block text-primary">${data.parent_username}</small>
                    <small class="text-truncate d-block text-muted">${data.parent_content}</small>
                </div>
            `;
        }

        const messageHtml = `
            <article class="d-flex mx-3 mb-2 ${isMe ? 'flex-row-reverse' : 'flex-row'}" id="message-${data.message_id}">
                <div class="message-wrapper position-relative ${isMe ? 'sent' : 'received'}"
                     oncontextmenu="prepareMessageReply(${data.message_id}, '${data.username}', '${data.parent_content.substring(0, 30)}'); return false;">
                    
                    <div class="message-content px-3 py-2">
                        ${replyHtml} <span class="message-text">${data.message}</span>
                        <span class="status-spacer"></span> 
                        
                        <div class="message-meta-container">
                            <time class="message-time">${msgTime}</time>
                            ${isMe ? `
                                <span class="material-symbols-outlined status-icon">check</span>
                            ` : ''}
                        </div>
                    </div>
                </div>
                
                <div class="message-actions d-flex align-items-center">
                    <span class="material-symbols-outlined pointer text-secondary small mx-1" 
                          onclick="prepareMessageReply(${data.message_id}, '${data.username}', '${data.message.substring(0, 30)}')">
                        reply
                    </span>
                    ${isMe ? `
                        <button onclick="deleteMessage(${data.message_id})" 
                                class="material-symbols-outlined pointer p-2 delete-btn align-self-center border-0 bg-transparent">
                            delete
                        </button>
                    ` : ''}
                </div>
            </article>
        `;

        chatMessages.insertAdjacentHTML('beforeend', messageHtml);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
};

// Обробка натискання Enter (без Shift)
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        SendMessage();
    }
});

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

chatMessages.addEventListener('scroll', async () => {
    if (chatMessages.scrollTop <= 50 && !isFetching) {
        isFetching = true;
        
        // Зберігаємо поточне перше повідомлення, щоб знати, чи довантажилось щось
        const currentFirstMsg = chatMessages.querySelector('article');
        
        await loadMoreMessages();
        
        isFetching = false;
    }
});

function scrollToBottom() {
    if (chatMessages) {
        // scrollHeight — це повна висота всього контенту всередині
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Викликаємо відразу після завантаження DOM
document.addEventListener('DOMContentLoaded', () => {
    // Невелика затримка (100мс) потрібна, щоб браузер встиг 
    // прорахувати висоту всіх елементів і картинок
    setTimeout(scrollToBottom, 100);
});

async function loadMoreMessages(){
    const firstMessage = document.querySelector("#chat-messages article:first-child");
    if (!firstMessage) return;

    const oldestId = firstMessage.id.replace("message-", "");
    const url = `/chat/messages/${chatId}/?oldest_id=${oldestId}`;

    try {
        const response = await fetch(url);
        const data = await response.json(); // Тут була помилка в слові response

        if (data.messages && data.messages.length > 0) {
            renderOlderMessages(data.messages);
        }
    } catch (error) {
        console.error("Error loading messages:", error);
    }
}

function renderOlderMessages(messages){
    const oldHeight = chatMessages.scrollHeight;

    let htmlContent = '';
    messages.forEach(msg => {
        const isMe = msg.is_user_message; // Беремо з твого JSON у в'юсі
        const msgHtml = `
            <article class="d-flex mx-3 mb-2 ${isMe ? 'flex-row-reverse' : 'flex-row'}" id="message-${msg.id}">
                <div class="message-wrapper position-relative ${isMe ? 'sent' : 'received'}">
                    <div class="message-content px-3 py-2">
                        <span class="message-text">${msg.content}</span>
                        <span class="status-spacer"></span> 
                        <div class="message-meta-container">
                            <time class="message-time">${msg.timestamp || ''}</time>
                            ${isMe ? '<span class="material-symbols-outlined status-icon">check</span>' : ''}
                        </div>
                    </div>
                </div>
                ${isMe ? `
                    <button onclick="deleteMessage(${msg.id})" 
                            class="material-symbols-outlined pointer p-2 delete-btn align-self-center border-0 bg-transparent">
                        delete
                    </button>` : ''}
            </article>
        `;
        htmlContent += msgHtml;
    });

    // 3. Вставляємо все одним махом у початок контейнера
    chatMessages.insertAdjacentHTML('afterbegin', htmlContent);

    // 4. Коригуємо скрол: нова висота мінус стара висота
    // Це дозволить юзеру залишитися на тому ж місці, де він був
    const newHeight = chatMessages.scrollHeight;
    chatMessages.scrollTop = newHeight - oldHeight;
}