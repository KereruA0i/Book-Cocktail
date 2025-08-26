// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('cocktail-form');
    const input = document.getElementById('user-input');
    const loadingDiv = document.getElementById('loading');
    const resultContainer = document.getElementById('result-container');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const userInput = input.value;
        if (!userInput) return;

        loadingDiv.classList.remove('hidden');
        resultContainer.innerHTML = '';

        try {
            const response = await fetch('/generate-for-web', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_input: userInput }),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || `サーバーエラー: ${response.statusText}`);
            }
            displayResults(data);
        } catch (error) {
            console.error('Fetch error:', error);
            resultContainer.innerHTML = `<p class="error-message">エラーが発生しました: ${error.message}</p>`;
        } finally {
            loadingDiv.classList.add('hidden');
        }
    });

    function displayResults(data) {
        if (data.error) {
            resultContainer.innerHTML = `<p class="error-message">${data.error}</p>`;
            return;
        }
        const createSourceSection = (title, icon, sourceData) => {
            let content = '<p>関連情報が見つかりませんでした。</p>';
            if (sourceData && sourceData.url && sourceData.title) {
                content = `<a href="${sourceData.url}" target="_blank">${sourceData.title}</a><p>→ 解説: ${sourceData.commentary}</p>`;
            }
            return `<div class="section"><h3>${icon} ${title}</h3>${content}</div>`;
        };
        const resultHTML = `
            <div class="cocktail-result">
                <h2>『${data.book_title}』</h2>
                <div class="section"><h3>■ 作品の要約</h3><p>${data.summary}</p></div><hr>
                ${createSourceSection('ベース', '🍸', data.complementary)}
                ${createSourceSection('スパイス', '🍅', data.contrasting)}
                ${createSourceSection('隠し味', '🌶️', data.tangent)}
                <div class="section"><h3 class="final-twist">🥜 おつまみ</h3><p class="final-twist">「${data.twist}」</p></div>
            </div>`;
        resultContainer.innerHTML = resultHTML;
    }
});
