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