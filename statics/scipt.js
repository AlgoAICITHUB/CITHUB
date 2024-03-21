function sendData() {
    const input = document.getElementById('aiInput').value; // 獲取輸入值
    fetch('/predict', { // 假設 '/process_data' 是後端處理數據的路徑
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({data: input}),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('aiOutput').textContent = data.output; // 將輸出顯示在頁面上
    })
    .catch((error) => {
        console.error('Error:', error);
        document.getElementById('aiOutput').textContent = '處理錯誤';
    });
}
