const currentUser = window.ChatConfig.currentUser;
const chatId = window.ChatConfig.chatId;
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
    } else if (data.type === 'messages_read') {
        if (!isMe) {
            document.querySelectorAll('.status-icon').forEach(el => {
            if (el.innerText.trim() === 'check') {
                el.innerText = 'done_all';
                el.classList.add('read');
            }
        });
        }
    } else if (data.type === 'chat_message') {
        const chatMessages = document.getElementById('chat-messages');
        
        // 1. ПЕРЕВІРКА: Чи це повідомлення вже існує як "оптимістичне"?
        if (data.temp_id) {
            const tempMsg = document.getElementById(data.temp_id);
            if (tempMsg) {
                // 1. Оновлюємо основні атрибути
                tempMsg.id = `message-${data.message_id}`;
                tempMsg.classList.remove('optimistic');
                
                // 2. Оновлюємо стилі (прибираємо прозорість)
                const wrapper = tempMsg.querySelector('.message-wrapper');
                wrapper.style.opacity = '1';
                const controls = tempMsg.querySelector('.d-flex.align-items-center');
                controls.style.opacity = '1';
                controls.style.pointerEvents = 'auto';

                // 3. Оновлюємо іконку статусу (з годинника на галочку)
                const statusIcon = tempMsg.querySelector('.status-icon');
                if (statusIcon) statusIcon.innerText = 'check';

                // 4. Оновлюємо обробники подій для кнопок (тепер ми знаємо реальний ID)
                const deleteBtn = tempMsg.querySelector('.delete-btn');
                if (deleteBtn) deleteBtn.setAttribute('onclick', `deleteMessage(${data.message_id})`);
                
                const replyBtn = tempMsg.querySelector('.material-symbols-outlined.pointer');
                if (replyBtn) {
                    replyBtn.setAttribute('onclick', `prepareMessageReply(${data.message_id}, '${data.username}', '${data.content.substring(0, 30)}')`);
                }

                // 5. Оновлюємо контекстне меню (oncontextmenu)
                wrapper.setAttribute('oncontextmenu', `prepareMessageReply(${data.message_id}, '${data.username}', '${(data.content || "").substring(0, 30)}'); return false;`);

                return; // Закінчуємо, повідомлення вже в чаті
            }
        }
        // 2. Якщо це повідомлення від іншого юзера (або не знайшли temp_id)
        if (!isMe) {
            chatSocket.send(JSON.stringify({ 'action': 'mark_as_read' }));
        }

        const msgTime = data.timestamp || new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        // Логіка реплаю (залишається твоя)
        let replyHtml = '';
        if (data.parent_content) {
            replyHtml = `
                <div class="reply-in-message border-start ps-2 mb-1" 
                     style="border-left: 3px solid #007bff !important; background: rgba(0,0,0,0.05); cursor: pointer;"
                     onclick="scrollToMessage(${data.parent_id || ''})">
                    <small class="fw-bold d-block">${data.parent_username}</small>
                    <small class="text-truncate d-block">${data.parent_content}</small>
                </div>
            `;
        }

        // Твій шаблон повідомлення
        const messageHtml = `
            <article class="d-flex mx-3 mb-2 ${isMe ? 'flex-row-reverse' : 'flex-row'}" id="message-${data.message_id}">
                <div class="message-wrapper position-relative ${isMe ? 'sent' : 'received'}"
                     oncontextmenu="prepareMessageReply(${data.message_id}, '${data.username}', '${(data.parent_content || "").substring(0, 30)}'); return false;">
                    <div class="message-content px-3 py-2">
                        ${replyHtml} <span class="message-text">${data.message}</span>
                        <span class="status-spacer"></span> 
                        <div class="message-meta-container">
                            <time class="message-time">${msgTime}</time>
                            ${isMe ? `<span class="material-symbols-outlined status-icon">check</span>` : ''}
                        </div>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    <span class="material-symbols-outlined pointer text-secondary small mx-1" 
                          onclick="prepareMessageReply(${data.message_id}, '${data.username}', '${data.message.substring(0, 30)}')">
                        reply
                    </span>
                    ${isMe ? `
                        <span onclick="deleteMessage(${data.message_id})" class="delete-btn pointer material-symbols-outlined">delete</span>
                    ` : ''}
                </div>
            </article>
        `;

        chatMessages.insertAdjacentHTML('afterbegin', messageHtml);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};