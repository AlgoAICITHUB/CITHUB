document.addEventListener('DOMContentLoaded', function() {
    var chatbotIcon = document.getElementById('chatbot-container');
    var chatbotMessage = document.getElementById('chatbot-message');

    chatbotIcon.addEventListener('click', function() {
        var isDisplayed = chatbotMessage.style.display !== 'none';
        chatbotMessage.style.display = isDisplayed ? 'none' : 'block';
    });
});
