function sendMessage() {
    const input = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const message = input.value.trim();
    
    if (message) {
        addMessage(message, 'user');
        input.value = '';
        
        // Disable input and show loading state
        input.disabled = true;
        sendButton.disabled = true;
        sendButton.classList.add('loading');
        
        // Start countdown animation with 0.1s resolution
        let countdown = 3.0;
        sendButton.textContent = countdown.toFixed(1);
        
        const countdownInterval = setInterval(() => {
            countdown -= 0.1;
            if (countdown > 0) {
                sendButton.textContent = countdown.toFixed(1);
            } else {
                clearInterval(countdownInterval);
                
                // Simulate bot response
                addMessage('This is a simulated response to: "' + message + '"', 'bot');
                
                // Reset button state
                sendButton.classList.remove('loading');
                sendButton.disabled = false;
                sendButton.textContent = 'Send';
                input.disabled = false;
                input.focus();
            }
        }, 100);
    }
}

function addMessage(text, type) {
    const history = document.getElementById('chatHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.textContent = text;
    
    history.appendChild(messageDiv);
    history.scrollTop = history.scrollHeight;
}

function insertQuickMessage(text) {
    document.getElementById('messageInput').value = text;
}

function clearChat() {
    const history = document.getElementById('chatHistory');
    history.innerHTML = '<div class="message bot-message">Chat cleared. How can I help you?</div>';
}

function toggleInfoBubble(icon) {
    // Find the parent bot-message
    const botMessage = icon.closest('.bot-message');
    if (!botMessage) return;
    
    // Find the info bubble within this message
    const infoBubble = botMessage.querySelector('.info-bubble');
    if (!infoBubble) return;
    
    // Hide all other bubbles first
    const allBubbles = document.querySelectorAll('.info-bubble');
    allBubbles.forEach(bubble => {
        if (bubble !== infoBubble) {
            bubble.classList.remove('show');
        }
    });
    
    // Toggle this bubble
    infoBubble.classList.toggle('show');
}

function attachFile() {
    // Placeholder function for file attachment
    console.log('Attach file functionality not implemented yet');
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Auto-resize textarea
const textarea = document.getElementById('messageInput');
textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    
    // Adjust send button position when textarea resizes
    const sendButton = document.getElementById('sendButton');
    const textareaHeight = parseInt(this.style.height);
    if (textareaHeight > 50) {
        sendButton.style.bottom = '8px';
    }
});

// Close info bubbles when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.info-icon')) {
        const allBubbles = document.querySelectorAll('.info-bubble');
        allBubbles.forEach(bubble => {
            bubble.classList.remove('show');
        });
    }
});
