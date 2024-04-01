document.addEventListener('DOMContentLoaded', function () {
    // 檢查當前時間並啟用夜晚模式
    const hour = new Date().getHours();
    const isNight = hour >= 18 || hour < 6;
    const body = document.body;
    const starsContainer = document.getElementById('stars');

    if (isNight) {
      body.classList.add('night-mode');
      createStars(200); // 創建200顆星星
    }

    function createStars(count) {
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
  });

