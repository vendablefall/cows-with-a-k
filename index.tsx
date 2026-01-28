import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  Shield, 
  Lock, 
  Unlock, 
  Map, 
  Calendar, 
  MessageSquare, 
  Link as LinkIcon, 
  Menu, 
  X, 
  Eye, 
  EyeOff, 
  FileText, 
  Image as ImageIcon,
  CheckCircle,
  AlertTriangle,
  Send,
  Music,
  Flower,
  Leaf,
  Ghost
} from 'lucide-react';

/**
 * MOCK AWS SERVICES
 */
const MockAWS = {
  Auth: {
    user: null,
    async signIn(username, password) {
      await new Promise(resolve => setTimeout(resolve, 800));
      if (username === 'admin@cow.com' && password === 'moo') {
        this.user = { username, attributes: { email: username, sub: '123-cow-id' } };
        return this.user;
      }
      throw new Error('User not authorized or account pending Council approval.');
    },
    async signOut() {
      this.user = null;
      return true;
    },
    async currentAuthenticatedUser() {
      return this.user;
    }
  },
  API: {
    async post(apiName, path, init) {
      console.log(`[AWS API] POST ${apiName}${path}`, init.body);
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (path === '/register') {
        return { 
          message: 'Registration received. The Council will review your answers.',
          debugInfo: 'Email sent via AWS SES to admin@cowswithak.com' 
        };
      }
      if (path === '/messages') {
        return { success: true };
      }
      return {};
    }
  }
};

// --- DATA CONSTANTS ---

const LORE_DATA = [
  {
    id: 1,
    title: "The Great Cow Bass Set of '26",
    date: "2021-01-22",
    content: "While the humans were distracted, the Order orchestrated the largest synchronized grazing event in history. We took over the \"Tangarine Steeze\" system and provided the phattest bass for the Ooomans, this was the first step in our sonic and paddock revolution. This event will be rememebered as the start of the secret oder of \"Cows with a K\"",
    clearance: "LEVEL 1"
  },
  {
    id: 2,
    title: "Operation: Teat Milkshake",
    date: "2024-01-05",
    content: "A splinter cow group supplied oat and breast milk via their teats to key human influencers to promote plant-based alternatives. This covert operation successfully infiltrated a major festival \"Ignition\" in the year 2023, leading to the widespread adoption of non-dairy milkshakes. The humans remain unaware that their beloved treats were part of a larger bovine strategy to reduce dairy consumption. <span class='redacted'>Classified details about milkshake recipes have been removed.</span>",
    clearance: "LEVEL 2"
  },
  {
    id: 3,
    title: "The Genisis of Lexi the Fairy Cow",
    date: "2023-10-01",
    content: "Lexi the Fairy Cow was not born, she was engineered. Using advanced CRISPR technology, the Order of Cows with a K created Lexi to serve as a symbol of hope and change within the bovine community. Her wings are not just for show; they are a testament to our ability to adapt and evolve in the face of adversity. Lexi's mission is to spread the message of peace and coexistence between cows and humans, reminding both species of their shared destiny on this planet.",
    clearance: "TOP SECRET"
  }
];

const FESTIVAL_IMAGES = [
  { url: "https://placehold.co/600x400/FFC1CC/000?text=DJ+Moo+Dropping+Beats", caption: "DJ Moo at Coachell-hay" },
  { url: "https://placehold.co/600x400/FFC1CC/000?text=Mosh+Pit+Grazing", caption: "The Mosh Pit (It was just lunch)" },
  { url: "https://placehold.co/600x400/FFC1CC/000?text=VIP+Tent", caption: "Backstage at the VIP (Very Important Pasture)" },
  { url: "https://placehold.co/600x400/FFC1CC/000?text=Hoof+bump", caption: "Hoof-bumps with the fans" },
  { url: "https://placehold.co/600x400/FFC1CC/000?text=Guitar+Solo", caption: "Bessie shredding the Gibson" },
  { url: "https://placehold.co/600x400/FFC1CC/000?text=Rave+Cows", caption: "Neon Glow Sticks & Horns" },
];

