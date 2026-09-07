import React, { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '../hooks/useAuth';
import { 
  Send, Mic, MicOff, User, Bot, Sparkles, Building2, 
  ArrowRight, FileText, MapPin, RefreshCw, ShieldCheck, Check
} from 'lucide-react';
import { Link } from 'react-router-dom';

const SUGGESTED_QUESTIONS = [
  'Which schemes can I apply for?',
  'What documents do I need for PMEGP?',
  'Why was I matched with Mudra Loan?',
  'How do I apply for a 35% capital subsidy?',
  'Where is my nearest Common Service Center (CSC)?',
];

export default function Chat() {
  const { api, user } = useAuthStore();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Namaste ${user?.full_name ? user.full_name.split(' ')[0] : ''}! I am SchemeMatch AI Assistant. I can guide you through central & state government schemes, check why you qualify, prepare documents, and help you apply. What would you like to explore today?`,
      timestamp: new Date(),
      source: 'knowledge_base'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [language, setLanguage] = useState('hi');
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (messageText = input) => {
    const textToSend = messageText.trim();
    if (!textToSend || loading) return;

    setInput('');
    const userMessage = { 
      role: 'user', 
      content: textToSend, 
      timestamp: new Date() 
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await api().post('/chat/message', {
        message: textToSend,
        language: language,
        channel: 'text',
      });

      const replyContent = res.data?.reply || 'I am processing your inquiry. Please consult our Matches section for direct criteria evaluation.';
      const replySource = res.data?.source || 'rule_based_fallback';

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: replyContent,
          timestamp: new Date(),
          source: replySource,
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I apologize, but our network connection is experiencing high latency. You can still browse all matched schemes directly in your Matches dashboard.',
          timestamp: new Date(),
          source: 'offline_fallback',
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceToggle = () => {
    if (isRecording) {
      setIsRecording(false);
      // Simulate speech-to-text input
      setInput('Which schemes can I apply for with my current turnover?');
    } else {
      setIsRecording(true);
      setTimeout(() => {
        setIsRecording(false);
        handleSend('Which schemes can I apply for with my current turnover?');
      }, 2500);
    }
  };

  // Helper to detect if reply references schemes, documents or CSC
  const renderActionPills = (text = '') => {
    const lower = text.toLowerCase();
    const actions = [];
    if (lower.includes('scheme') || lower.includes('pmegp') || lower.includes('mudra') || lower.includes('match')) {
      actions.push(
        <Link 
          key="matches" 
          to="/matches" 
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-gov-navy-900 text-white text-xs font-bold hover:bg-gov-navy-800 transition-colors shadow-sm"
        >
          <Sparkles size={13} className="text-gov-saffron-400" />
          <span>View Matched Schemes</span>
        </Link>
      );
    }
    if (lower.includes('document') || lower.includes('aadhaar') || lower.includes('pan') || lower.includes('passbook')) {
      actions.push(
        <Link 
          key="docs" 
          to="/documents" 
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-100 text-slate-800 text-xs font-bold hover:bg-slate-200 transition-colors border border-slate-300"
        >
          <FileText size={13} />
          <span>Go to Document Center</span>
        </Link>
      );
    }
    if (lower.includes('csc') || lower.includes('center') || lower.includes('biometric')) {
      actions.push(
        <Link 
          key="csc" 
          to="/csc" 
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-gov-emerald-100 text-gov-emerald-900 text-xs font-bold hover:bg-gov-emerald-200 transition-colors border border-gov-emerald-300"
        >
          <MapPin size={13} />
          <span>Locate Nearest CSC</span>
        </Link>
      );
    }
    return actions.length > 0 ? (
      <div className="flex flex-wrap gap-2 mt-3 pt-2.5 border-t border-slate-100">
        {actions}
      </div>
    ) : null;
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-4xl mx-auto text-left">
      
      {/* Chat Top Header */}
      <div className="bg-white p-4 sm:p-5 rounded-t-3xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-gov-navy-950 via-gov-navy-800 to-gov-saffron-600 text-white flex items-center justify-center font-bold shadow-sm">
            <Bot size={22} className="text-gov-saffron-300" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base sm:text-lg font-bold text-gov-navy-950">
                SchemeMatch AI Assistant
              </h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gov-emerald-50 text-gov-emerald-700 border border-gov-emerald-200">
                Online
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Government scheme discovery, eligibility guidance & application support
            </p>
          </div>
        </div>

        {/* Language selector */}
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="text-xs font-semibold border border-slate-200 rounded-xl px-2.5 py-1.5 bg-slate-50 text-slate-700 focus:outline-none"
        >
          <option value="hi">हिन्दी (Hindi)</option>
          <option value="en">English</option>
          <option value="mr">मराठी (Marathi)</option>
          <option value="ta">தமிழ் (Tamil)</option>
        </select>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 bg-slate-50/50 border-x border-slate-200 p-4 sm:p-6 overflow-y-auto space-y-4 custom-scrollbar">
        
        {/* Suggested Prompts Bar */}
        {messages.length <= 2 && (
          <div className="space-y-2 pb-2">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Frequently Asked Questions:
            </p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q)}
                  className="text-xs font-semibold px-3 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:border-gov-navy-900 hover:text-gov-navy-950 transition-all shadow-sm text-left"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((msg, i) => {
          const isUser = msg.role === 'user';
          return (
            <div 
              key={i} 
              className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start`}
            >
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0 shadow-sm ${
                isUser ? 'bg-gov-navy-950 text-white' : 'bg-gov-saffron-600 text-white'
              }`}>
                {isUser ? <User size={15} /> : <Bot size={16} />}
              </div>

              {/* Message Content Bubble */}
              <div className={`max-w-[85%] sm:max-w-[75%] p-4 rounded-3xl text-xs sm:text-sm shadow-gov leading-relaxed ${
                isUser
                  ? 'bg-gov-navy-950 text-white rounded-tr-none'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none'
              }`}>
                <p className="whitespace-pre-line leading-relaxed">
                  {msg.content}
                </p>

                {/* Structured action buttons inside assistant bubble */}
                {!isUser && renderActionPills(msg.content)}

                {/* Engine Source transparency pill */}
                {!isUser && msg.source && (
                  <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400 font-medium">
                    <span>
                      {msg.source === 'knowledge_base' 
                        ? 'Grounded in National Ministry Guidelines' 
                        : 'SchemeMatch Deterministic Engine'}
                    </span>
                    <span>
                      {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Bubble */}
        {loading && (
          <div className="flex gap-3 items-start">
            <div className="w-8 h-8 rounded-xl bg-gov-saffron-600 text-white flex items-center justify-center text-xs font-bold shadow-sm">
              <Bot size={16} />
            </div>
            <div className="bg-white border border-slate-200 p-4 rounded-3xl rounded-tl-none shadow-gov flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-gov-saffron-600 animate-bounce" />
              <div className="w-2 h-2 rounded-full bg-gov-saffron-600 animate-bounce delay-100" />
              <div className="w-2 h-2 rounded-full bg-gov-saffron-600 animate-bounce delay-200" />
              <span className="text-xs text-slate-400 ml-1">Analyzing criteria & guidelines...</span>
            </div>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* Chat Input Bar */}
      <div className="bg-white p-3 sm:p-4 rounded-b-3xl border border-slate-200 shadow-md">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-2xl p-1.5 focus-within:border-gov-navy-950 focus-within:bg-white transition-all"
        >
          {/* Voice Input Button */}
          <button
            type="button"
            onClick={handleVoiceToggle}
            aria-label="Voice input"
            title="Voice input"
            className={`p-2.5 rounded-xl transition-all ${
              isRecording 
                ? 'bg-red-500 text-white animate-pulse' 
                : 'text-slate-500 hover:text-gov-navy-950 hover:bg-slate-200/60'
            }`}
          >
            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isRecording ? 'Listening in Hindi/English...' : 'Ask about government schemes, eligibility, or documents...'}
            className="flex-1 bg-transparent px-2 text-xs sm:text-sm text-slate-900 focus:outline-none"
          />

          <button
            type="submit"
            disabled={!input.trim() || loading}
            aria-label="Send message"
            className="p-2.5 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white disabled:opacity-40 disabled:cursor-not-allowed shadow-sm transition-all"
          >
            <Send size={16} />
          </button>
        </form>

        <p className="text-[10px] text-center text-slate-400 mt-2">
          SchemeMatch AI responses are for guidance. Final sanctions depend on nodal bank scrutiny and official DBT rules.
        </p>
      </div>

    </div>
  );
}
