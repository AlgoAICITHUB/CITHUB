document.addEventListener("DOMContentLoaded", function () {
    const toggleSnowButton = document.getElementById('toggleSnow');
    const snowContainer = document.querySelector(".snow-container");
    const snowflakes = [];
    let snowing = false;

    function resetSnowflake(snowflake) {
        const size = Math.random() * 5 + 1;
        const viewportWidth = window.innerWidth - size;
        const viewportHeight = window.innerHeight;

        snowflake.style.width = `${size}px`;
        snowflake.style.height = `${size}px`;
        snowflake.style.left = `${Math.random() * viewportWidth}px`;
        snowflake.style.top = `-${size}px`;

        const animationDuration = (Math.random() * 3 + 2);
        snowflake.style.animationDuration = `${animationDuration}s`;
        snowflake.style.animationTimingFunction = "linear";
        snowflake.style.animationName = Math.random() < 0.5 ? "fall" : "diagonal-fall";

        setTimeout(() => {
            if (parseInt(snowflake.style.top, 10) < viewportHeight) {
                resetSnowflake(snowflake);
            } else {
                snowflake.remove();
                const index = snowflakes.indexOf(snowflake);
                if (index > -1) {
                    snowflakes.splice(index, 1);
                }
            }
        }, animationDuration * 1000);
    }

    function createSnowflake() {
        const snowflake = document.createElement("div");
        snowflake.classList.add("snowflake");
        snowflakes.push(snowflake);
        snowContainer.appendChild(snowflake);
        resetSnowflake(snowflake);
    }

    function generateSnowflakes() {
        if (snowing) {
            createSnowflake();
            setTimeout(generateSnowflakes, 200);
        }
    }

    function toggleSnowfall() {
        snowing = !snowing;
        toggleSnowButton.textContent = snowing ? "停止下雪" : "開始下雪";
        if (snowing) {
            generateSnowflakes();
        } else {
            snowflakes.forEach(snowflake => snowflake.remove());
            snowflakes.length = 0;
        }
    }


    const currentDate = new Date();
    const currentMonth = currentDate.getMonth(); 
    if (currentMonth >= 9) { 
        snowing = true;
        generateSnowflakes();
        toggleSnowButton.textContent = "停止下雪";
    }

    toggleSnowButton.addEventListener('click', toggleSnowfall);
});
