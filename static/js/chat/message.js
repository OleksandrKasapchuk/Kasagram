const csrf = window.DjangoConfig.csrfToken;
function SendMessage() {
    const content = document.getElementById('message-content').value.trim();
    if (content === '') {
        alert('Please enter a message.');
        return;
    }

    const formData = new FormData();
    formData.append('content', content);
    formData.append('csrfmiddlewaretoken', csrf);

    fetch(window.ChatConfig.sendMessageUrl, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const chatMessages = document.getElementById('chat-messages');
            const newMessage = document.createElement('article');
            newMessage.classList.add('d-flex', 'mx-3', 'flex-row-reverse');
            newMessage.id = `message-${data.message_id}`;
            newMessage.innerHTML = `
                <p class="message d-flex bg-info mb-1 px-3 py-2 flex-wrap">
                    ${data.content}
                </p>
                <a href="javascript:void(0);" class="p-2 delete-btn" onclick="deleteMessage(${data.message_id})"><span class="material-symbols-outlined pointer">delete</span></a>
            `;
            chatMessages.appendChild(newMessage);
            document.getElementById('message-content').value = '';
        } else {
            alert('Error sending message: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => console.error('Error:', error));
};

function deleteMessage(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }

    fetch(`/chat/delete-message/${messageId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById(`message-${messageId}`).remove();
        } else {
            alert('Error deleting message: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => console.error('Error:', error));
}

function fetchMessages() {
    const chatMessages = document.getElementById('chat-messages');
    fetch(window.ChatConfig.fetchMessagesUrl, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        chatMessages.innerHTML = '';
        data.messages.forEach(message => {
            const newMessage = document.createElement('article');
            newMessage.classList.add('d-flex', 'mx-3');
            newMessage.id = `message-${message.id}`;
            if (message.is_user_message) {
                newMessage.classList.add('flex-row-reverse');
            }
            newMessage.innerHTML = `
                <p class="message d-flex px-3 py-2 ${message.is_user_message ? 'bg-info' : ''}">
                    ${message.content}
                </p>
                ${message.is_user_message ? `  <span onclick="deleteMessage(${message.id})" class="material-symbols-outlined pointer p-3 delete-btn">delete</span>` : ''}
            `;
            chatMessages.appendChild(newMessage);
        });
    })
    .catch(error => console.error('Error:', error));
}
// Fetch messages every 5 seconds
setInterval(fetchMessages, 5000);

// Initial fetch
fetchMessages();