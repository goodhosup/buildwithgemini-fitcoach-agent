import asyncio
import os
import subprocess
import time
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/ms-playwright"

URL = "http://localhost:8080/"
OUTPUT_FILE = "/config/Desktop/BuildWithGemini/fitcoach-agent/fitcoach_demo.webm"
TEMP_DIR = "/config/Desktop/BuildWithGemini/fitcoach-agent/.video_tmp"

QUERIES = [
    "초보자를 위한 20분 맞춤 홈트레이닝 루틴과 주의사항을 알려줘",
    "운동 데이터베이스에서 맨몸 스쿼트 상세 동작을 찾아서 자세와 팁을 알려주고, 스쿼트 동작 안내 이미지도 함께 생성해 줘"
]

FRAME_TITLE = "FitCoach AI Demo"

CSS = """
#gwt-frame {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 2147483647;
  box-sizing: border-box;
  border: 10px solid transparent;
  border-image: linear-gradient(135deg, #0d9488, #14b8a6, #3b82f6) 10;
}
#gwt-badge {
  position: fixed;
  top: 18px;
  right: 22px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(15, 23, 42, 0.88);
  color: #f1f5f9;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 13px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 9999px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.15);
}
"""

async def inject_frame(page):
    try:
        await page.evaluate(f"""() => {{
            if (!document.getElementById('gwt-overlay-style')) {{
                const style = document.createElement('style');
                style.id = 'gwt-overlay-style';
                style.textContent = `{CSS}`;
                (document.head || document.documentElement).appendChild(style);
            }}
            if (!document.getElementById('gwt-frame')) {{
                const frame = document.createElement('div');
                frame.id = 'gwt-frame';
                const badge = document.createElement('div');
                badge.id = 'gwt-badge';
                badge.innerHTML = `<span>⚡</span><span>{FRAME_TITLE}</span>`;
                frame.appendChild(badge);
                document.documentElement.appendChild(frame);
            }}
        }}""")
    except Exception as e:
        pass

async def main():
    if os.path.exists(TEMP_DIR):
        subprocess.run(["rm", "-rf", TEMP_DIR])
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("--- Starting FitCoach AI Demo Recorder ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        viewport = {"width": 1280, "height": 800}
        context = await browser.new_context(
            viewport=viewport,
            record_video_dir=TEMP_DIR,
            record_video_size=viewport,
        )
        page = await context.new_page()

        print(f"Navigating to {URL}...")
        await page.goto(URL, wait_until="networkidle", timeout=30000)
        await inject_frame(page)
        await asyncio.sleep(2.5)

        input_selector = '#input, textarea, input[type="text"]'
        chat_input = page.locator(input_selector).first

        for i, query in enumerate(QUERIES):
            print(f"\n[Turn {i+1}/{len(QUERIES)}] Typing: {query}")
            await inject_frame(page)
            await chat_input.click()
            await asyncio.sleep(0.5)
            await chat_input.press_sequentially(query, delay=35)
            await asyncio.sleep(0.8)
            print("Sending message...")
            await chat_input.press("Enter")

            # First query takes ~8-12s, second query (DB search + image gen) takes ~15-25s
            wait_time = 15 if i == 0 else 30
            print(f"Waiting {wait_time}s for response...")
            await asyncio.sleep(wait_time)

        # Hold on final state
        await asyncio.sleep(3.0)
        print("Finishing recording...")
        await page.close()
        await context.close()
        await browser.close()

    # Find the recorded video in TEMP_DIR
    videos = [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR) if f.endswith(".webm")]
    if not videos:
        print("ERROR: No video file was generated.")
        return

    raw_video = videos[0]
    print(f"Raw video saved at: {raw_video}")

    # Speed up 1.5x with ffmpeg
    speed = 1.5
    pts = 1.0 / speed
    cmd = [
        "ffmpeg", "-y", "-i", raw_video,
        "-filter:v", f"setpts={pts}*PTS",
        "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "30",
        OUTPUT_FILE
    ]
    print(f"Applying {speed}x speed with ffmpeg...")
    subprocess.run(cmd, check=True)
    subprocess.run(["rm", "-rf", TEMP_DIR])
    print(f"\nSUCCESS: Demo video saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
