let page = 1;
let emptyPage = false;
let blockRequest = false;

window.onscroll = function() {
    let margin = document.body.clientHeight - window.innerHeight - 200;
    if (window.pageYOffset > margin && !emptyPage && !blockRequest) {
        blockRequest = true;
        page += 1;
        
        const urlParams = new URLSearchParams(window.location.search);
        const category = urlParams.get('category') || 'for_you';

        // ТЕПЕР СТУКАЄМОСЯ В API ЕНДПОІНТ
        fetch(`/api/posts/?category=${category}&page=${page}`)
        .then(response => {
            if (!response.ok) throw new Error('No more pages');
            return response.json();
        })
        .then(data => {
            // DRF Pagination повертає дані в data.results
            if (data.results.length === 0) {
                emptyPage = true;
            } else {
                const container = document.getElementById('post-list-container');
                
                data.results.forEach(post => {
                    const postHtml = renderPost(post); // Викликаємо функцію малювання
                    container.insertAdjacentHTML('beforeend', postHtml);
                });

                blockRequest = false;
                if (!data.next) emptyPage = true;
            }
        })
        .catch(err => {
            console.log(err);
            emptyPage = true;
        });
    }
};

function renderPost(post) {
    // Перевіряємо аватар
    const avatarUrl = post.user.avatar_url ? post.user.avatar_url : '/static/images/default_avatar.jpg';
    
    // Перевіряємо, чи лайкнув поточний юзер (використовуємо поле is_liked з серіалізатора)
    const likedClass = post.is_liked ? 'liked' : '';
    
    // Перевіряємо, чи є юзер власником (це можна зробити, порівнявши ID)
    // Припускаємо, що currentUserId ми передали в шаблон раніше
    const isOwner = post.is_owner;

    return `
        <br>
        <article class="post-container">
            <section>
                <article class="post-user-info d-flex">
                    <a href="/user/${post.user.id}/">
                        <img src="${avatarUrl}" class="profile-avatar" style="width: 36px;height: 36px;">
                    </a>
                    <a href="/user/${post.user.id}/"><h4><b>${post.user.username}</b></h4></a>
                    <h4 class="gray-text">${new Date(post.date_published).toLocaleDateString()}</h4>
                </article>
                <figure>
                    <img src="${post.media_url}" class="post-media">
                    <section>
                        <span onclick="likePost(${post.id})" class="pointer like-btn ${likedClass}" id="like-btn-${post.id}">
                            <span class="heart">&hearts;</span> 
                        </span>
                        
                        ${isOwner ? `
                            <a href="/update_post/${post.id}/" class="p-2"><span class="material-symbols-outlined pointer">edit</span></a>
                            <a href="/delete_post/${post.id}/" class="p-2"><span class="material-symbols-outlined pointer">delete</span></a>
                        ` : ''}
                        
                        <a href="/post_details/${post.id}/" class="p-2"><span class="material-symbols-outlined pointer">comment</span></a>
                    </section>
                    <h5><span id="like-count-${post.id}">${post.likes_count}</span> likes</h5>
                    
                    ${post.content ? `
                        <figcaption class="truncate-text">
                            <a href="/user/${post.user.id}/"><b>${post.user.username}</b></a> ${post.content}
                        </figcaption>
                    ` : ''}
                </figure>
            </section>
            <br>
        </article>
    `;
}