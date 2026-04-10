const chatMessages = document.getElementById("chat-messages");
let isFetching = false;

chatMessages.addEventListener('scroll', async () => {
    const scrollFromBottom = Math.abs(chatMessages.scrollTop) + chatMessages.clientHeight;
    
    if (scrollFromBottom >= chatMessages.scrollHeight - 100 && !isFetching) {
        isFetching = true;
        await loadMoreMessages();
        isFetching = false;
    }
});


async function loadMoreMessages(){
    const firstMessage = document.querySelector("#chat-messages article:last-child");
    if (!firstMessage) return;

    const oldestId = firstMessage.id.replace("message-", "");
    const url = `/api/messages/${chatId}/?oldest_id=${oldestId}`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (data.messages && data.messages.length > 0) {
            renderOlderMessages(data.messages);
        }
    } catch (error) {
        console.error("Error loading messages:", error);
    }
}


function renderOlderMessages(messages){
    let htmlContent = '';
    messages.forEach(msg => {
        const isMe = msg.is_me;
        const msgHtml = `
            <article class="d-flex mx-3 mb-2 ${isMe ? 'flex-row-reverse' : 'flex-row'}" id="message-${msg.id}">
                <div class="message-wrapper position-relative ${isMe ? 'sent' : 'received'}">
                    <div class="message-content px-3 py-2">
                        <span class="message-text">${msg.content}</span>
                        <span class="status-spacer"></span> 
                        <div class="message-meta-container">
                            <time class="message-time">${msg.formatted_time || ''}</time>
                            ${isMe ? `
                                <span class="material-symbols-outlined status-icon ${msg.is_read ? 'read' : ''}">
                                    ${msg.is_read ? 'done_all' : 'check'}
                                </span>
                            ` : ''}
                        </div>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    <span class="material-symbols-outlined pointer text-secondary small mx-1" 
                          onclick="prepareMessageReply(${msg.id}, '${msg.username}', '${msg.content.substring(0, 30)}')">
                        reply
                    </span>
                    ${isMe ? `
                        <span onclick="deleteMessage(${msg.id})" class="delete-btn pointer material-symbols-outlined">delete</span>
                    ` : ''}
                </div>
            </article>
        `;
        htmlContent += msgHtml;
    });

    chatMessages.insertAdjacentHTML('beforeend', htmlContent);
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