document.addEventListener("DOMContentLoaded", function () {
    const toggleSnowButton = document.getElementById('toggleSnow');
    const snowContainer = document.querySelector(".snow-container");
    const snowflakes = [];
    let snowing = false;

    // 創建積雪容器並加入到頁面中
    const snowGround = document.createElement("div");
    snowGround.classList.add("snow-ground");
    document.body.appendChild(snowGround);
    snowGround.style.display = "none"; // 初始隱藏積雪

    let accumulatedSnow = 0; // 初始積雪高度

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

                // 增加積雪效果
                if (snowing && accumulatedSnow < viewportHeight * 0.1) { // 確保積雪不會無限制增長
                    accumulatedSnow += 1;
                    snowGround.style.height = `${accumulatedSnow}px`;
                    if (snowGround.style.display === "none") {
                        snowGround.style.display = "block";
                    }
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
            snowGround.style.display = "none"; // 重新開始下雪時隱藏先前的積雪
            accumulatedSnow = 0; // 重置積雪高度
        } else {
            snowflakes.forEach(snowflake => snowflake.remove());
            snowflakes.length = 0;
        }
    }
    function increaseSnowGround() {
        snowGroundHeight += Math.random() * 2; // 隨機增加高度
        snowGround.style.height = `${snowGroundHeight}px`;
        snowGround.style.display = "block"; // 顯示積雪容器
        // 新增：將積雪容器的高度應用到 CSS 中
        snowGround.style.height = `${snowGroundHeight}px`;
    }
    

    const currentDate = new Date();
    const currentMonth = currentDate.getMonth();
    if (currentMonth >= 3 || currentMonth <= 2) { // 考慮冬季月份
        snowing = true;
        generateSnowflakes();
        toggleSnowButton.textContent = "停止下雪";
    }

    toggleSnowButton.addEventListener('click', toggleSnowfall);
});
