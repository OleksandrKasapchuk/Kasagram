function likePost(postId) {
    const csrf = window.DjangoConfig.csrfToken;
    const loginUrl = window.DjangoConfig.loginUrl;
    const likeBtn = document.getElementById('like-btn-' + postId);
    const likeCount = document.getElementById('like-count-' + postId);

    fetch(`/like/${postId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        },
        body: JSON.stringify({})
    })
    .then(response => {
        if (response.status === 403) {
            window.location.href = loginUrl;
            return;
        }
        return response.json();
    })
    .then(data => {
        likeCount.textContent = data.likes_count;
        if (data.liked) {
            likeBtn.classList.add('liked');
        } else {
            likeBtn.classList.remove('liked');
        }
    })
    .catch(error => console.error('Error:', error));
}
    function toggleFollow(userId) {

		fetch(`/toggle-follow/${userId}`, {
			method: 'POST',
			headers: {
				'X-CSRFToken': window.DjangoConfig.csrfToken,
				'X-Requested-With': 'XMLHttpRequest',
			},
			body: JSON.stringify({ user_id: userId })
		})
		.then(response => response.json())
		.then(data => {
			if (data.error) {
				alert(data.error);
			} else {
				const followButton = document.getElementById(`follow-button-${userId}`);
				const followersCount = document.getElementById('followers-count');
				const followingCount = document.getElementById('following-count');

				followButton.textContent = data.following ? 'Unfollow' : 'Follow';
				if (followersCount) {
					followersCount.textContent = data.followers_count;
				}
				if (followingCount) {
					followingCount.textContent = data.following_count;
				}
			}
		})
		.catch(error => console.error('Error:', error));
	}