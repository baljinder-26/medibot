import React, { useState, useEffect, useRef } from 'react';
import './index.css';
import './auth.css';

// --- Particle Canvas Background ---
const ParticleCanvas = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H;
    let pts = [];
    let animationFrameId;

    const resizeC = () => {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    };
    resizeC();
    window.addEventListener('resize', resizeC);

    for (let i = 0; i < 70; i++) {
      pts.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        r: Math.random() * 1.5 + 0.3,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        a: Math.random() * 0.5 + 0.1
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      pts.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = W;
        if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H;
        if (p.y > H) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,229,195,${p.a})`;
        ctx.fill();
      });
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const dx = pts[i].x - pts[j].x;
          const dy = pts[i].y - pts[j].y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < 120) {
            ctx.beginPath();
            ctx.moveTo(pts[i].x, pts[i].y);
            ctx.lineTo(pts[j].x, pts[j].y);
            ctx.strokeStyle = `rgba(0,229,195,${0.06 * (1 - d / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      animationFrameId = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      window.removeEventListener('resize', resizeC);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas id="particleCanvas" ref={canvasRef}></canvas>;
};

// --- Typewriter Hook ---
const useTypewriter = (phrases) => {
  const [text, setText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [loopNum, setLoopNum] = useState(0);

  useEffect(() => {
    let timer;
    const i = loopNum % phrases.length;
    const fullText = phrases[i];

    if (isDeleting) {
      timer = setTimeout(() => {
        setText(fullText.substring(0, text.length - 1));
      }, 60);
    } else {
      timer = setTimeout(() => {
        setText(fullText.substring(0, text.length + 1));
      }, 90);
    }

    if (!isDeleting && text === fullText) {
      timer = setTimeout(() => setIsDeleting(true), 1800);
    } else if (isDeleting && text === '') {
      setIsDeleting(false);
      setLoopNum(loopNum + 1);
    }

    return () => clearTimeout(timer);
  }, [text, isDeleting, loopNum, phrases]);

  return text;
};


// --- Main App Component ---
function App() {
  const [view, setView] = useState(() => {
    return localStorage.getItem('current_user') ? 'chat' : 'landing';
  });
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const messageRefs = useRef({});

  // Auth State
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('current_user');
    return saved ? JSON.parse(saved) : null;
  });

  // Sessions State (History)
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem('current_user');
    if (saved) {
      const user = JSON.parse(saved);
      if (user.sessions && user.sessions.length > 0) return user.sessions;
    }
    return [{ id: Date.now(), title: 'New Chat', messages: [] }];
  });
  const [activeSessionId, setActiveSessionId] = useState(sessions[0]?.id || Date.now());

  useEffect(() => {
    if (currentUser) {
      localStorage.setItem('current_user', JSON.stringify({ ...currentUser, sessions }));
    } else {
      localStorage.removeItem('current_user');
    }
  }, [currentUser, sessions]);

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];
  const messages = activeSession ? activeSession.messages : [];

  // Image Upload State
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('signin'); // 'signin' or 'signup'
  
  // Auth Form State
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [authError, setAuthError] = useState('');

  // Settings State
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [settingsHeight, setSettingsHeight] = useState('');
  const [settingsWeight, setSettingsWeight] = useState('');
  const [settingsPassword, setSettingsPassword] = useState('');
  const [settingsError, setSettingsError] = useState('');
  const [settingsSuccess, setSettingsSuccess] = useState('');

  // Search State
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // News State
  const [newsArticles, setNewsArticles] = useState([]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const apiKey = "pub_74551e2bc10e8dbb67f21267233ae6a9dd800";
        const url = `https://newsdata.io/api/1/news?apikey=${apiKey}&category=health&language=en`;
        const res = await fetch(url);
        const data = await res.json();
        if (data.status === "success" && data.results) {
          setNewsArticles(data.results.slice(0, 3)); // Display top 3 news articles
        }
      } catch (err) {
        console.error("Failed to fetch news", err);
      } finally {
        setNewsLoading(false);
      }
    };
    fetchNews();
  }, []);

  const typeTarget = useTypewriter(['millions', '5 lakh+', 'thousands', 'vast volumes']);

  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (!showSearch || !searchQuery) {
      scrollToBottom();
    }
  }, [messages, isTyping, showSearch, searchQuery]);

  // Scroll to search match
  useEffect(() => {
    if (showSearch && searchQuery) {
      const index = messages.findIndex(m => m.content && m.content.toLowerCase().includes(searchQuery.toLowerCase()));
      if (index !== -1 && messageRefs.current[index]) {
        messageRefs.current[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [searchQuery, showSearch, messages]);

  const highlightText = (text, highlight) => {
    if (!text) return '';
    const safeText = text.replace(/\n/g, '<br/>');
    if (!highlight.trim() || !showSearch) return safeText;
    
    try {
      const regex = new RegExp(`(${highlight})`, 'gi');
      return safeText.replace(regex, '<mark style="background: rgba(0,229,195,0.4); color: white; padding: 0 2px; border-radius: 3px;">$1</mark>');
    } catch(e) {
      return safeText;
    }
  };

  const handleLandingAction = (mode) => {
    if (currentUser) {
      setView('chat');
    } else {
      openAuthModal(mode);
    }
  };

  const openAuthModal = (mode = 'signin') => {
    setAuthMode(mode);
    setShowAuthModal(true);
    setAuthError('');
    setUsername('');
    setEmail('');
    setPassword('');
    setHeight('');
    setWeight('');
  };

  const playGreeting = (name) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(`Welcome, ${name}. I am MediRap AI, your assistant.`);
      window.speechSynthesis.speak(utterance);
    }
  };

  const closeAuthModal = () => setShowAuthModal(false);

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');

    if (authMode === 'signup') {
      if (!email || !password || !username) {
        setAuthError('Please fill in email, username and password.');
        return;
      }
      
      const h = height ? parseFloat(height) : null;
      const w = weight ? parseFloat(weight) : null;
      let bmi = 'N/A';
      if (h && w) {
        const hMeters = h / 100;
        bmi = (w / (hMeters * hMeters)).toFixed(1);
      }

      const newUserPayload = {
        username,
        email,
        password,
        height: h ? String(h) : 'N/A',
        weight: w ? String(w) : 'N/A',
        bmi: String(bmi)
      };

      try {
        const res = await fetch(`${BACKEND_URL}/auth/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newUserPayload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Signup failed');
        
        setCurrentUser(data.user);
        setSessions(data.user.sessions || [{ id: Date.now(), title: 'New Chat', messages: [] }]);
        setActiveSessionId(data.user.sessions?.[0]?.id || Date.now());
        closeAuthModal();
        setView('chat');
        playGreeting(data.user.username);
      } catch (err) {
        setAuthError(err.message);
      }
    } else {
      // Sign In
      if (!email || !password) {
        setAuthError('Please fill in both email and password.');
        return;
      }
      try {
        const res = await fetch(`${BACKEND_URL}/auth/signin`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Signin failed');
        
        setCurrentUser(data.user);
        const userSessions = data.user.sessions && data.user.sessions.length > 0 ? data.user.sessions : [{ id: Date.now(), title: 'New Chat', messages: [] }];
        setSessions(userSessions);
        setActiveSessionId(userSessions[0].id);
        closeAuthModal();
        setView('chat');
        playGreeting(data.user.username);
      } catch (err) {
        setAuthError(err.message);
      }
    }
  };

  const handleSignOut = () => {
    setCurrentUser(null);
    setSessions([{ id: Date.now(), title: 'New Chat', messages: [] }]);
    setActiveSessionId(Date.now());
    setView('landing');
  };

  const openSettingsModal = () => {
    if (currentUser) {
      setSettingsHeight(currentUser.height === 'N/A' ? '' : currentUser.height);
      setSettingsWeight(currentUser.weight === 'N/A' ? '' : currentUser.weight);
      setSettingsPassword('');
      setSettingsError('');
      setSettingsSuccess('');
      setShowSettingsModal(true);
    }
  };

  const handleSettingsSubmit = async (e) => {
    e.preventDefault();
    setSettingsError('');
    setSettingsSuccess('');

    if (!currentUser) return;

    const payload = { email: currentUser.email };
    if (settingsPassword) payload.password = settingsPassword;
    if (settingsHeight) payload.height = String(parseFloat(settingsHeight));
    if (settingsWeight) payload.weight = String(parseFloat(settingsWeight));

    let updatedBmi = currentUser.bmi;
    if (payload.height && payload.weight) {
        const hMeters = parseFloat(payload.height) / 100;
        updatedBmi = (parseFloat(payload.weight) / (hMeters * hMeters)).toFixed(1);
        payload.bmi = updatedBmi;
    }

    try {
      const res = await fetch(`${BACKEND_URL}/auth/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Update failed');
      
      setCurrentUser(data.user);
      setSettingsSuccess('Settings updated successfully!');
      setTimeout(() => {
        setShowSettingsModal(false);
      }, 1500);
    } catch (err) {
      setSettingsError(err.message);
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      const url = URL.createObjectURL(file);
      setImagePreview(url);
    }
  };

  const removeImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if(fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleNewChat = () => {
    const newSession = { id: Date.now(), title: 'New Chat', messages: [] };
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
  };

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() && !imagePreview) return;

    const userMsg = { 
      role: 'user', 
      content: text, 
      userImage: imagePreview,
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) 
    };
    
    // Update active session locally
    let updatedSessions = [...sessions];
    let sIndex = updatedSessions.findIndex(s => s.id === activeSessionId);
    if (sIndex === -1) return;

    let currentSession = updatedSessions[sIndex];
    const isFirstMsg = currentSession.messages.length === 0;
    const newTitle = isFirstMsg ? (text.length > 20 ? text.substring(0,20)+'...' : text) : currentSession.title;
    
    const newMessages = [...currentSession.messages, userMsg];
    updatedSessions[sIndex] = { ...currentSession, title: newTitle || 'Photo Upload', messages: newMessages };
    
    setSessions(updatedSessions);
    if (currentUser) {
      fetch(`${BACKEND_URL}/auth/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: currentUser.email, sessions: updatedSessions })
      }).catch(e => console.error("Auto-save failed", e));
    }
    setInput('');
    removeImage();
    setIsTyping(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: text || "Please analyze this image." })
      });

      if (!res.ok) throw new Error("Failed to fetch response");

      const data = await res.json();
      
      const aiMsg = { 
        role: 'ai', 
        content: data.answer, 
        pages: data.pages,
        image: data.image,
        time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) 
      };
      
      updatedSessions = [...updatedSessions];
      sIndex = updatedSessions.findIndex(s => s.id === activeSessionId);
      updatedSessions[sIndex] = { ...updatedSessions[sIndex], messages: [...updatedSessions[sIndex].messages, aiMsg] };
      
      setSessions(updatedSessions);

      // Save to dummy DB automatically
      if (currentUser) {
        fetch(`${BACKEND_URL}/auth/update`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: currentUser.email, sessions: updatedSessions })
        }).catch(e => console.error("Auto-save failed", e));
      }
    } catch (err) {
      const errMsg = {
        role: 'ai',
        content: "I am having trouble connecting to the backend. Please ensure the server is running and the database connection is healthy.",
        time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
      };
      updatedSessions = [...updatedSessions];
      sIndex = updatedSessions.findIndex(s => s.id === activeSessionId);
      updatedSessions[sIndex] = { ...updatedSessions[sIndex], messages: [...updatedSessions[sIndex].messages, errMsg] };
      setSessions(updatedSessions);
      if (currentUser) {
        fetch(`${BACKEND_URL}/auth/update`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: currentUser.email, sessions: updatedSessions })
        }).catch(e => console.error("Auto-save failed", e));
      }
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickSend = (topic) => {
    const text = topic.replace(/^[\u1000-\uFFFF]+\s/, '').trim(); // strip emoji if any
    handleSend(text);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleMicClick = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    
    recognition.onstart = () => {
      setIsRecording(true);
    };
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(prev => prev + (prev ? ' ' : '') + transcript);
    };
    
    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
      setIsRecording(false);
    };
    
    recognition.onend = () => {
      setIsRecording(false);
    };
    
    recognition.start();
  };

  const getBmiStatusClass = (bmi) => {
    if (!bmi || bmi === 'N/A') return '';
    const b = parseFloat(bmi);
    if (b < 18.5) return 'warn';
    if (b >= 18.5 && b < 25) return 'good';
    if (b >= 25 && b < 30) return 'warn';
    return 'warn'; // obese
  };

  return (
    <>
      <div className="glow-line"></div>
      <div className="grid-bg"></div>
      <ParticleCanvas />

      {/* AUTH MODAL */}
      {showAuthModal && (
        <div className="modal-overlay" onClick={closeAuthModal}>
          <div className="auth-modal" onClick={e => e.stopPropagation()}>
            <button className="auth-close" onClick={closeAuthModal}>&times;</button>
            <div className="auth-header">
              <h2>Medi<span>Rap</span> AI</h2>
              <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>Secure access to clinical intelligence</p>
            </div>
            
            <div className="auth-tabs">
              <button className={`auth-tab ${authMode === 'signin' ? 'active' : ''}`} onClick={() => setAuthMode('signin')}>Sign In</button>
              <button className={`auth-tab ${authMode === 'signup' ? 'active' : ''}`} onClick={() => setAuthMode('signup')}>Sign Up</button>
            </div>

            <form className="auth-form" onSubmit={handleAuthSubmit}>
              {authMode === 'signup' && (
                <div className="auth-input-group">
                  <label className="auth-label">Username</label>
                  <input type="text" className="auth-input" value={username} onChange={e => setUsername(e.target.value)} placeholder="Enter your username" required />
                </div>
              )}
              <div className="auth-input-group">
                <label className="auth-label">Email</label>
                <input type="email" className="auth-input" value={email} onChange={e => setEmail(e.target.value)} placeholder="Enter your email" required />
              </div>
              <div className="auth-input-group">
                <label className="auth-label">Password</label>
                <input type="password" className="auth-input" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter your password" required />
              </div>
              
              {authMode === 'signup' && (
                <div className="grid-2">
                  <div className="auth-input-group">
                    <label className="auth-label">Height (cm) - Optional</label>
                    <input type="number" className="auth-input" value={height} onChange={e => setHeight(e.target.value)} placeholder="e.g. 175" />
                  </div>
                  <div className="auth-input-group">
                    <label className="auth-label">Weight (kg) - Optional</label>
                    <input type="number" className="auth-input" value={weight} onChange={e => setWeight(e.target.value)} placeholder="e.g. 70" />
                  </div>
                </div>
              )}

              {authError && <div className="auth-error">{authError}</div>}
              
              <button type="submit" className="auth-submit">
                {authMode === 'signin' ? 'Access Workspace' : 'Create Profile'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* SETTINGS MODAL */}
      {showSettingsModal && (
        <div className="modal-overlay" onClick={() => setShowSettingsModal(false)}>
          <div className="auth-modal" onClick={e => e.stopPropagation()}>
            <button className="auth-close" onClick={() => setShowSettingsModal(false)}>&times;</button>
            <div className="auth-header">
              <h2>User <span>Settings</span></h2>
              <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>Update your health profile and security</p>
            </div>

            <form className="auth-form" onSubmit={handleSettingsSubmit}>
              <div className="grid-2">
                <div className="auth-input-group">
                  <label className="auth-label">Height (cm)</label>
                  <input type="number" className="auth-input" value={settingsHeight} onChange={e => setSettingsHeight(e.target.value)} placeholder="e.g. 175" />
                </div>
                <div className="auth-input-group">
                  <label className="auth-label">Weight (kg)</label>
                  <input type="number" className="auth-input" value={settingsWeight} onChange={e => setSettingsWeight(e.target.value)} placeholder="e.g. 70" />
                </div>
              </div>
              
              <div className="auth-input-group" style={{marginTop: '10px'}}>
                <label className="auth-label">New Password</label>
                <input type="password" className="auth-input" value={settingsPassword} onChange={e => setSettingsPassword(e.target.value)} placeholder="Leave blank to keep current" />
              </div>

              {settingsError && <div className="auth-error">{settingsError}</div>}
              {settingsSuccess && <div style={{color: '#22c55e', fontSize: '0.85rem', textAlign: 'center', marginTop: '10px'}}>{settingsSuccess}</div>}
              
              <button type="submit" className="auth-submit" style={{marginTop: '20px'}}>
                Save Changes
              </button>
            </form>
          </div>
        </div>
      )}

      {/* LANDING PAGE */}
      <div id="landingPage" className={`page ${view === 'landing' ? 'visible' : 'hidden'}`}>
        <nav>
          <div className="nav-logo">
            <div className="nav-logo-icon">🧬</div>
            Medi<span>Rap</span> AI
          </div>
          <ul className="nav-links">
            <li><a href="#about">About</a></li>
            <li><a href="#features">Features</a></li>
            <li><a href="#capabilities">Capabilities</a></li>
          </ul>
          <div style={{display: 'flex', gap: '12px'}}>
            {!currentUser && (
              <button className="btn-ghost" style={{padding: '10px'}} onClick={() => handleLandingAction('signin')}>Sign In</button>
            )}
            <button className="nav-cta" onClick={() => handleLandingAction('signup')}>
              {currentUser ? 'Go to Chat' : 'Get Early Access'}
            </button>
          </div>
        </nav>

        <section className="hero">
          <div className="hero-left">
            <div className="badge fade-up d1">
              <span className="badge-dot"></span>
              Next-Gen Medical Intelligence
            </div>
            <h1 className="hero-title fade-up d2">
              Your AI Doctor,<br/>
              <span className="accent">Smarter</span> than<br/>
              <span className="accent2">Yesterday.</span>
            </h1>
            <p className="hero-sub fade-up d3">
              MediRap AI is an advanced clinical intelligence companion — trained on <span id="typeTarget">{typeTarget}</span><span className="type-cursor"></span> of medical journals to diagnose, advise, and guide your health with precision and calm.
            </p>
            <div className="hero-actions fade-up d4">
              <button className="btn-primary" onClick={() => handleLandingAction('signup')}>
                {currentUser ? 'Resume Diagnosis' : 'Start Diagnosis'}
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              <button className="btn-ghost">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5"/>
                  <path d="M10 8l6 4-6 4V8z" fill="currentColor"/>
                </svg>
                See how it works
              </button>
            </div>
            <div className="stats-row fade-up d5">
              <div className="stat-item"><div className="stat-num">98.4%</div><div className="stat-label">Diagnostic Accuracy</div></div>
              <div className="stat-item"><div className="stat-num">5L+</div><div className="stat-label">Medical Records Trained</div></div>
              <div className="stat-item"><div className="stat-num">24/7</div><div className="stat-label">Always Available</div></div>
            </div>
          </div>

          <div className="hero-right fade-up d3">
            <div className="orb-wrap">
              <div className="orb-ring"></div><div className="orb-ring"></div><div className="orb-ring"></div>
              <div className="pulse-ring"></div><div className="pulse-ring"></div><div className="pulse-ring"></div>
              <div className="orb-core">
                <div className="orb-icon">🧬</div>
                <div className="orb-label">MediRap AI</div>
              </div>
              <div className="float-card top-left">
                <div className="fc-title"><span className="fc-dot">●</span> Diagnosis Ready</div>
                <div className="fc-sub">Analyzing symptoms…</div>
              </div>
              <div className="float-card bottom-right">
                <div className="fc-title">💊 Treatment Plan</div>
                <div className="fc-sub">Personalized for you</div>
              </div>
              <div className="float-card mid-right">
                <div className="fc-title">🛡️ Verified Sources</div>
                <div className="fc-sub">WHO · PubMed · NIH</div>
              </div>
            </div>
          </div>

          <div className="scroll-hint">Discover<div className="scroll-arrow"></div></div>
        </section>

        {/* Other Landing Page Sections */}
        <section className="section" id="about">
          <div className="about-grid">
            <div>
              <div className="section-tag">The Vision</div>
              <h2 className="section-title">Built for <span className="hi">modern</span><br/>healthcare.</h2>
              <div className="divider"></div>
              <p className="about-text">MediRap AI is built to make clinical-grade intelligence accessible to everyone. We believe <strong>medical knowledge</strong> should not be locked behind waiting rooms and long queues.</p>
              <p className="about-text">Our platform draws from a <strong>vast corpus of medical literature</strong>, clinical trials, and expert guidelines — distilled into a calm, clear, and reliable conversational experience.</p>
              <div className="about-chips">
                <div className="chip">Evidence-Based</div>
                <div className="chip">HIPAA Aware</div>
                <div className="chip">Clinically Verified</div>
                <div className="chip">Private & Secure</div>
              </div>
            </div>
            <div className="feature-stack" id="features">
              <div className="feature-card">
                <div className="feature-icon">🔬</div>
                <div><h4>Clinical Intelligence</h4><p>Powered by peer-reviewed medical journals and real clinical data for accurate, contextual answers.</p></div>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🤝</div>
                <div><h4>Empathetic Conversations</h4><p>A calm, meditative tone that reassures patients — not a cold, robotic response engine.</p></div>
              </div>
              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <div><h4>Instant, Always On</h4><p>No appointments, no waiting. MediRap AI is available the moment you need medical clarity.</p></div>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="capabilities">
          <div className="section-tag">What It Does</div>
          <h2 className="section-title">Core <span className="hi">Capabilities</span></h2>
          <div className="caps-grid">
            <div className="cap-card"><div className="cap-num">01</div><div className="cap-icon">🩺</div><h3>Symptom Analysis</h3><p>Describe your symptoms in plain language. MediRap evaluates them against thousands of conditions and returns a clear, prioritized assessment.</p></div>
            <div className="cap-card"><div className="cap-num">02</div><div className="cap-icon">💊</div><h3>Drug Information</h3><p>Look up medications, interactions, dosages, and side effects — sourced directly from pharmacological databases and clinical guidelines.</p></div>
            <div className="cap-card"><div className="cap-num">03</div><div className="cap-icon">📋</div><h3>Treatment Pathways</h3><p>Receive personalized treatment suggestions aligned with WHO and NIH best practices — presented in plain, actionable language.</p></div>
            <div className="cap-card"><div className="cap-num">04</div><div className="cap-icon">🧠</div><h3>Mental Health Support</h3><p>A compassionate space for mental wellness guidance — mood tracking, coping strategies, and referral pathways built in.</p></div>
            <div className="cap-card"><div className="cap-num">05</div><div className="cap-icon">📊</div><h3>Lab Report Interpreter</h3><p>Upload your lab results and get a clear, jargon-free explanation of what each value means for your health.</p></div>
            <div className="cap-card"><div className="cap-num">06</div><div className="cap-icon">💬</div><h3>Chat Assistance</h3><p>Talk to MediRap AI anytime — ask follow-up questions, clarify doubts, and get real-time conversational support for all your health concerns.</p></div>
          </div>
        </section>

        <div className="cta-section">
          <h2>Ready to meet your <span style={{color: 'var(--teal)'}}>AI doctor?</span></h2>
          <p>Join thousands of patients and healthcare professionals who trust MediRap AI for clarity, speed, and precision.</p>
          <button className="btn-primary" onClick={() => handleLandingAction('signup')}>
            Begin Your Treatment Plan
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </button>
        </div>

        <footer>
          <div className="footer-logo">Medi<span>Rap</span> AI</div>
          <p>© 2026 MEDIRAP AI — CLINICAL INTELLIGENCE</p>
          <p>Intelligent Health, Always On</p>
        </footer>
      </div>

      {/* CHAT PAGE */}
      <div id="chatPage" className={`page ${view === 'chat' ? 'visible' : 'hidden'}`}>
        <div className="chat-nav">
          <div className="chat-nav-left">
            <button className="back-btn" onClick={() => setView('landing')} title="Back to Home">←</button>
            <button className="hamburger-btn" onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}>☰</button>
            <div className="chat-brand">
              <div className="chat-brand-icon">🧬</div>
              <div>
                <div className="chat-brand-name">Medi<span>Rap</span> AI</div>
                <div className="chat-status"><span className="status-dot"></span> Online · Clinical Intelligence</div>
              </div>
            </div>
          </div>
          <div className="chat-nav-right" style={{ position: 'relative' }}>
            <span style={{ color: 'var(--teal)', fontSize: '0.85rem', marginRight: '10px' }}>
              Welcome, {currentUser?.username}
            </span>
            <button className="nav-icon-btn" title="Search Chat" onClick={() => setShowSearch(!showSearch)}>
              🔍
            </button>
            <button className="nav-icon-btn" title="Live Vitals" onClick={() => window.location.href = '/vitals-dashboard.html'}>
              ❤️
            </button>
            <button className="nav-icon-btn" title="Settings" onClick={openSettingsModal}>
              ⚙️
            </button>
            <button className="nav-icon-btn" title="Sign Out" onClick={handleSignOut}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
            </button>
          </div>
        </div>

        {/* SEARCH BAR DROPDOWN */}
        {showSearch && (
          <div style={{
            position: 'absolute', top: '64px', right: '0', width: '100%', zIndex: 9,
            background: 'rgba(9,14,22,0.95)', borderBottom: '1px solid var(--border)', padding: '12px 28px',
            display: 'flex', justifyContent: 'flex-end'
          }}>
            <input 
              type="text" 
              placeholder="Highlight text in current chat..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'rgba(15,22,32,0.9)', border: '1px solid var(--teal)', borderRadius: '8px', 
                padding: '8px 16px', color: 'var(--white)', outline: 'none', width: '300px'
              }}
              autoFocus
            />
          </div>
        )}

        <div className="chat-body">
          {isMobileSidebarOpen && <div className="sidebar-overlay" onClick={() => setIsMobileSidebarOpen(false)}></div>}
          <div className={`chat-sidebar ${isMobileSidebarOpen ? 'open' : ''}`} style={{ padding: 0, gap: 0, overflow: 'hidden' }}>
            <div style={{ padding: '20px 16px 8px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button className="new-chat-btn" onClick={() => { handleNewChat(); setIsMobileSidebarOpen(false); }}>
                <span>✏️</span> New Chat
              </button>
              <div className="sidebar-label">Recent Chats</div>
            </div>
            
            <div style={{ flex: 1, overflowY: 'auto', padding: '0 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {sessions.map(s => (
                <div 
                  key={s.id} 
                  className={`chat-history-item ${activeSessionId === s.id ? 'active' : ''}`}
                  onClick={() => { setActiveSessionId(s.id); setIsMobileSidebarOpen(false); }}
                >
                  <span className="chi-icon">💬</span>
                  <span className="chi-text">{s.title || 'New Chat'}</span>
                </div>
              ))}
            </div>
            
            <div style={{ padding: '16px', flexShrink: 0, borderTop: '1px solid var(--border)', background: 'rgba(9,14,22,0.95)' }}>
              <button 
                className="fitness-btn" 
                onClick={() => window.location.href = '/vitals-dashboard.html'}
                style={{ width: '100%', justifyContent: 'center' }}
              >
                <span className="fb-icon">🏃‍♂️</span> Track Your Fitness
              </button>
            </div>
          </div>

          <div className="chat-main">
            <div className="messages-area" id="messagesArea" style={{ paddingTop: showSearch ? '70px' : '32px' }}>
              {messages.length === 0 ? (
                <div className="welcome-screen">
                  <div className="welcome-orb">🧬</div>
                  <h2>Hello, {currentUser?.username}! I'm <span>MediRap AI</span></h2>
                  <p>Your intelligent medical companion. Ask me anything about symptoms, medications, health conditions, or general wellness advice.</p>
                  <div className="quick-pills">
                    <div className="quick-pill" onClick={() => handleQuickSend("🤒 I have a fever and headache")}>🤒 I have a fever and headache</div>
                    <div className="quick-pill" onClick={() => handleQuickSend("💊 Is it safe to mix ibuprofen?")}>💊 Is it safe to mix ibuprofen?</div>
                    <div className="quick-pill" onClick={() => handleQuickSend("❤️ How to lower blood pressure?")}>❤️ How to lower blood pressure?</div>
                    <div className="quick-pill" onClick={() => handleQuickSend("📋 Explain my CBC report")}>📋 Explain my CBC report</div>
                    <div className="quick-pill" onClick={() => handleQuickSend("😴 Tips for better sleep")}>😴 Tips for better sleep</div>
                  </div>
                </div>
              ) : (
                messages.map((m, i) => (
                  <div key={i} className={`msg ${m.role}`} ref={el => messageRefs.current[i] = el}>
                    <div className="msg-avatar">{m.role === 'user' ? '👤' : '🧬'}</div>
                    <div className="msg-content">
                      <div className="msg-name">{m.role === 'user' ? (currentUser?.username || 'You') : 'MediRap AI'}</div>
                      
                      {m.userImage && m.role === 'user' && (
                        <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'flex-start' }}>
                          <img src={m.userImage} alt="User Upload" style={{ maxWidth: '250px', borderRadius: '12px', border: '1px solid rgba(0,229,195,0.3)', boxShadow: '0 4px 12px rgba(0,0,0,0.2)' }} />
                        </div>
                      )}

                      <div className="msg-bubble" dangerouslySetInnerHTML={{ __html: highlightText(m.content, searchQuery) }}></div>
                      
                      {m.image && m.role === 'ai' && (
                        <div style={{ marginTop: '10px' }}>
                          <img src={`${BACKEND_URL}/${m.image}`} alt="Medical Reference" style={{ maxWidth: '100%', borderRadius: '8px', border: '1px solid var(--border)' }} />
                        </div>
                      )}
                      
                      {m.pages && m.pages.length > 0 && (
                        <div style={{ marginTop: '10px', fontSize: '0.8rem', color: 'var(--teal)', fontWeight: 'bold' }}>
                          📚 Sources: Page(s) {m.pages.join(', ')}
                        </div>
                      )}

                      <div className="msg-meta">
                        <span className="msg-time">{m.time}</span>
                        {m.role === 'ai' && (
                          <div className="msg-actions">
                            <button className="msg-action-btn" title="Copy">📋</button>
                            <button className="msg-action-btn" title="Like">👍</button>
                            <button className="msg-action-btn" title="Dislike">👎</button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
              {isTyping && (
                <div className="typing-indicator">
                  <div className="msg-avatar" style={{background: 'linear-gradient(135deg,var(--teal),var(--blue))', borderRadius: '10px', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>🧬</div>
                  <div className="typing-dots"><div className="typing-dot"></div><div className="typing-dot"></div><div className="typing-dot"></div></div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
              {imagePreview && (
                <div style={{ position: 'relative', display: 'inline-block', marginBottom: '12px', padding: '8px', background: 'rgba(15,22,32,0.9)', border: '1px solid var(--border)', borderRadius: '12px' }}>
                  <img src={imagePreview} alt="Preview" style={{ height: '60px', borderRadius: '6px' }} />
                  <button onClick={removeImage} style={{ position: 'absolute', top: '-6px', right: '-6px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '50%', width: '20px', height: '20px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px' }}>&times;</button>
                </div>
              )}
              <div className="disclaimer">⚠️ MediRap AI provides general information only. Always consult a licensed physician for medical decisions.</div>
              <div className="input-box">
                <input 
                  type="file" 
                  accept="image/*" 
                  ref={fileInputRef} 
                  style={{ display: 'none' }} 
                  onChange={handleImageChange} 
                />
                <button className="input-attach" title="Attach Image" onClick={() => fileInputRef.current.click()}>📎</button>
                <textarea 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Describe your symptoms or ask a health question…" 
                  rows="1" 
                  style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: 'var(--white)', fontFamily: 'DM Sans, sans-serif', fontSize: '0.95rem', resize: 'none', maxHeight: '140px' }}
                />
                <button 
                  className={`input-attach ${isRecording ? 'recording' : ''}`} 
                  title="Voice Input" 
                  onClick={handleMicClick}
                  style={{ 
                    color: isRecording ? '#ef4444' : 'inherit', 
                    background: 'none', 
                    border: 'none', 
                    cursor: 'pointer', 
                    fontSize: '1.2rem', 
                    width: '40px',
                    height: '40px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 0
                  }}
                >
                  🎙️
                </button>
                <button className="send-btn" onClick={() => handleSend()} disabled={isTyping || (!input.trim() && !imagePreview)}>➤</button>
              </div>
              <div className="input-tags">
                <span className="input-tag" onClick={() => setInput('🩺 Symptoms — ')}>🩺 Symptoms</span>
                <span className="input-tag" onClick={() => setInput('💊 Medications — ')}>💊 Medications</span>
                <span className="input-tag" onClick={() => setInput('🧪 Lab Results — ')}>🧪 Lab Results</span>
                <span className="input-tag" onClick={() => setInput('❤️ Heart Health — ')}>❤️ Heart Health</span>
              </div>
            </div>
          </div>

          <div className="chat-right-panel">
            {currentUser && (
              <div>
                <div className="panel-section-title">Patient Profile</div>
                <div className="health-card">
                  <div className="health-card-header">
                    <span className="health-card-icon">👤</span>
                    <span className="health-card-title">{currentUser.username}</span>
                  </div>
                  <div className="health-metric"><span className="hm-label">Height</span><span className="hm-val">{currentUser.height === 'N/A' ? '--' : `${currentUser.height} cm`}</span></div>
                  <div className="health-metric"><span className="hm-label">Weight</span><span className="hm-val">{currentUser.weight === 'N/A' ? '--' : `${currentUser.weight} kg`}</span></div>
                  <div className="health-metric">
                    <span className="hm-label">BMI</span>
                    <span className={`hm-val ${getBmiStatusClass(currentUser.bmi)}`}>{currentUser.bmi}</span>
                  </div>
                </div>
              </div>
            )}
            
            <div style={{marginTop: '24px', marginBottom: '24px'}}>
              <div className="panel-section-title">HEALTH NEWS</div>
              {newsLoading ? (
                <div className="health-card" style={{ textAlign: 'center', color: 'var(--muted)', padding: '20px' }}>
                  Loading latest news...
                </div>
              ) : newsArticles.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {newsArticles.map((article, idx) => {
                    const pubDateObj = new Date(article.pubDate);
                    const now = new Date();
                    const hoursAgo = Math.floor((now - pubDateObj) / (1000 * 60 * 60));
                    const timeDisplay = hoursAgo > 0 ? `${hoursAgo} hrs ago` : 'Just now';
                    
                    return (
                      <div key={idx} style={{ 
                        background: 'rgba(15,22,32,0.4)', 
                        border: '1px solid rgba(255,255,255,0.05)', 
                        borderRadius: '8px', 
                        padding: '16px',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = 'rgba(25,32,45,0.8)'; e.currentTarget.style.borderColor = 'rgba(0,229,195,0.3)'; }}
                      onMouseLeave={e => { e.currentTarget.style.background = 'rgba(15,22,32,0.4)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)'; }}
                      onClick={() => window.open(article.link, '_blank')}
                      >
                        <div style={{ 
                          display: 'inline-block', 
                          background: idx === 0 ? 'rgba(0, 229, 195, 0.1)' : idx === 1 ? 'rgba(139, 92, 246, 0.1)' : 'rgba(236, 72, 153, 0.1)', 
                          color: idx === 0 ? 'var(--teal)' : idx === 1 ? '#a78bfa' : '#f472b6', 
                          fontSize: '0.65rem', 
                          fontWeight: '700', 
                          letterSpacing: '0.5px', 
                          padding: '4px 8px', 
                          borderRadius: '4px', 
                          marginBottom: '10px', 
                          textTransform: 'uppercase' 
                        }}>
                          {article.category?.[0] || 'HEALTH'}
                        </div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--white)', fontWeight: '500', lineHeight: '1.4', marginBottom: '8px' }}>
                          {article.title}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)' }}>
                          {timeDisplay}
                        </div>
                      </div>
                    )
                  })}
                  <div style={{ textAlign: 'right', marginTop: '8px' }}>
                    <a href="https://newsdata.io" target="_blank" rel="noreferrer" style={{ color: 'var(--teal)', fontSize: '0.85rem', textDecoration: 'none', fontWeight: '500' }}>
                      View more news
                    </a>
                  </div>
                </div>
              ) : (
                 <div className="health-card" style={{ textAlign: 'center', color: 'var(--muted)', padding: '20px' }}>
                  No recent health news available.
                </div>
              )}
            </div>

            <div style={{marginTop: '20px'}}>
              <div className="panel-section-title">Health Snapshot</div>
              <div className="health-card">
                <div className="health-card-header">
                  <span className="health-card-icon">📊</span>
                  <span className="health-card-title">Quick Vitals</span>
                </div>
                <div className="health-metric"><span className="hm-label">Heart Rate</span><span className="hm-val good">72 bpm</span></div>
                <div className="health-metric"><span className="hm-label">Blood Pressure</span><span className="hm-val warn">130/85</span></div>
                <div className="health-metric"><span className="hm-label">Sleep</span><span className="hm-val warn">5.5 hrs</span></div>
              </div>
            </div>

            <div style={{marginTop: '20px'}}>
              <div className="panel-section-title">AI Sources</div>
              <div className="health-card">
                <div className="health-metric"><span className="hm-label">Encyclopedia</span><span className="hm-val good">✓ Connected</span></div>
                <div className="health-metric"><span className="hm-label">Backend API</span><span className="hm-val good">✓ Active</span></div>
                <div className="health-metric"><span className="hm-label">Model Engine</span><span className="hm-val">LLaMA 3.3 70B</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
