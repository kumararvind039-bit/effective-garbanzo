GSEB LearnMate — Final Version
A full-stack AI teaching agent for GSEB Class IX and X English-medium students. This rebuilt package includes a responsive website, Flask API, SQLite progress tracking, and an Expo mobile client.
Included
All core GSEB subject categories: English, Gujarati, Mathematics, Science, Social Science, Computer Studies.
Student authentication and demo account (`demo@gseb.edu` / `demo123`).
Text teaching queries, question history, and subject mastery progress.
Mobile-ready camera/microphone entry point for connecting OCR/transcription services.
Student feedback after every answer: helpful/not helpful, reason, and optional comment on web; one-tap feedback on mobile.
Teacher feedback summary API at `GET /api/feedback/summary` for teacher-role accounts.
Run the backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
The API runs on `http://localhost:5000`. Set `PORT` and `APP_SECRET` in production. Replace the deterministic teaching fallback in `teach()` with the approved OpenAI/GPT integration and add server-side OCR/Whisper processing before exposing it publicly.
Run the website
```bash
cd frontend
npm install
npm run dev
```
For a deployed API, set `VITE_API_URL=https://your-api.example.com/api` before `npm run build`.
Run the mobile app
```bash
cd gseb-teaching-agent-mobile
npx expo start
```
Edit `API` in `App.tsx` to the LAN or deployed backend URL. Install Expo Go on the phone and scan the QR code. Camera and microphone permissions should be added with `expo-camera` and `expo-av` when wiring the production multimodal handlers.
Feedback design
Each answer stores the user, question, subject, rating, helpful flag, reason, comment, feedback type, and timestamp. Keep student comments private, restrict teacher analytics by role, moderate free text, and collect only educationally necessary data because many users are minors.
Production checklist
Use HTTPS, a strong `APP_SECRET`, and PostgreSQL or managed SQLite storage.
Integrate GPT-4.1-mini/Vision/Whisper through server-side secrets only.
Add rate limiting, file-size limits, virus scanning, and consent-aware media retention.
Create a teacher account through a controlled admin process; never allow public role escalation.
Build the web app and serve `frontend/dist` behind a reverse proxy.
