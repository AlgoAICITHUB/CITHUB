document.addEventListener('DOMContentLoaded', function() {
    const toggleHeartsButton = document.getElementById('toggleHearts');
    toggleHeartsButton.addEventListener('click', function() {
      for (let i = 0; i < 50; i++) {
        createHeart();
      }
    });
  });
  
  function createHeart() {
    const heart = document.createElement('div');
    heart.className = 'heart';
    heart.style.left = Math.random() * 100 + 'vw';
    heart.style.animationDuration = Math.random() * 3 + 2 + 's';
  
    document.getElementById('valentine').appendChild(heart);
  
    setTimeout(() => {
      heart.remove();
    }, 5000);
  }
  