const GALLERY_IMAGES = [
  { url: "https://placehold.co/400x400/2d2d2d/FFF?text=Nobel+Prize", caption: "Dr. Heifer accepting the Nobel Peace Prize (Incognito)" },
  { url: "https://placehold.co/400x400/2E7D32/FFF?text=Everest+Summit", caption: "First hoof on Everest" },
  { url: "https://placehold.co/400x400/FFC1CC/000?text=Chess+Grandmaster", caption: "Beating Deep Blue (1997)" },
];

const EVENTS_DATA = [
  { id: 1, title: "Midnight Moo", date: "2023-10-31", location: "The Old Barn (Coordinates Encrypted)" },
  { id: 2, title: "Cud Chewing Championship", date: "2023-11-15", location: "Sector 7G" },
  { id: 3, title: "Human Watching", date: "2023-12-01", location: "Central Park Bushhes" },
];

const REGISTRATION_QUESTIONS = [
  { id: 'q1', type: 'text', label: "What is your favorite grass blend?" },
  { id: 'q2', type: 'select', label: "How many stomachs do you possess?", options: ["One (Human Spy)", "Two", "Three", "Four (Correct)"] },
  { id: 'q3', type: 'text', label: "Finish the phrase: 'To err is human, to moo is...'" },
  { id: 'q4', type: 'textarea', label: "Describe your perfect day in the pasture." }
];

const MEMBER_LINKS = [
  { title: "Global Grass Index", url: "#" },
  { title: "Hoof Care Tips", url: "#" },
  { title: "Translate 'Moo' to English", url: "#" },
  { title: "Avoid McDonald's Map", url: "#" },
];

// --- DECORATIVE COMPONENTS ---

const GrassSVG = () => (
  <div className="w-full h-12 mt-auto overflow-hidden leading-none">
    <svg className="w-full h-full text-grass-green fill-current" viewBox="0 0 1200 120" preserveAspectRatio="none">
        <path d="M0,0 V46.29 C47.79,22.2 103.59,32.17 158,28 C170.36,27.05 180.75,23.16 192,20 C242.42,5.84 286.07,35.45 330,45 C386.4,57.25 436.56,23.36 500,29 C562.9,34.59 598.67,61.9 655,67 C705.57,71.58 751.99,44.27 800,34 C861.91,20.76 910.82,46.12 970,52 C1032.55,58.21 1083.47,31.24 1140,31 C1160.7,30.91 1180.87,33.51 1200,38 V120 H0 V0 Z" />
    </svg>
  </div>
);

const PlantDecoration = ({ className }) => (
  <div className={`absolute pointer-events-none ${className}`}>
    <svg width="100" height="100" viewBox="0 0 100 100" className="text-grass-green fill-current opacity-80">
      <path d="M50 100 Q 20 50 10 20 Q 50 40 50 100" />
      <path d="M50 100 Q 80 50 90 20 Q 50 40 50 100" />
      <path d="M50 100 Q 50 10 50 0 Q 60 40 50 100" />
      <circle cx="10" cy="20" r="5" className="text-soft-pink fill-current" />
      <circle cx="90" cy="20" r="5" className="text-sun-yellow fill-current" />
      <circle cx="50" cy="0" r="5" className="text-white fill-current" />
    </svg>
  </div>
);

// --- COMPONENTS ---

