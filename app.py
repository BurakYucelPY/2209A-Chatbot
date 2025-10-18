import gradio as gr
from dotenv import load_dotenv
from sor_chroma import answer
import os
from pathlib import Path

load_dotenv()

# ----------------- Mantık -----------------
def first_respond(user_msg, chat_history):
    """Hero ekranındaki ilk gönderim."""
    try:
        ans, _ = answer(user_msg)
    except Exception as e:
        ans = f"Hata: {e}"

    chat_history = (chat_history or []) + [(user_msg, ans)]
    return (
        chat_history,
        gr.update(visible=False),   # hero sütunu
        gr.update(visible=True),    # chat sütunu
        "",                         # hero input temizle
        gr.update(value="")         # alt input temizle
    )

def respond(user_msg, chat_history):
    """Sohbet modundaki gönderim."""
    try:
        ans, _ = answer(user_msg)
    except Exception as e:
        ans = f"Hata: {e}"

    chat_history = (chat_history or []) + [(user_msg, ans)]
    return chat_history, ""

# ----------------- UI -----------------
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --primary: #3b82f6;
  --primary-dark: #2563eb;
  --secondary: #8b5cf6;
  --accent: #06b6d4;
  --bg-main: #0a0e27;
  --bg-card: #0f1629;
  --bg-input: #1a1f3a;
  --border: #1e293b;
  --border-light: #334155;
  --text: #f1f5f9;
  --text-muted: #94a3b8;
  --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.1);
  --shadow-md: 0 8px 24px rgba(0,0,0,0.15);
  --shadow-lg: 0 16px 48px rgba(0,0,0,0.25);
  --shadow-glow: 0 0 40px rgba(59,130,246,0.15);
}

* {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

body {
  background: var(--bg-main);
  background-image: 
    radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.1) 0px, transparent 50%),
    radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.1) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.1) 0px, transparent 50%),
    radial-gradient(at 0% 100%, rgba(239, 68, 68, 0.05) 0px, transparent 50%);
  background-attachment: fixed;
}

#root {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* Logo Container */
.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  animation: fadeInDown 0.6s ease-out;
}

.logo-container .gr-image {
  border: none !important;
  border-radius: 50% !important;
  box-shadow: 0 8px 16px rgba(59,130,246,0.3) !important;
  animation: float 3s ease-in-out infinite;
}

.logo-container .gr-image img {
  width: 240px !important;
  height: 240px !important;
  object-fit: contain !important;
  border-radius: 50% !important;
}

/* Logo butonlarını gizle */
.logo-container .gr-image .image-button-row {
  display: none !important;
}

.logo-container .gr-image .download-button,
.logo-container .gr-image .share-button,
.logo-container .gr-image .fullscreen-button {
  display: none !important;
}
  filter: drop-shadow(0 8px 16px rgba(59,130,246,0.3));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Hero Card */
.hero-card {
  background: linear-gradient(135deg, rgba(15, 22, 41, 0.9) 0%, rgba(10, 14, 39, 0.95) 100%);
  border: 1px solid var(--border-light);
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: var(--shadow-lg), var(--shadow-glow);
  backdrop-filter: blur(20px);
  animation: fadeInUp 0.6s ease-out;
}

.title {
  font-size: 48px;
  font-weight: 800;
  text-align: center;
  margin: 0 0 16px;
  background: linear-gradient(135deg, #60a5fa, #a78bfa, #34d399);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  letter-spacing: -0.5px;
  animation: fadeInUp 0.6s ease-out 0.1s both;
}

.subtitle {
  color: var(--text-muted);
  text-align: center;
  font-size: 16px;
  line-height: 1.6;
  margin: 0 0 32px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  animation: fadeInUp 0.6s ease-out 0.2s both;
}

/* Input Styling */
.hero-input-wrapper {
  animation: fadeInUp 0.6s ease-out 0.3s both;
}

.hero-input .gr-textbox,
.footer-input .gr-textbox {
  border: none !important;
  background: transparent !important;
}

.hero-input textarea,
.footer-input textarea {
  background: var(--bg-input) !important;
  border: 2px solid var(--border) !important;
  border-radius: 16px !important;
  color: var(--text) !important;
  font-size: 15px !important;
  padding: 16px 20px !important;
  min-height: 80px !important;
  box-shadow: var(--shadow-sm) !important;
  transition: all 0.3s ease !important;
}

.hero-input textarea:focus,
.footer-input textarea:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1), var(--shadow-md) !important;
  outline: none !important;
}

/* Buttons */
.primary-btn,
.send-btn {
  background: var(--gradient-3) !important;
  border: none !important;
  border-radius: 14px !important;
  font-weight: 600 !important;
  font-size: 15px !important;
  padding: 14px 32px !important;
  color: white !important;
  box-shadow: var(--shadow-md) !important;
  cursor: pointer !important;
  transition: all 0.3s ease !important;
}

.primary-btn:hover,
.send-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg) !important;
  filter: brightness(1.1);
}

.primary-btn:active,
.send-btn:active {
  transform: translateY(0);
}

/* Chat Container */
.chat-container {
  animation: fadeInUp 0.5s ease-out;
}

.chat-card {
  background: linear-gradient(135deg, rgba(15, 22, 41, 0.9) 0%, rgba(10, 14, 39, 0.95) 100%);
  border: 1px solid var(--border-light);
  border-radius: 24px;
  padding: 20px;
  box-shadow: var(--shadow-lg), var(--shadow-glow);
  backdrop-filter: blur(20px);
}

