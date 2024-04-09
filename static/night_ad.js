document.addEventListener('DOMContentLoaded', function () {
    const hour = new Date().getHours();
    const isNight = hour >= 12 || hour < 6;
    const body = document.body;
  
    // 按鈕事件處理器
    const toggleButton = document.getElementById('toggle-night-mode');
    toggleButton.addEventListener('click', function() {
      body.classList.add('night-mode');
      createStars(200);
    });
  
    if (isNight) {
      body.classList.add('night-mode');
      createStars(200); // 創建200顆星星
    }
  });
  
  // 將createStars函數移到這裡，使其全局可訪問
  function createStars(count) {
    const starsContainer = document.getElementById('stars');
    starsContainer.innerHTML = ''; // 清除現有星星，避免重複添加
    for (let i = 0; i < count; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        star.style.animationDuration = `${Math.random() * 3 + 1}s`;
        star.style.animationDelay = `${Math.random() * 3}s`;
        starsContainer.appendChild(star);
    }
  }
  