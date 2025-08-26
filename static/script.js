// static/script.js

// DOM要素が読み込まれたら実行
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('cocktail-form');
    const input = document.getElementById('book-title-input');
    const loadingDiv = document.getElementById('loading');
    const resultContainer = document.getElementById('result-container');

    form.addEventListener('submit', async (event) => {
        event.preventDefault(); // フォームのデフォルト送信をキャンセル

        const bookTitle = input.value;
        if (!bookTitle) return;

        // ローディング表示を開始
        loadingDiv.classList.remove('hidden');
        resultContainer.innerHTML = ''; // 前回の結果をクリア

        try {
            const response = await fetch('/generate-for-web', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ book_title: bookTitle }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `サーバーエラー: ${response.statusText}`);
            }

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            console.error('Fetch error:', error);
            resultContainer.innerHTML = `<p class="error-message">エラーが発生しました: ${error.message}</p>`;
        } finally {
            // ローディング表示を終了
            loadingDiv.classList.add('hidden');
        }
    });

    function displayResults(data) {
        if (data.error) {
            resultContainer.innerHTML = `<p class="error-message">${data.error}</p>`;
            return;
        }

        // ヘルパー関数: ソースのセクションを生成
        const createSourceSection = (title, icon, sourceData) => {
            let content = '<p>関連情報が見つかりませんでした。</p>';
            if (sourceData && sourceData.url && sourceData.title) {
                content = `
                    <a href="${sourceData.url}" target="_blank">${sourceData.title}</a>
                    <p>→ 解説: ${sourceData.commentary}</p>
                `;
            }
            return `
                <div class="section">
                    <h3>${icon} ${title}</h3>
                    ${content}
                </div>
            `;
        };

        const resultHTML = `
            <div class="cocktail-result">
                <h2>『${data.book_title}』</h2>
                <div class="section">
                    <h3>■ 作品の要約</h3>
                    <p>${data.summary}</p>
                </div>
                <hr>
                ${createSourceSection('ベース', '🍸', data.complementary)}
                ${createSourceSection('スパイス', '🍅', data.contrasting)}
                ${createSourceSection('隠し味', '🌶️', data.tangent)}
                <div class="section">
                    <h3 class="final-twist">🎭 おつまみ</h3>
                    <p class="final-twist">「${data.twist}」</p>
                </div>
            </div>
        `;
        resultContainer.innerHTML = resultHTML;
    }
});