.gr-chatbot {
  border: 1px solid var(--border) !important;
  border-radius: 20px !important;
  background: rgba(10, 14, 39, 0.5) !important;
}

.gr-chatbot .message {
  border-radius: 16px !important;
  padding: 16px 20px !important;
  margin: 8px 0 !important;
  box-shadow: var(--shadow-sm) !important;
  animation: messageSlideIn 0.3s ease-out;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.gr-chatbot .message.user {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(99, 102, 241, 0.15)) !important;
  border: 1px solid rgba(59, 130, 246, 0.3) !important;
  margin-left: auto !important;
}

.gr-chatbot .message.bot {
  background: linear-gradient(135deg, rgba(15, 22, 41, 0.8), rgba(26, 31, 58, 0.8)) !important;
  border: 1px solid var(--border) !important;
}

/* Footer Input Area */
.footer {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(180deg, transparent 0%, rgba(10, 14, 39, 0.8) 30%);
  border-radius: 0 0 24px 24px;
  backdrop-filter: blur(10px);
}

/* Feature Pills */
.feature-pills {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  margin: 24px 0;
  animation: fadeInUp 0.6s ease-out 0.4s both;
}

.pill {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--text);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.pill:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
}

/* Smooth transitions */
.hide {
  opacity: 0;
  transform: translateY(-20px);
  pointer-events: none;
}

.show {
  opacity: 1;
  transform: translateY(0);
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-card);
}

::-webkit-scrollbar-thumb {
  background: var(--border-light);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--primary);
}

/* Responsive */
@media (max-width: 768px) {
  .title {
    font-size: 36px;
  }
  
  .hero-card {
    padding: 32px 24px;
  }
  
  .logo-container .gr-image img {
    width: 180px !important;
    height: 180px !important;
  }
}
"""

# Logo kontrolü
logo_path = "logo.png"
logo_exists = os.path.exists(logo_path)

with gr.Blocks(title="TübiBot — 2209-A", css=CUSTOM_CSS, theme=gr.themes.Soft()) as demo:
    chat_state = gr.State([])

    # ---------------- HERO (İLK EKRAN) ----------------
    with gr.Column(visible=True, elem_classes=["show"], elem_id="hero_col") as hero_col:
        with gr.Column(elem_classes=["hero-card"]):
            # Logo
            if logo_exists:
                with gr.Column(elem_classes=["logo-container"]):
                    gr.Image(
                        value=logo_path, 
                        show_label=False, 
                        container=False,
                        height=240,
                        width=240,
                        interactive=False,
                        show_download_button=False,
                        show_share_button=False,
                        show_fullscreen_button=False
                    )
            
            gr.HTML("<div class='title'>Merhaba, ben <b>TübiBot</b></div>")
            gr.HTML("<div class='subtitle'>TÜBİTAK 2209-A: Belgeler üzerinden kaynak-temelli cevaplar üreten RAG tabanlı yapay zeka asistanı. Sorularınızı doğal dilde sorun, size en doğru yanıtları sunayım.</div>")
            
            # Feature pills
            gr.HTML("""
            <div class='feature-pills'>
                <div class='pill'>🔍 RAG Tabanlı Arama</div>
                <div class='pill'>📚 Kaynak Belirtme</div>
                <div class='pill'>💬 Doğal Dil İşleme</div>
            </div>
            """)
            
            with gr.Row(elem_classes=["hero-input-wrapper"]):
                first_msg = gr.Textbox(
                    placeholder="Sorunu buraya yaz... (örn: 'Projem şehir göllerinde su kalitesi ile biyoçeşitlilik ilişkisini incelemek. 2209-A kapsamında hangi SKA kapsamına girer?')",
                    label=None, 
                    lines=3, 
                    elem_classes=["hero-input"],
                    show_label=False
                )
            
            with gr.Row():
                first_send = gr.Button("🚀 Sohbete Başla", variant="primary", elem_classes=["primary-btn"], size="lg")

    # ---------------- CHAT (İKİNCİ EKRAN) ----------------
    with gr.Column(visible=False, elem_classes=["show", "chat-container"]) as chat_col:
        with gr.Column(elem_classes=["chat-card"]):
            chat = gr.Chatbot(
                height=560,
                bubble_full_width=False,
                avatar_images=(None, None),
                show_copy_button=True,
                show_label=False
            )

            with gr.Column(elem_classes=["footer"]):
                with gr.Row(equal_height=True):
                    msg = gr.Textbox(
                        placeholder="Mesajını buraya yaz ve Enter'a bas...",
                        label=None,
                        lines=2,
                        elem_classes=["footer-input"],
                        scale=10,
                        show_label=False
                    )
                    send = gr.Button("📤", variant="primary", elem_classes=["send-btn"], scale=0, size="lg")

    # ---------------- BAĞLANTILAR ----------------
    first_msg.submit(
        first_respond,
        [first_msg, chat_state],
        [chat, hero_col, chat_col, first_msg, msg],
        queue=False
    )
    first_send.click(
        first_respond,
        [first_msg, chat_state],
        [chat, hero_col, chat_col, first_msg, msg],
        queue=False
    )

    msg.submit(respond, [msg, chat_state], [chat, msg], queue=False)
    send.click(respond, [msg, chat_state], [chat, msg], queue=False)

if __name__ == "__main__":
    demo.launch()