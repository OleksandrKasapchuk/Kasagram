const csrf = window.DjangoConfig.csrfToken;
function SendComment(postId) {
    const content = document.getElementById('message-content').value.trim();
    if (content === '') {
        alert('Please enter the text.');
        return;
    }

    const formData = new FormData();
    formData.append('content', content);
    formData.append('csrfmiddlewaretoken', csrf);

    fetch(`/post_details/${postId}/` , {
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
            const postComments = document.getElementById('comments');
            const newComment = document.createElement('li');
            newComment.classList.add('comment-container', 'mt-3', 'd-flex');
            newComment.innerHTML = `
                <section class="d-flex flex-column">
                    <section class="d-flex">
                        <a href="${data.user_url}"><img src="${data.avatar_url}" class="sidebar-avatar me-3"></a>
                        <p><a href="${data.user_url}"><b>${data.username}</b></a> ${data.content}</p>
                    </section>
                    <p class="gray-text">${data.date_published}</p>
                </section>
                <section>
                    <a href="${data.update_url}/"><span class="material-symbols-outlined pointer">edit</span></a>
                    <a href="${data.delete_url}/"><span class="material-symbols-outlined pointer">delete</span></a>
                </section>
            `;
            postComments.appendChild(newComment);
            document.getElementById('message-content').value = '';
        } else {
            alert('Error sending message: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => console.error('Error:', error));
}
	function deleteComment(commentId) {
		if (!confirm('Are you sure you want to delete this comment?')) {
			return;
		}

		fetch(`/delete-comment/${commentId}/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrf
			}
		})
		.then(response => response.json())
		.then(data => {
			if (data.success) {
				document.getElementById('comment-' + commentId).remove();
			}
		})
		.catch(error => console.error('Error:', error));
	}