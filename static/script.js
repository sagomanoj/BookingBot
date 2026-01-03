const messagesArea = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typing');

// Auto-resize textarea
userInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    if (this.value === '') this.style.height = '52px';
});

// Enter key to send
userInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function sendQuickMessage(text) {
    userInput.value = text;
    sendMessage();
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Add User Message
    addMessage(text, 'user');
    userInput.value = '';
    userInput.style.height = '52px';

    // Show Typing
    showTyping(true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();

        // Hide Typing
        showTyping(false);

        // Add Bot Message
        // Simple formatting: Convert newlines to <br> and bold common headers
        let formattedResp = formatResponse(data.response);
        addMessage(formattedResp, 'bot');

    } catch (error) {
        showTyping(false);
        addMessage("Sorry, I'm having trouble connecting to the server.", 'bot');
        console.error('Error:', error);
    }
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.classList.add('message', sender);
    div.innerHTML = text; // Allow HTML injected from formatResponse
    messagesArea.appendChild(div);
    scrollToBottom();
}

function showTyping(show) {
    if (show) {
        messagesArea.appendChild(typingIndicator);
        typingIndicator.style.display = 'flex';
    } else {
        typingIndicator.style.display = 'none';
        // Move back to regular flow if needed (hidden)
    }
    scrollToBottom();
}

function scrollToBottom() {
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function formatResponse(text) {
    // Basic markdown-ish parsing
    let html = text.replace(/\n/g, '<br>');

    // Bold specific keys like "Availability:" or "Confirmation #:"
    html = html.replace(/(Confirmation #:)/g, '<strong>$1</strong>');
    html = html.replace(/(Availability for .*?):/g, '<strong>$1</strong>:');

    // Bullet points to dots
    html = html.replace(/- /g, '• ');

    return html;
}
