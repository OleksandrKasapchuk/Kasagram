function deleteMessage(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }
    chatSocket.send(JSON.stringify({
        'action': 'delete',
        'message_id': messageId
    }));
}


function SendMessage() {
    const input = document.getElementById('message-content');
    const content = input.value.trim();
    const parentId = document.getElementById('reply-parent-id').value;
    const chatMessages = document.getElementById('chat-messages');

    // Отримуємо дані для реплаю з візуального блоку (той, що над полем вводу)
    const replyUserName = document.getElementById('reply-to-username')?.innerText;
    const replyText = document.getElementById('reply-to-content')?.innerText;

    if (content !== "") {
        const tempId = 'temp-' + Date.now();
        const msgTime = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        // ПІДГОТОВКА HTML ДЛЯ РЕПЛАЮ (Оптимістична)
        let optimisticReplyHtml = '';
        if (parentId && replyText) {
            optimisticReplyHtml = `
                <div class="reply-in-message border-start ps-2 mb-1" 
                     style="border-left: 3px solid #007bff !important; background: rgba(0,0,0,0.05);">
                    <small class="fw-bold d-block">${replyUserName}</small>
                    <small class="text-truncate d-block">${replyText}</small>
                </div>
            `;
        }

        const tempHtml = `
            <article class="d-flex mx-3 mb-2 flex-row-reverse optimistic" id="${tempId}">
                <div class="message-wrapper position-relative sent" style="opacity: 0.6;">
                    <div class="message-content px-3 py-2">
                        ${optimisticReplyHtml} 
                        <span class="message-text">${content}</span>
                        <span class="status-spacer"></span> 
                        <div class="message-meta-container">
                            <time class="message-time">${msgTime}</time>
                            <span class="material-symbols-outlined status-icon">schedule</span>
                        </div>
                    </div>
                </div>
                <div class="d-flex align-items-center" style="opacity: 0.5; pointer-events: none;">
                    <span class="material-symbols-outlined pointer text-secondary small mx-1">reply</span>
                    <span class="delete-btn pointer material-symbols-outlined">delete</span>
                </div>
            </article>
        `;
        chatMessages.insertAdjacentHTML('afterbegin', tempHtml);
        
        // 2. Відправляємо на сервер
        chatSocket.send(JSON.stringify({
            'action': 'chat_message',
            'message': content,
            'username': window.ChatConfig.currentUser,
            'parent_id': parentId ? parentId : null,
            'temp_id': tempId // Додаємо temp_id, щоб бекенд повернув його нам
        }));

        input.value = '';
        cancelMessageReply();
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Обробка натискання Enter (без Shift)
const messageInput = document.getElementById('message-content');
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        SendMessage();
    }
});