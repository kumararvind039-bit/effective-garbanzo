import os, sqlite3, hashlib, secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g
from flask_cors import CORS

app = Flask(__name__); CORS(app)
DB = os.path.join(os.path.dirname(__file__), 'gseb.db')
SUBJECTS = {g: ['English','Gujarati','Mathematics','Science','Social Science','Computer Studies'] for g in ('Class IX','Class X')}

def db():
    if 'db' not in g: g.db = sqlite3.connect(DB)
    g.db.row_factory = sqlite3.Row; return g.db
@app.teardown_appcontext
def close(_):
    x=g.pop('db',None)
    if x: x.close()
def init_db():
    x=sqlite3.connect(DB); x.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,grade TEXT NOT NULL DEFAULT 'Class IX',role TEXT NOT NULL DEFAULT 'student'); CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER,expires_at TEXT); CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY,user_id INTEGER,subject TEXT,prompt TEXT,answer TEXT,input_type TEXT,created_at TEXT); CREATE TABLE IF NOT EXISTS progress(id INTEGER PRIMARY KEY,user_id INTEGER,subject TEXT,minutes INTEGER DEFAULT 0,questions INTEGER DEFAULT 0,mastery INTEGER DEFAULT 0,UNIQUE(user_id,subject)); CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY,user_id INTEGER,question_id INTEGER,subject TEXT,helpful INTEGER,rating INTEGER,reason TEXT,comment TEXT,feedback_type TEXT DEFAULT 'answer',created_at TEXT);''')
    if not x.execute('SELECT 1 FROM users WHERE email=?',('demo@gseb.edu',)).fetchone(): x.execute('INSERT INTO users(name,email,password,grade) VALUES(?,?,?,?)',('Demo Student','demo@gseb.edu',hashlib.sha256(b'demo123').hexdigest(),'Class IX'))
    x.commit(); x.close()
def current():
    t=request.headers.get('Authorization','').replace('Bearer ',''); return db().execute('SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=? AND s.expires_at>?',(t,datetime.utcnow().isoformat())).fetchone()
def teach(prompt,subject): return f"Let's learn this step by step for GSEB {subject}.\n\n1. Identify the key idea in the question.\n2. Connect it to the rule or example from your textbook.\n3. Explain it in your own words.\n\nQuestion received: {prompt}\n\nWould you like a simpler explanation, an example, or a practice question?"
@app.get('/api/health')
def health(): return jsonify(status='ok',service='GSEB AI Teaching Agent')
@app.post('/api/auth/login')
def login():
    d=request.json or {}; pw=hashlib.sha256((d.get('password') or '').encode()).hexdigest(); u=db().execute('SELECT * FROM users WHERE email=? AND password=?',(d.get('email','').lower(),pw)).fetchone()
    if not u: return jsonify(error='Invalid email or password'),401
    t=secrets.token_urlsafe(32); db().execute('INSERT INTO sessions VALUES(?,?,?)',(t,u['id'],(datetime.utcnow()+timedelta(days=7)).isoformat())); db().commit(); return jsonify(token=t,user=dict(u))
@app.post('/api/auth/register')
def register():
    d=request.json or {}; email=d.get('email','').lower(); pw=d.get('password','')
    if not email or len(pw)<6: return jsonify(error='Use a valid email and a password of at least 6 characters'),400
    try: db().execute('INSERT INTO users(name,email,password,grade) VALUES(?,?,?,?)',(d.get('name','Student'),email,hashlib.sha256(pw.encode()).hexdigest(),d.get('grade','Class IX'))); db().commit()
    except sqlite3.IntegrityError: return jsonify(error='An account with this email already exists'),409
    return login()
@app.get('/api/subjects')
def subjects():
    u=current(); return jsonify(grade=u['grade'] if u else 'Class IX',subjects=SUBJECTS['Class IX'])
@app.post('/api/ask')
def ask():
    u=current(); d=request.json or {}
    if not u: return jsonify(error='Unauthorized'),401
    p=d.get('prompt','').strip(); s=d.get('subject','English')
    if not p: return jsonify(error='Please enter a question'),400
    a=teach(p,s); now=datetime.utcnow().isoformat(); x=db(); q=x.execute('INSERT INTO questions(user_id,subject,prompt,answer,input_type,created_at) VALUES(?,?,?,?,?,?)',(u['id'],s,p,a,d.get('input_type','text'),now)).lastrowid; x.execute('INSERT INTO progress(user_id,subject,questions,mastery) VALUES(?,?,1,10) ON CONFLICT(user_id,subject) DO UPDATE SET questions=questions+1,mastery=MIN(100,mastery+2)',(u['id'],s)); x.commit(); return jsonify(question_id=q,answer=a,subject=s,created_at=now)
@app.get('/api/history')
def history():
    u=current(); return jsonify(items=[dict(x) for x in db().execute('SELECT * FROM questions WHERE user_id=? ORDER BY id DESC LIMIT 30',(u['id'],))]) if u else (jsonify(error='Unauthorized'),401)
@app.get('/api/progress')
def progress():
    u=current(); return jsonify(items=[dict(x) for x in db().execute('SELECT subject,minutes,questions,mastery FROM progress WHERE user_id=? ORDER BY subject',(u['id'],))]) if u else (jsonify(error='Unauthorized'),401)
@app.post('/api/feedback')
def feedback():
    u=current(); d=request.json or {}
    if not u: return jsonify(error='Unauthorized'),401
    if d.get('helpful') is None and d.get('rating') is None: return jsonify(error='Choose a rating'),400
    db().execute('INSERT INTO feedback(user_id,question_id,subject,helpful,rating,reason,comment,feedback_type,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(u['id'],d.get('question_id'),d.get('subject',''),d.get('helpful'),d.get('rating'),d.get('reason',''),d.get('comment','')[:2000],d.get('feedback_type','answer'),datetime.utcnow().isoformat())); db().commit(); return jsonify(message='Thank you — your feedback helps improve the teaching agent.')
@app.get('/api/feedback/summary')
def summary():
    u=current()
    if not u or u['role']!='teacher': return jsonify(error='Teacher access required'),403
    t=db().execute('SELECT COUNT(*) total,ROUND(AVG(rating),1) average_rating,SUM(CASE WHEN helpful=1 THEN 1 ELSE 0 END) helpful FROM feedback').fetchone(); r=db().execute('SELECT reason,COUNT(*) count FROM feedback WHERE reason<>"" GROUP BY reason ORDER BY count DESC').fetchall(); return jsonify(total=dict(t),reasons=[dict(x) for x in r])
if __name__=='__main__': init_db(); app.run(host='0.0.0.0',port=int(os.getenv('PORT',5000)))
