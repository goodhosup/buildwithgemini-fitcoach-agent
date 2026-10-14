import base64
import json
import os
import subprocess
import urllib.request

PROJECT = "qwiklabs-gcp-04-0102cc32b1a9"
REGION = "us-central1"
MODEL = "lyria-002"
PROMPT = "lo-fi hip hop, relaxing electric piano, soft drum groove, chill instrumental beats"
VIDEO_INPUT = "/config/Desktop/BuildWithGemini/fitcoach-agent/fitcoach_demo.webm"
VIDEO_OUTPUT = "/config/Desktop/BuildWithGemini/fitcoach-agent/fitcoach_demo_music.webm"
WAV_OUTPUT = "/config/Desktop/BuildWithGemini/fitcoach-agent/lofi_bgm.wav"

def get_token():
    out = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True)
    return out.strip()

def get_video_duration(video_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]
    out = subprocess.check_output(cmd, text=True)
    return float(out.strip())

def main():
    print("1. Requesting Lo-Fi music from Vertex AI Lyria-002...")
    token = get_token()
    url = f"https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{REGION}/publishers/google/models/{MODEL}:predict"
    
    body = {
        "instances": [{"prompt": PROMPT}],
        "parameters": {"sample_count": 1}
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        
    b64_data = res["predictions"][0]["bytesBase64Encoded"]
    wav_bytes = base64.b64decode(b64_data)
    
    with open(WAV_OUTPUT, "wb") as f:
        f.write(wav_bytes)
    print(f"2. Saved generated Lo-Fi music to {WAV_OUTPUT} ({len(wav_bytes)} bytes)")

    dur = get_video_duration(VIDEO_INPUT)
    print(f"3. Video duration: {dur:.2f}s")
    
    fade_in = min(1.0, dur / 4)
    fade_out_dur = min(2.0, dur / 3)
    fade_out_start = max(0, dur - fade_out_dur)
    volume = 0.6
    af = f"afade=t=in:st=0:d={fade_in:.2f},afade=t=out:st={fade_out_start:.2f}:d={fade_out_dur:.2f},volume={volume}"

    mux_cmd = [
        "ffmpeg", "-y",
        "-i", VIDEO_INPUT,
        "-stream_loop", "-1",
        "-i", WAV_OUTPUT,
        "-filter:a", af,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-t", f"{dur:.3f}",
        "-c:v", "copy",
        "-c:a", "libopus",
        "-b:a", "128k",
        "-shortest",
        VIDEO_OUTPUT
    ]
    
    print("4. Muxing video and audio with ffmpeg...")
    subprocess.run(mux_cmd, check=True)
    
    # Also overwrite the primary demo webm so any submission points to the musical version
    subprocess.run(["cp", "-f", VIDEO_OUTPUT, VIDEO_INPUT], check=True)
    
    print(f"\nSUCCESS: Synced video with Lo-Fi background music saved to {VIDEO_INPUT} and {VIDEO_OUTPUT}")

if __name__ == "__main__":
    main()
