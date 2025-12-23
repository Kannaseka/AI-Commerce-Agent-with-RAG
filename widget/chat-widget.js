/**
 * Roze AI Chat Widget
 * Embeddable chat widget for websites
 */

(function() {
    'use strict';
    
    // Configuration (loaded from backend)
    let config = {
        apiEndpoint: 'http://localhost:8002',
        position: 'bottom-right',
        primaryColor: '#007bff',
        secondaryColor: '#6c757d',
        textColor: '#ffffff',
        welcomeMessage: 'Hello! How can I help you today?',
        autoOpenDelay: 0,
        botAvatar: '🤖'
    };

    // State
    let isOpen = false;
    let chatHistory = [];

    // Load configuration from backend
    async function loadConfig() {
        try {
            const response = await fetch(`${config.apiEndpoint}/admin/settings`);
            const settings = await response.json();
            
            // Update config with backend settings
            config = {
                ...config,
                position: settings.widget_position || config.position,
                primaryColor: settings.primary_color || config.primaryColor,
                secondaryColor: settings.secondary_color || config.secondaryColor,
                textColor: settings.text_color || config.textColor,
                welcomeMessage: settings.welcome_message || config.welcomeMessage,
                autoOpenDelay: settings.auto_open_delay || 0
            };
            
            applyStyles();
        } catch (error) {
            console.warn('Using default widget configuration');
        }
    }

    // Create widget HTML
    function createWidget() {
        const widgetHTML = `
            <div id="roze-chat-widget" class="roze-chat-widget">
                <!-- Chat Button -->
                <div id="roze-chat-button" class="roze-chat-button" onclick="window.RozeChat.toggle()">
                    <span class="roze-chat-icon">${config.botAvatar}</span>
                    <span class="roze-chat-badge" id="roze-unread-badge" style="display: none;">1</span>
                </div>

                <!-- Chat Window -->
                <div id="roze-chat-window" class="roze-chat-window" style="display: none;">
                    <!-- Header -->
                    <div class="roze-chat-header">
                        <div class="roze-chat-header-content">
                            <span class="roze-chat-avatar">${config.botAvatar}</span>
                            <div class="roze-chat-title">
                                <strong>Roze AI Assistant</strong>
                                <span class="roze-chat-status">Online</span>
                            </div>
                        </div>
                        <button class="roze-chat-close" onclick="window.RozeChat.toggle()">✕</button>
                    </div>

                    <!-- Messages -->
                    <div id="roze-chat-messages" class="roze-chat-messages">
                        <div class="roze-message roze-message-bot">
                            <div class="roze-message-content">${config.welcomeMessage}</div>
                        </div>
                    </div>

                    <!-- Typing Indicator -->
                    <div id="roze-typing-indicator" class="roze-typing-indicator" style="display: none;">
                        <span></span><span></span><span></span>
                    </div>

                    <!-- Input -->
                    <div class="roze-chat-input-container">
                        <input 
                            type="text" 
                            id="roze-chat-input" 
                            class="roze-chat-input" 
                            placeholder="Type a message..."
                            onkeypress="if(event.key === 'Enter') window.RozeChat.sendMessage()"
                        >
                        <button class="roze-chat-send" onclick="window.RozeChat.sendMessage()">
                            ➤
                        </button>
                    </div>
                </div>
            </div>
        `;

        const container = document.createElement('div');
        container.innerHTML = widgetHTML;
        document.body.appendChild(container.firstElementChild);
    }

    // Apply dynamic styles
    function applyStyles() {
        const styleId = 'roze-chat-styles';
        let styleElement = document.getElementById(styleId);
        
        if (styleElement) {
            styleElement.remove();
        }

        const styles = `
            .roze-chat-widget {
                position: fixed;
                ${getPositionStyles()}
                z-index: 999999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }

            .roze-chat-button {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, ${config.primaryColor} 0%, ${config.secondaryColor} 100%);
                color: ${config.textColor};
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transition: all 0.3s ease;
                position: relative;
            }

            .roze-chat-button:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(0,0,0,0.25);
            }

            .roze-chat-icon {
                font-size: 28px;
            }

            .roze-chat-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                background: #e74c3c;
                color: white;
                border-radius: 50%;
                width: 22px;
                height: 22px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: bold;
            }

            .roze-chat-window {
                width: 380px;
                height: 550px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                margin-bottom: 80px;
            }

            .roze-chat-header {
                background: linear-gradient(135deg, ${config.primaryColor} 0%, ${config.secondaryColor} 100%);
                color: ${config.textColor};
                padding: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .roze-chat-header-content {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .roze-chat-avatar {
                font-size: 32px;
            }

            .roze-chat-title strong {
                display: block;
                font-size: 16px;
            }

            .roze-chat-status {
                font-size: 12px;
                opacity: 0.9;
            }

            .roze-chat-close {
                background: rgba(255,255,255,0.2);
                border: none;
                color: ${config.textColor};
                width: 32px;
                height: 32px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 18px;
                transition: all 0.3s;
            }

            .roze-chat-close:hover {
                background: rgba(255,255,255,0.3);
            }

            .roze-chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                background: #f7fafc;
            }

            .roze-message {
                margin-bottom: 16px;
                display: flex;
            }

            .roze-message-bot .roze-message-content {
                background: white;
                color: #2d3748;
                border-radius: 12px 12px 12px 4px;
                padding: 12px 16px;
                max-width: 75%;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }

            .roze-message-user {
                justify-content: flex-end;
            }

            .roze-message-user .roze-message-content {
                background: ${config.primaryColor};
                color: ${config.textColor};
                border-radius: 12px 12px 4px 12px;
                padding: 12px 16px;
                max-width: 75%;
            }

            .roze-typing-indicator {
                padding: 12px 20px;
                display: flex;
                gap: 4px;
            }

            .roze-typing-indicator span {
                width: 8px;
                height: 8px;
                background: ${config.secondaryColor};
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }

            .roze-typing-indicator span:nth-child(2) {
                animation-delay: 0.2s;
            }

            .roze-typing-indicator span:nth-child(3) {
                animation-delay: 0.4s;
            }

            @keyframes typing {
                0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
                30% { transform: translateY(-10px); opacity: 1; }
            }

            .roze-chat-input-container {
                display: flex;
                padding: 12px;
                background: white;
                border-top: 1px solid #e2e8f0;
            }

            .roze-chat-input {
                flex: 1;
                border: 2px solid #e2e8f0;
                border-radius: 24px;
                padding: 10px 16px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.3s;
            }

            .roze-chat-input:focus {
                border-color: ${config.primaryColor};
            }

            .roze-chat-send {
                background: ${config.primaryColor};
                color: ${config.textColor};
                border: none;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                margin-left: 8px;
                cursor: pointer;
                transition: all 0.3s;
                font-size: 18px;
            }

            .roze-chat-send:hover {
                transform: scale(1.1);
            }

            @media (max-width: 480px) {
                .roze-chat-window {
                    width: 100vw;
                    height: 100vh;
                    border-radius: 0;
                    margin: 0;
                }
                
                .roze-chat-widget {
                    ${config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
                    bottom: 20px;
                }
            }
        `;

        styleElement = document.createElement('style');
        styleElement.id = styleId;
        styleElement.textContent = styles;
        document.head.appendChild(styleElement);
    }

    function getPositionStyles() {
        const positions = {
            'bottom-right': 'bottom: 20px; right: 20px;',
            'bottom-left': 'bottom: 20px; left: 20px;',
            'top-right': 'top: 20px; right: 20px;',
            'top-left': 'top: 20px; left: 20px;'
        };
        return positions[config.position] || positions['bottom-right'];
    }

    // Toggle chat window
    function toggle() {
        isOpen = !isOpen;
        const chatWindow = document.getElementById('roze-chat-window');
        const badge = document.getElementById('roze-unread-badge');
        
        if (isOpen) {
            chatWindow.style.display = 'flex';
            badge.style.display = 'none';
        } else {
            chatWindow.style.display = 'none';
        }
    }

    // Send message
    async function sendMessage() {
        const input = document.getElementById('roze-chat-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message to UI
        addMessage(message, 'user');
        input.value = '';

        // Show typing indicator
        showTypingIndicator(true);

        // Send to backend
        try {
            const response = await fetch(`${config.apiEndpoint}/api/test-chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            
            // Hide typing indicator
            showTypingIndicator(false);

            // Add bot response
            addMessage(data.response, 'bot');

            // Track analytics
            trackMessage(message, data.response);

        } catch (error) {
            showTypingIndicator(false);
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    }

    function addMessage(text, sender) {
        const messagesContainer = document.getElementById('roze-chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `roze-message roze-message-${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'roze-message-content';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Store in history
        chatHistory.push({ sender, text, timestamp: new Date() });
    }

    function showTypingIndicator(show) {
        const indicator = document.getElementById('roze-typing-indicator');
        indicator.style.display = show ? 'flex' : 'none';
    }

    async function trackMessage(userMessage, botResponse) {
        try {
            await fetch(`${config.apiEndpoint}/api/analytics/track`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_message: userMessage,
                    bot_response: botResponse,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            // Silent fail for analytics
        }
    }

    // Auto-open logic
    function autoOpen() {
        if (config.autoOpenDelay > 0) {
            setTimeout(() => {
                if (!isOpen) {
                    toggle();
                    document.getElementById('roze-unread-badge').style.display = 'flex';
                }
            }, config.autoOpenDelay * 1000);
        }
    }

    // Initialize
    async function init() {
        await loadConfig();
        createWidget();
        autoOpen();
    }

    // Public API
    window.RozeChat = {
        toggle,
        sendMessage,
        init
    };

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
