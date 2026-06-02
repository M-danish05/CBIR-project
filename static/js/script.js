// Image preview
document.getElementById('image-input').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('preview-image').src = e.target.result;
            document.getElementById('preview-container').style.display = 'block';
        }
        reader.readAsDataURL(file);
    }
});

// Drag and drop
const uploadBox = document.getElementById('upload-box');

uploadBox.addEventListener('dragover', function(e) {
    e.preventDefault();
    uploadBox.style.background = '#f0f0ff';
    uploadBox.style.borderColor = '#764ba2';
});

uploadBox.addEventListener('dragleave', function() {
    uploadBox.style.background = '';
    uploadBox.style.borderColor = '#667eea';
});

uploadBox.addEventListener('drop', function(e) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
        document.getElementById('image-input').files = e.dataTransfer.files;
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('preview-image').src = e.target.result;
            document.getElementById('preview-container').style.display = 'block';
        }
        reader.readAsDataURL(file);
    }
});
// Dark Mode Toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const btn = document.querySelector('.dark-mode-btn');
    if (document.body.classList.contains('dark-mode')) {
        btn.textContent = '☀️ Light Mode';
        localStorage.setItem('darkMode', 'enabled');
    } else {
        btn.textContent = '🌙 Dark Mode';
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Check saved dark mode preference
window.onload = function() {
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        document.querySelector('.dark-mode-btn').textContent = '☀️ Light Mode';
    }
}
// AI Chatbot
function sendMessage() {
    const input = document.getElementById('chat-input');
    const chatBox = document.getElementById('chat-box');
    const message = input.value.trim();
    
    if (!message) return;

    // Show user message
    chatBox.innerHTML += `<div class="user-msg">👤 ${message}</div>`;
    input.value = '';

    // Send to AI
    fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `message=${encodeURIComponent(message)}`
    })
    .then(res => res.json())
    .then(data => {
        chatBox.innerHTML += `<div class="ai-msg">🤖 ${data.response}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(err => {
        chatBox.innerHTML += `<div class="ai-msg">🤖 Error: ${err}</div>`;
    });
}

// Send on Enter key
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('chat-input');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    }
});