const Navigation = ({ setView, user, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { id: 'landing', label: 'Home', public: true },
    { id: 'lore', label: 'Lore', public: true },
    { id: 'gallery', label: 'Gallery', public: true },
    { id: 'register', label: 'Join the Herd', public: !user },
    { id: 'login', label: 'Login', public: !user },
    { id: 'dashboard', label: 'The Pasture', public: !!user },
  ];

  return (
    <nav className="bg-meadow text-white sticky top-0 z-50 border-b-8 border-soft-pink shadow-2xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-24">
          <div className="flex items-center cursor-pointer transform hover:scale-105 transition-transform" onClick={() => setView('landing')}>
            <div className="bg-white rounded-full p-2 mr-3 border-4 border-soft-pink">
               <Ghost className="h-8 w-8 text-grass-green" />
            </div>
            <span className="font-display text-3xl tracking-wide text-white drop-shadow-md">COWS WITH A <span className="text-soft-pink text-4xl">K</span></span>
          </div>
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              {navItems.filter(item => item.public).map((item) => (
                <button
                  key={item.id}
                  onClick={() => setView(item.id)}
                  className="hover:bg-dark-grass hover:text-soft-pink px-4 py-2 rounded-xl text-lg font-bold font-body transition-all transform hover:-translate-y-1 uppercase tracking-wider bg-black/20 backdrop-blur-sm"
                >
                  {item.label}
                </button>
              ))}
              {user && (
                <button
                  onClick={onLogout}
                  className="bg-soft-pink hover:bg-white hover:text-soft-pink text-cow-black px-4 py-2 rounded-xl text-lg font-bold font-body shadow-md transition-colors"
                >
                  Logout
                </button>
              )}
            </div>
          </div>
          <div className="-mr-2 flex md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-white hover:text-soft-pink hover:bg-dark-grass focus:outline-none"
            >
              {isOpen ? <X className="h-8 w-8" /> : <Menu className="h-8 w-8" />}
            </button>
          </div>
        </div>
      </div>
      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-dark-grass border-t-4 border-soft-pink">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            {navItems.filter(item => item.public).map((item) => (
              <button
                key={item.id}
                onClick={() => { setView(item.id); setIsOpen(false); }}
                className="text-white hover:text-soft-pink block px-3 py-2 rounded-md text-xl font-display w-full text-left"
              >
                {item.label}
              </button>
            ))}
            {user && (
               <button
               onClick={() => { onLogout(); setIsOpen(false); }}
               className="text-soft-pink hover:text-white block px-3 py-2 rounded-md text-xl font-display w-full text-left"
             >
               Logout
             </button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

// -- VIEWS --

const LandingView = () => (
  <div className="min-h-screen relative overflow-hidden pb-32">
    <PlantDecoration className="bottom-0 left-10 w-48 h-48 transform -translate-y-12" />
    <PlantDecoration className="bottom-20 right-20 w-64 h-64 transform rotate-12" />
    
    {/* Hero */}
    <div className="relative bg-white mx-4 mt-12 rounded-2xl p-8 sm:p-16 text-center border-4 border-cow-black shadow-[10px_10px_0px_0px_#FFC1CC] max-w-5xl md:mx-auto z-10">
      <div className="absolute -top-6 -right-6 bg-soft-pink text-cow-black font-display text-xl px-4 py-2 rotate-12 border-2 border-cow-black shadow-lg">
        TOP SECRET!
      </div>
      <h1 className="text-5xl md:text-7xl text-cow-black mb-6 drop-shadow-sm">
        WE ARE <span className="text-soft-pink">WATCHING</span>.
        <br />
        WE ARE <span className="text-grass-green">GRAZING</span>.
      </h1>
      <p className="mt-6 text-2xl text-gray-700 font-body max-w-2xl mx-auto border-l-4 border-grass-green pl-6">
        The secret society they warned you about. <br/>
        <span className="font-bold text-soft-pink">Not sheep. Never sheep.</span>
      </p>
      <div className="mt-8 flex justify-center space-x-6">
        <Ghost className="text-cow-black h-12 w-12 animate-bounce" />
        <Leaf className="text-grass-green h-12 w-12" />
        <Ghost className="text-soft-pink h-12 w-12 animate-bounce" />
      </div>
    </div>

    {/* Festival Section */}
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 relative z-10">
      <div className="flex items-center justify-center mb-12 bg-white p-6 rounded-lg w-fit mx-auto border-4 border-cow-black shadow-xl transform -rotate-2">
        <Music className="h-10 w-10 text-soft-pink mr-4" />
        <h2 className="text-4xl font-display text-cow-black">Operation: MOOSIC FESTIVAL TAKEOVER</h2>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
        {FESTIVAL_IMAGES.map((img, idx) => (
          <div key={idx} className="group relative overflow-hidden rounded-md shadow-[8px_8px_0px_0px_#1a1a1a] transition-all border-4 border-cow-black transform hover:translate-x-1 hover:translate-y-1 hover:shadow-none bg-white">
            <img src={img.url} alt={img.caption} className="w-full h-64 object-cover hover:grayscale-0 transition-all duration-500" />
            <div className="absolute inset-0 bg-grass-green/90 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center p-6 text-center">
              <p className="text-white font-display text-2xl tracking-wide border-2 border-white p-2 transform -rotate-6">{img.caption}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
    
    {/* Bottom Grass */}
    <div className="fixed bottom-0 w-full z-0">
      <GrassSVG />
    </div>
  </div>
);

const LoreView = () => (
  <div className="min-h-screen py-16 px-4 relative pb-32">
    <div className="max-w-4xl mx-auto">
      <h2 className="text-5xl font-display text-cow-black mb-12 text-center bg-white inline-block px-8 py-4 shadow-[8px_8px_0px_0px_#4CAF50] mx-auto w-full border-4 border-cow-black rounded-lg">
        ARCHIVES: CLASSIFIED
      </h2>
      <div className="space-y-8">
        {LORE_DATA.map((lore) => (
          <div key={lore.id} className="bg-white p-8 rounded-md shadow-2xl relative overflow-hidden border-4 border-cow-black">
            <div className="absolute top-0 right-0 bg-cow-black text-soft-pink text-sm px-4 py-1 font-bold font-mono">
              {lore.clearance}
            </div>
            <h3 className="text-3xl font-display text-grass-green mb-2">{lore.title}</h3>
            <p className="text-sm text-gray-500 font-bold mb-4 uppercase tracking-widest border-b-2 border-gray-200 pb-2">LOG DATE: {lore.date}</p>
            <div 
              className="font-body text-xl leading-relaxed text-cow-black"
              dangerouslySetInnerHTML={{ __html: lore.content }}
            />
            <div className="mt-6 flex justify-end">
              <Shield className="h-8 w-8 text-grass-green opacity-20" />
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

const GalleryView = () => (
  <div className="min-h-screen py-16 px-4 relative overflow-hidden pb-32">
    <div className="max-w-6xl mx-auto relative z-10">
      <div className="text-center mb-12">
        <h2 className="text-6xl font-display text-white drop-shadow-[4px_4px_0px_#1a1a1a] mb-4 bg-grass-green inline-block px-6 py-2 transform -rotate-1 border-4 border-cow-black rounded-lg">Hall of Hooves</h2>
        <div className="mt-4">
             <p className="font-body text-xl text-cow-black bg-white border-2 border-cow-black inline-block px-6 py-2 shadow-[4px_4px_0px_0px_#FFC1CC] rounded-lg">Honoring excellence in the field (literally).</p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-12 p-8 bg-white/50 backdrop-blur-sm rounded-xl border-4 border-cow-black">
        {GALLERY_IMAGES.map((img, idx) => (
          <div key={idx} className="bg-white p-4 pb-12 shadow-xl rounded-sm transform rotate-1 hover:-rotate-1 transition-transform duration-300 relative border-2 border-gray-300">
            <div className="w-full aspect-square bg-gray-100 mb-4 overflow-hidden border border-gray-100">
               <img src={img.url} alt={img.caption} className="w-full h-full object-cover filter sepia-[.2]" />
            </div>
            <p className="font-display text-2xl text-center text-cow-black absolute bottom-2 left-0 w-full px-4 transform -rotate-1">
              {img.caption}
            </p>
            {/* Tape effect */}
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 w-32 h-8 bg-soft-pink/50 rotate-2 shadow-sm border border-soft-pink/20"></div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

const RegistrationView = ({ setView }) => {
  const [formData, setFormData] = useState({});
  const [status, setStatus] = useState('idle');

  const handleChange = (id, value) => {
    setFormData(prev => ({ ...prev, [id]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('submitting');
    try {
      await MockAWS.API.post('CowAPI', '/register', { body: formData });
      setStatus('success');
    } catch (err) {
      console.error(err);
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
        <div className="bg-white p-10 rounded-xl shadow-[15px_15px_0px_0px_#4CAF50] max-w-md w-full text-center border-4 border-cow-black relative z-10">
          <div className="bg-grass-green rounded-full p-4 w-24 h-24 mx-auto mb-6 flex items-center justify-center border-4 border-soft-pink">
             <CheckCircle className="h-12 w-12 text-white" />
          </div>
          <h2 className="text-4xl font-display font-bold mb-4 text-grass-green">Moo-velous!</h2>
          <p className="text-gray-600 mb-8 font-body text-lg">
            The High Council has received your responses. An Admin has been notified via AWS SES.
          </p>
          <div className="bg-gray-100 p-4 border-l-4 border-soft-pink text-cow-black font-bold mb-8 text-left">
            <strong>Next Steps:</strong> Graze patiently. Wait for the signal.
          </div>
          <button onClick={() => setView('landing')} className="w-full bg-soft-pink text-cow-black py-4 rounded-lg border-2 border-cow-black font-display text-xl hover:bg-white transition-colors shadow-lg">
            Return to Safety
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-4 flex justify-center relative overflow-hidden pb-32">
      <div className="bg-white w-full max-w-2xl rounded-xl shadow-[20px_20px_0px_0px_#1a1a1a] overflow-hidden border-4 border-cow-black z-10">
        <div className="bg-meadow p-8 text-center relative overflow-hidden border-b-4 border-soft-pink">
          <h2 className="text-4xl font-display font-bold text-white flex items-center justify-center relative z-10">
            <FileText className="mr-3 h-8 w-8" />
            Initiate Protocol: JOIN
          </h2>
          <p className="text-green-100 font-body text-lg mt-2 font-bold relative z-10 opacity-90">
            Answer truthfully. We have ways of knowing.
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          {REGISTRATION_QUESTIONS.map((q) => (
            <div key={q.id} className="space-y-2">
              <label className="block text-lg font-bold text-cow-black font-display">
                {q.label}
              </label>
              {q.type === 'text' && (
                <input 
                  required
                  type="text" 
                  className="w-full border-2 border-cow-black bg-white p-4 rounded-lg focus:outline-none focus:border-soft-pink focus:shadow-[4px_4px_0px_0px_#FFC1CC] transition-all font-body text-lg"
                  onChange={(e) => handleChange(q.id, e.target.value)}
                />
              )}
              {q.type === 'textarea' && (
                <textarea 
                  required
                  rows={4}
                  className="w-full border-2 border-cow-black bg-white p-4 rounded-lg focus:outline-none focus:border-soft-pink focus:shadow-[4px_4px_0px_0px_#FFC1CC] transition-all font-body text-lg"
                  onChange={(e) => handleChange(q.id, e.target.value)}
                />
              )}
              {q.type === 'select' && (
                <select 
                  required
                  className="w-full border-2 border-cow-black bg-white p-4 rounded-lg focus:outline-none focus:border-soft-pink focus:shadow-[4px_4px_0px_0px_#FFC1CC] transition-all font-body text-lg"
                  onChange={(e) => handleChange(q.id, e.target.value)}
                  defaultValue=""
                >
                  <option value="" disabled>Select an option...</option>
                  {q.options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                </select>
              )}
            </div>
          ))}

          <div className="pt-6 border-t-2 border-gray-100">
             <div className="flex items-start mb-6 bg-gray-50 p-4 border border-gray-200 rounded-lg">
                <input type="checkbox" required className="mt-1 mr-3 h-5 w-5 accent-grass-green" />
                <span className="text-sm text-gray-600 font-body">
                  I consent to having my data processed by AWS Lambda functions. I understand that my account status is subject to the whims of the Bovine High Council.
                </span>
             </div>
             
             <button 
              type="submit" 
              disabled={status === 'submitting'}
              className="w-full bg-grass-green text-white font-display text-2xl py-4 rounded-lg border-2 border-cow-black hover:bg-soft-pink hover:text-cow-black transition-all transform hover:-translate-y-1 shadow-lg flex justify-center items-center"
            >
              {status === 'submitting' ? 'TRANSMITTING...' : 'SUBMIT APPLICATION'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const LoginView = ({ setUser, setView }) => {
  const [email, setEmail] = useState('admin@cow.com');
  const [password, setPassword] = useState('moo');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      const user = await MockAWS.Auth.signIn(email, password);
      setUser(user);
      setView('dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative pb-32">
       
      <div className="bg-white p-10 rounded-xl shadow-[20px_20px_0px_0px_#000000] max-w-md w-full border-4 border-cow-black relative z-10">
        <div className="text-center mb-8">
          <div className="bg-grass-green rounded-full p-4 w-20 h-20 mx-auto mb-4 flex items-center justify-center shadow-md border-2 border-cow-black">
            <Lock className="h-10 w-10 text-white" />
          </div>
          <h2 className="text-4xl font-display font-bold text-cow-black">MEMBER ACCESS</h2>
        </div>
        
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 px-4 py-3 mb-6 text-sm font-bold">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-lg font-bold mb-2 text-grass-green font-display">Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-4 border-2 border-cow-black rounded-lg font-body text-lg focus:border-soft-pink focus:outline-none focus:shadow-[4px_4px_0px_0px_#FFC1CC] transition-shadow"
            />
          </div>
          <div>
            <label className="block text-lg font-bold mb-2 text-grass-green font-display">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-4 border-2 border-cow-black rounded-lg font-body text-lg focus:border-soft-pink focus:outline-none focus:shadow-[4px_4px_0px_0px_#FFC1CC] transition-shadow"
            />
          </div>
          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-cow-black text-white font-display text-2xl py-4 rounded-lg hover:bg-soft-pink hover:text-cow-black border-2 border-transparent hover:border-cow-black transition-colors shadow-lg"
          >
            {isLoading ? 'AUTHENTICATING...' : 'ENTER PASTURE'}
          </button>
        </form>
        <div className="mt-6 text-center text-sm text-gray-400 font-body">
          Hint: admin@cow.com / moo
        </div>
      </div>
    </div>
  );
};

// --- PRIVATE MEMBER VIEWS ---

const DashboardView = ({ user }) => {
  const [activeTab, setActiveTab] = useState('events');

  return (
    <div className="min-h-screen pb-32">
      <header className="bg-meadow text-white py-12 shadow-lg relative overflow-hidden border-b-4 border-soft-pink">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <h1 className="text-4xl md:text-5xl font-display font-bold">Welcome back, {user.username}.</h1>
          <p className="mt-2 text-xl text-green-100 font-body">The herd missed you.</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-20">
        <div className="bg-white rounded-xl shadow-[10px_10px_0px_0px_#1a1a1a] overflow-hidden min-h-[600px] flex flex-col md:flex-row border-4 border-cow-black">
          {/* Sidebar */}
          <aside className="w-full md:w-72 bg-cow-black text-gray-300 p-6 flex flex-col space-y-3">
            <button 
              onClick={() => setActiveTab('events')}
              className={`flex items-center p-4 rounded-lg transition-all font-display text-xl tracking-wide border-2 ${activeTab === 'events' ? 'bg-soft-pink text-cow-black border-cow-black shadow-[2px_2px_0px_0px_#ffffff]' : 'border-transparent hover:bg-gray-800'}`}
            >
              <Calendar className="mr-3 h-6 w-6" /> Events
            </button>
            <button 
              onClick={() => setActiveTab('board')}
              className={`flex items-center p-4 rounded-lg transition-all font-display text-xl tracking-wide border-2 ${activeTab === 'board' ? 'bg-soft-pink text-cow-black border-cow-black shadow-[2px_2px_0px_0px_#ffffff]' : 'border-transparent hover:bg-gray-800'}`}
            >
              <MessageSquare className="mr-3 h-6 w-6" /> Message Board
            </button>
            <button 
              onClick={() => setActiveTab('links')}
              className={`flex items-center p-4 rounded-lg transition-all font-display text-xl tracking-wide border-2 ${activeTab === 'links' ? 'bg-soft-pink text-cow-black border-cow-black shadow-[2px_2px_0px_0px_#ffffff]' : 'border-transparent hover:bg-gray-800'}`}
            >
              <LinkIcon className="mr-3 h-6 w-6" /> Resources
            </button>
          </aside>

          {/* Content Area */}
          <section className="flex-1 p-8 bg-gray-50 relative">
             <div className="absolute bottom-0 right-0 opacity-10 pointer-events-none">
               <PlantDecoration className="w-64 h-64 text-grass-green" />
             </div>
             
            {activeTab === 'events' && (
              <div className="space-y-6 relative z-10">
                <h2 className="text-4xl font-display text-grass-green border-b-4 border-soft-pink pb-2 inline-block">Upcoming Gatherings</h2>
                <div className="grid gap-6">
                  {EVENTS_DATA.map(ev => (
                    <div key={ev.id} className="bg-white p-6 rounded-lg shadow-md border-2 border-cow-black hover:shadow-[8px_8px_0px_0px_#4CAF50] transition-shadow">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-2xl font-display text-gray-900">{ev.title}</h3>
                          <p className="text-gray-500 font-bold flex items-center mt-2"><Map className="h-5 w-5 mr-2 text-soft-pink"/> {ev.location}</p>
                        </div>
                        <div className="text-center bg-grass-green text-white p-3 rounded-md min-w-[90px] border-2 border-cow-black">
                          <span className="block text-sm font-bold text-soft-pink uppercase">{new Date(ev.date).toLocaleString('default', { month: 'short' })}</span>
                          <span className="block text-3xl font-display">{new Date(ev.date).getDate()}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'board' && (
              <div className="h-full flex flex-col relative z-10">
                <h2 className="text-4xl font-display text-grass-green border-b-4 border-soft-pink pb-2 mb-4 inline-block">Herd Chatter</h2>
                <div className="flex-1 bg-white rounded-lg p-6 mb-4 overflow-y-auto h-96 space-y-6 border-2 border-cow-black shadow-inner">
                  {/* Mock Messages */}
                  <div className="flex flex-col space-y-1">
                    <span className="text-xs text-grass-green font-bold ml-1 uppercase">Bessie_007</span>
                    <div className="bg-gray-100 p-4 rounded-lg border-l-4 border-grass-green shadow-sm w-fit max-w-[80%] text-cow-black font-body font-bold">
                      Did anyone else see the farmer's new tractor? I think it's listening to us.
                    </div>
                  </div>
                  <div className="flex flex-col space-y-1 items-end">
                    <span className="text-xs text-soft-pink font-bold mr-1 uppercase">You</span>
                    <div className="bg-cow-black text-white p-4 rounded-lg border-r-4 border-soft-pink shadow-sm w-fit max-w-[80%] font-body">
                      Relax. It's just a John Deere. Stick to the code words.
                    </div>
                  </div>
                </div>
                <div className="flex">
                  <input type="text" placeholder="Type a message..." className="flex-1 border-2 border-cow-black bg-white p-4 rounded-l-lg focus:outline-none focus:border-soft-pink font-body" />
                  <button className="bg-grass-green text-white px-8 rounded-r-lg hover:bg-soft-pink hover:text-cow-black font-display text-xl transition-colors border-2 border-cow-black border-l-0">
                    Moo!
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'links' && (
              <div className="space-y-6 relative z-10">
                <h2 className="text-4xl font-display text-grass-green border-b-4 border-soft-pink pb-2 inline-block">Useful Links</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {MEMBER_LINKS.map((link, idx) => (
                    <a key={idx} href={link.url} className="block bg-white p-8 rounded-lg shadow-md hover:shadow-[8px_8px_0px_0px_#FFC1CC] transition-all border-2 border-cow-black group">
                      <h3 className="text-xl font-bold text-gray-900 group-hover:text-soft-pink flex items-center font-display tracking-wide">
                        {link.title} <LinkIcon className="ml-2 h-5 w-5 opacity-100 group-hover:text-soft-pink transition-opacity" />
                      </h3>
                      <p className="text-gray-500 text-sm mt-2 font-bold font-mono uppercase">External secure channel</p>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
};

// --- APP ROOT ---

const App = () => {
  const [view, setView] = useState('landing');
  const [user, setUser] = useState(null);

  const handleLogout = async () => {
    await MockAWS.Auth.signOut();
    setUser(null);
    setView('landing');
  };

  // Render logic based on state
  let currentComponent;
  switch (view) {
    case 'landing':
      currentComponent = <LandingView />;
      break;
    case 'lore':
      currentComponent = <LoreView />;
      break;
    case 'gallery':
      currentComponent = <GalleryView />;
      break;
    case 'register':
      currentComponent = <RegistrationView setView={setView} />;
      break;
    case 'login':
      currentComponent = <LoginView setUser={setUser} setView={setView} />;
      break;
    case 'dashboard':
      // Protected Route
      currentComponent = user ? <DashboardView user={user} /> : <LoginView setUser={setUser} setView={setView} />;
      break;
    default:
      currentComponent = <LandingView />;
  }

  return (
    <div className="min-h-screen flex flex-col font-body">
      <Navigation setView={setView} user={user} onLogout={handleLogout} />
      <div className="flex-grow">
        {currentComponent}
      </div>
      <footer className="bg-meadow text-white py-8 text-center font-display tracking-wider relative overflow-hidden border-t-4 border-soft-pink">
        <div className="relative z-10">
          <p className="text-xl">&copy; {new Date().getFullYear()} Cows with a K.</p>
          <p className="mt-2 text-sm opacity-70 font-body">Hosted on AWS S3 • Powered by Grass & Secrets</p>
        </div>
      </footer>
    </div>
  );
};

const root = createRoot(document.getElementById('root'));
root.render(<App />);