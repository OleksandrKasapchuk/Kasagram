function filterPosts(category) {
		const url = new URL(window.location.href);
		url.searchParams.set('category', category);
		url.searchParams.delete('page'); // скидаємо сторінку
		window.location.href = url.toString();
	}
	function changeFilter(filter) {
		const url = new URL(window.location.href);
		url.searchParams.set('filter', filter);
		window.location.href = url.toString();
	}