import re
from pathlib import Path

html_path = Path("onboardbot.html")
content = html_path.read_text(encoding="utf-8")

# 1. Insert Company Selection Modal CSS + HTML
modal_css_html = """
    <!-- Company Selection Modal -->
    <style>
        #company-selection-modal {
            position: fixed; inset: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(12px);
            z-index: 99999; display: flex; align-items: center; justify-content: center;
        }
        .cs-card {
            background: var(--glass-bg); border: 1px solid var(--accent); border-radius: var(--radius-lg);
            padding: 30px; max-width: 400px; width: 100%; text-align: center; color: white;
            box-shadow: var(--shadow-glow);
        }
        .cs-card input {
            width: 100%; padding: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border);
            background: var(--bg-deep); color: white; margin: 15px 0; font-family: var(--font-ui);
        }
        .cs-card button {
            background: var(--accent); color: white; border: none; padding: 12px 24px;
            border-radius: var(--radius-full); cursor: pointer; font-weight: bold; width: 100%;
        }
        .cs-card button:hover { background: var(--system-blue); }
        #cs-loading { display: none; margin-top: 15px; font-size: 0.9em; color: var(--accent); }
    </style>
    <div id="company-selection-modal">
        <div class="cs-card">
            <h2>🏢 Select Company</h2>
            <p style="font-size: 0.9em; color: #aaa; margin-top: 8px;">Enter any MNC to build its Knowledge Base in real-time.</p>
            <input type="text" id="cs-input" placeholder="e.g. Google, Netflix, TCS..." />
            <button id="cs-btn">Build Knowledge Base</button>
            <div id="cs-loading">Building dynamic knowledge base... Please wait...</div>
        </div>
    </div>
"""
content = content.replace("<body>", f"<body>\n{modal_css_html}")

# 2. Update processQueryEngine to use fetch API
fetch_js = """
        // Core RAG Semantic Engine Execution Pipelines
        async function processQueryEngine(query) {
            if (!query.trim()) return;
            
            appendMessageDOM({ role: 'user', text: query, time: Date.now() });
            chatInput.value = '';
            updateInputState();

            showTypingIndicator(true, "Consulting dynamic documents...");
            updateDynamicIsland('thinking');

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        company: window.activeCompany || "Nexus Technologies",
                        message: query,
                        history: APP.messages.filter(m => m.role !== 'bot' || m.text).map(m => ({
                            role: m.role === 'bot' ? 'assistant' : 'user',
                            content: m.text
                        }))
                    })
                });

                showTypingIndicator(false);
                updateDynamicIsland('idle');

                if (response.headers.get('content-type')?.includes('application/json')) {
                    const data = await response.json();
                    appendMessageDOM({
                        role: 'bot',
                        text: data.answer,
                        time: Date.now(),
                        sources: data.citations ? data.citations.map(c => c.source) : []
                    });
                } else {
                    // Handle SSE stream manually (simplified for DOM updates)
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    
                    let botMsg = { role: 'bot', text: '', time: Date.now(), sources: [] };
                    appendMessageDOM(botMsg);
                    
                    // We need to find the DOM element we just appended to update it
                    const bubbles = document.querySelectorAll('.bot-bubble div:first-child');
                    const currentBubble = bubbles[bubbles.length - 1];
                    
                    let buffer = "";
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\\n\\n');
                        buffer = lines.pop(); // Keep incomplete chunk in buffer
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data === '[DONE]') break;
                                
                                // Clean up escaped newlines
                                const chunkText = data.replace(/\\\\n/g, '\\n');
                                botMsg.text += chunkText;
                                
                                // Render current text
                                let html = botMsg.text.replace(/\\n/g, '<br>');
                                html = html.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
                                currentBubble.innerHTML = html;
                                scrollCanvasToBottom();
                            }
                        }
                    }
                    playSound('receive');
                }
                
                // Track history
                const existsIdx = APP.history.findIndex(h => (typeof h === 'string' ? h : h.query) === query);
                if (existsIdx !== -1) APP.history.splice(existsIdx, 1);
                APP.history.unshift({ query: query, time: Date.now() });
                if (APP.history.length > 8) APP.history.pop();
                renderHistoryListUI();
                saveState();

            } catch (err) {
                console.error(err);
                showTypingIndicator(false);
                updateDynamicIsland('idle');
                showToast("Connection to engine failed.", "error");
            }
        }
"""
# We'll use regex to replace processQueryEngine entirely
content = re.sub(r'// Core RAG Semantic Engine Execution Pipelines\s+function processQueryEngine\(query\) \{.*?(?=\n        // Framework DOM Interface Render Engines Modules)', fetch_js, content, flags=re.DOTALL)

# 3. Add promptCompanySelection to initializeApplicationCoreEngineSequence
company_js = """
            // Company Selection
            window.activeCompany = "Nexus Technologies";
            document.getElementById('cs-btn').addEventListener('click', async () => {
                const comp = document.getElementById('cs-input').value.trim();
                if(!comp) return;
                
                document.getElementById('cs-loading').style.display = 'block';
                document.getElementById('cs-btn').disabled = true;
                
                try {
                    const res = await fetch('/api/set_company', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ company: comp })
                    });
                    const data = await res.json();
                    
                    if(data.status === 'success') {
                        window.activeCompany = data.company_info.full_name || comp;
                        document.getElementById('company-selection-modal').style.display = 'none';
                        
                        // Update UI Brands
                        document.querySelectorAll('.brand-title').forEach(el => el.innerText = "OnboardBot");
                        document.querySelectorAll('.brand-company').forEach(el => el.innerText = window.activeCompany);
                        
                        const greetingLabel = document.querySelector('.welcome-greeting');
                        if (greetingLabel) greetingLabel.innerHTML = `${getGreeting()}<br><span style="color:var(--text-dim); font-size:0.95rem;">Your guide to life at ${window.activeCompany}</span>`;
                        
                    } else {
                        alert("Error: " + data.detail);
                    }
                } catch(e) {
                    alert("API Error. Make sure python api.py is running.");
                } finally {
                    document.getElementById('cs-loading').style.display = 'none';
                    document.getElementById('cs-btn').disabled = false;
                }
            });
"""
# Insert right before console.log("OnboardBot Core Runtime Systems...
content = content.replace('console.log("OnboardBot Core Runtime Systems', company_js + '\n            console.log("OnboardBot Core Runtime Systems')

html_path.write_text(content, encoding="utf-8")
print("Successfully patched onboardbot.html!")
