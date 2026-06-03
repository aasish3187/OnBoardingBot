import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# Extract the block to replace
start_idx = content.find("function processQueryEngine(query) {")
end_idx = content.find("// Framework DOM Interface Render Engines Modules")

if start_idx == -1 or end_idx == -1:
    print("Could not find markers!")
    exit(1)

new_function = """async function processQueryEngine(query) {
            if (!query.trim()) return;
            
            // Render User bubble element logs
            appendMessageDOM({ role: 'user', text: query, time: Date.now() });
            chatInput.value = '';
            updateInputState();

            // Append parsing latency simulated timeline
            showTypingIndicator(true, "Consulting Nexus Knowledge Graph...");
            updateDynamicIsland('thinking');

            // Setup a blank bot message container for streaming
            const msgObj = { role: 'bot', text: '', time: Date.now(), sources: [], followups: [] };
            APP.messages.push(msgObj);
            saveState();

            const welcome = document.getElementById('welcome-screen');
            if (welcome) welcome.remove();

            const row = document.createElement('div');
            row.className = `message-row bot-row`;
            row.style.animation = "msg-in 0.35s var(--ease-out) forwards";

            // Basic Bot Avatar SVG
            let avatarMarkup = `
<div class="msg-avatar bot-avatar-3d" style="background:var(--bg-deep); border:1px solid var(--border); width:40px; height:40px;">
<svg class="bot-avatar-svg" width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" style="overflow: visible;">
<circle cx="40" cy="40" r="36" fill="#fbbf24"/>
<circle cx="26" cy="32" r="4" fill="#1e293b"/>
<circle cx="54" cy="32" r="4" fill="#1e293b"/>
<path d="M26 48 C 26 48, 33 55, 40 55 C 47 55, 54 48, 54 48" stroke="#1e293b" stroke-width="3" stroke-linecap="round" fill="none"/>
</svg>
</div>`;

            row.innerHTML = `
                ${avatarMarkup}
                <div class="msg-bubble bot-bubble">
                    <div class="msg-meta">OnboardBot <span class="msg-time">Just now</span></div>
                    <div class="msg-text" id="streaming-text"></div>
                    <div id="streaming-sources"></div>
                    <div class="msg-actions">
                        <button class="msg-meta-btn" title="Read aloud">Read aloud</button>
                    </div>
                </div>
            `;
            document.getElementById('chat-canvas').appendChild(row);
            
            showTypingIndicator(false);
            
            try {
                // Fetch to real Python backend!
                const response = await fetch('http://localhost:8080/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        company: "Nexus Technologies",
                        message: query,
                        history: APP.history.map(h => ({ role: typeof h === 'string' ? 'user' : 'user', content: typeof h === 'string' ? h : h.query }))
                    })
                });

                if (!response.ok) throw new Error("API Network response was not ok");
                if (response.headers.get('content-type')?.includes('application/json')) {
                    const data = await response.json();
                    msgObj.text = data.answer;
                    document.getElementById('streaming-text').innerHTML = data.answer.replace(/\\n/g, '<br>');
                } else {
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder('utf-8');
                    let fullText = "";

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value, { stream: true });
                        const lines = chunk.split('\\n');
                        for (const line of lines) {
                            if (line.startsWith('data: ') && line !== 'data: [DONE]') {
                                let content = line.substring(6).replace(/\\\\n/g, '\\n');
                                if (content.startsWith('{"sources"')) {
                                    // Parse citations
                                    try {
                                        let cdata = JSON.parse(content);
                                    } catch(e) {}
                                } else {
                                    fullText += content;
                                    let htmlText = fullText.replace(/\\n/g, '<br>');
                                    htmlText = htmlText.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
                                    document.getElementById('streaming-text').innerHTML = htmlText;
                                    scrollToBottom();
                                }
                            } else if (line.startsWith('event: citations')) {
                                // Ignore for simple parsing
                            }
                        }
                    }
                    msgObj.text = fullText;
                }
                
                playSound('receive');
                updateDynamicIsland('idle');
                
                // Maintain system unique context logs pipeline cache
                const existsIdx = APP.history.findIndex(h => (typeof h === 'string' ? h : h.query) === query);
                if (existsIdx !== -1) APP.history.splice(existsIdx, 1);
                APP.history.unshift({ query: query, time: Date.now() });
                if (APP.history.length > 8) APP.history.pop();
                renderHistoryListUI();
                saveState();

                // Clear temporary ID
                document.getElementById('streaming-text').removeAttribute('id');

            } catch (err) {
                console.error("Chat API error:", err);
                document.getElementById('streaming-text').innerHTML = "Sorry, I could not connect to the backend server. Please make sure api.py is running on port 8080.";
                updateDynamicIsland('idle');
            }
        }

        """

content = content[:start_idx] + new_function + "\n\n        " + content[end_idx:]

html_path.write_text(content, encoding="utf-8")
print("Successfully injected async processQueryEngine into onboardbot.html!")
