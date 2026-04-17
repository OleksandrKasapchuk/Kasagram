const csrf = window.DjangoConfig.csrfToken;
let currentParentId = null;

function SendComment(postId) {
    const textarea = document.getElementById('message-content');
    const content = textarea.value.trim();
    
    if (content === '') {
        alert('Please enter the text.');
        return;
    }

    const formData = new FormData();
    formData.append('content', content);
    formData.append('csrfmiddlewaretoken', csrf);
    
    // ДОДАЄМО ЦЕ: якщо є ID батька, відправляємо його
    if (currentParentId) {
        formData.append('parent_id', currentParentId);
    }
    fetch('/api/comments/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        },
        body: JSON.stringify({
            content: content,
            post: postId,
            parent_id: currentParentId || null
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        const newCommentHtml = `
            <section class="d-flex flex-column flex-grow-1">
                <section class="d-flex">
                    <a href="/users/${data.user.id}/">
                        <img src="${data.user.avatar_url}" class="sidebar-avatar me-3">
                    </a>
                    <p>
                        <a href="/users/${data.user.id}"><b>${data.user.username}</b></a> 
                        ${data.content}
                    </p>
                </section>
                <div class="d-flex gap-3 align-items-center">
                    <small class="gray-text">now</small>
                    <small class="pointer text-secondary fw-bold" onclick="prepareReply(${data.id}, '{{ comment.user.username }}')">Reply</small>
                </div>
            </section>
            <section class="mb-3">
                <a href="/update-comment/${data.id}/"><span class="material-symbols-outlined pointer">edit</span></a>
                <span onclick="deleteComment(${data.id})" class="material-symbols-outlined pointer">delete</span>
            </section>
        `;

        const newComment = document.createElement('li');
        newComment.id = `comment-${data.id}`;
        newComment.classList.add('comment-container', 'mt-3', 'd-flex');
        newComment.innerHTML = newCommentHtml;

        // ЛОГІКА ВСТАВКИ:
        if (currentParentId) {
            // Якщо це відповідь — шукаємо батьківський <li> і вставляємо в його контейнер реплаїв
            const parentLi = document.getElementById(`comment-${currentParentId}`);
            // Шукаємо всередині батька контейнер <article class="ms-5">, який ти створив у HTML
            let repliesContainer = parentLi.querySelector('article.ms-3');
            repliesContainer.insertAdjacentElement('afterbegin', newComment);
            
            // Скидаємо стан відповіді
            cancelReply();
        } else {
            // Якщо це звичайний коментар — просто в кінець головного списку
            document.getElementById('comments').insertAdjacentElement('afterbegin', newComment);
        }

        textarea.value = '';
    })
    .catch(error => console.error('Error:', error));
}

const messageInput = document.getElementById('message-content');

messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        
        const sendBtn = document.querySelector('span[onclick^="SendComment"]');
        if (sendBtn) {
            sendBtn.click(); // Це викличе SendComment з потрібним ID поста
        }
    }
});

function deleteComment(commentId) {
    if (!confirm('Are you sure you want to delete this comment?')) {
        return;
    }

    fetch(`/api/comments/delete/${commentId}/`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        }
    })
    .then(response => {
        if (response.ok) {
            const commentElement = document.getElementById('comment-' + commentId);
            const repliesContainer = commentElement.querySelector('.replies-list');
            
            if (repliesContainer && repliesContainer.children.length > 0) {
                // ПЕРЕД видаленням батька переносимо реплаї в головний список
                const mainCommentsList = document.getElementById('comments');
                
                while (repliesContainer.firstChild) {
                    let reply = repliesContainer.firstChild;
                    // Можемо додати клас, щоб візуально було видно, що це колишній реплай
                    mainCommentsList.appendChild(reply); 
                }
            }
            
            commentElement.remove();
        }
    })
    .catch(error => console.error('Error:', error));
}

// Функція, яка спрацьовує при натисканні "Reply"
function prepareReply(commentId, username) {
    currentParentId = commentId; // Запам'ятовуємо, кому відповідаємо
    
    // Знаходимо елементи UI
    const previewBar = document.getElementById('reply-preview');
    const usernameSpan = document.getElementById('reply-to-username');
    const textarea = document.getElementById('message-content');

    // 1. Оновлюємо нікнейм у плашці
    usernameSpan.innerText = '@' + username;
    
    // 2. Показуємо плашку (прибираємо bootstrap клас d-none)
    previewBar.classList.remove('d-none');
    
    // 3. Ставимо фокус на поле вводу
    textarea.focus();
    
    // Опціонально: прокручуємо вниз до поля вводу
    previewBar.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

// Функція скасування відповіді (натискання на хрестик)
function cancelReply() {
    currentParentId = null; // Обнуляємо батьківський ID
    
    // Приховуємо плашку (додаємо bootstrap клас d-none)
    document.getElementById('reply-preview').classList.add('d-none');
}