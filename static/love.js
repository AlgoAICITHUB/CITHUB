document.addEventListener('DOMContentLoaded', function() {
    const today = new Date();
    // Set for demonstration. Change to match the current date or Valentine's Day (Month is 0-indexed)
    if (today.getMonth() === 1 && today.getDate() === 14) {
      for (let i = 0; i < 50; i++) { // Creates 50 hearts for a fuller effect
        createHeart();
      }
    }
  });
  
  function createHeart() {
    const heart = document.createElement('div');
    heart.className = 'heart';
    heart.style.left = Math.random() * 100 + 'vw';
    heart.style.bottom = Math.random() * 100 + 'px'; // Start from different positions at the bottom
    heart.style.animationDuration = Math.random() * 3 + 2 + 's'; // Random animation time for variety
  
    document.getElementById('valentine').appendChild(heart);
  
    setTimeout(() => {
      heart.remove(); // Removes the heart after it floats up
    }, 5000);
  }