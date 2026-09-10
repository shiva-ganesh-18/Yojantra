import React, { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { 
  Send, Mic, MicOff, User, Bot, Sparkles, Building2, 
  ArrowRight, FileText, MapPin, RefreshCw, ShieldCheck, Check,
  ExternalLink, Phone, AlertCircle, Info, Scale, Landmark
} from 'lucide-react';
import { Link } from 'react-router-dom';

const SUGGESTED_QUESTIONS = [
  'Which schemes are best for my business?',
  'Explain my eligibility for PMEGP subsidy',
  'Compare PMEGP and MUDRA loans',
  'What documents are required for capital subsidy?',
  'Calculate EMI for ₹10 Lakhs loan at 8.5%',
  'Where is my nearest Channel Partner or CSC Center?',
];

export default function Chat() {
  const { api, user } = useAuthStore();
  const { language, setLanguage, t, supportedLanguages } = useLanguage();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Namaste ${user?.full_name ? user.full_name.split(' ')[0] : 'Citizen'}! I am Yojantra AI. I am grounded strictly in 63 verified Central and State Government scheme records.\n\nI can evaluate your eligibility, compare schemes side-by-side, explain required documents, and guide your application through official channels.\n\nHow can I help you today?`,
      timestamp: new Date(),
      source: 'rule_based_fallback',
      cited_schemes: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [providerStatus, setProviderStatus] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await api().get('/chat/status');
        setProviderStatus(res.data);
      } catch (e) {
        setProviderStatus({
          provider: 'rule_based_fallback',
          is_ai_live: false,
          model_name: 'local_deterministic_rag',
          indexed_schemes_count: 63
        });
      }
    };
    fetchStatus();
  }, []);

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
      const citedSchemes = res.data?.cited_schemes || [];
      const disclaimer = res.data?.disclaimer;

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: replyContent,
          timestamp: new Date(),
          source: replySource,
          cited_schemes: citedSchemes,
          disclaimer: disclaimer
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Network connection is currently experiencing latency. I am falling back to offline scheme knowledge. You can explore all matched schemes directly in the Matches tab.',
          timestamp: new Date(),
          source: 'offline_fallback',
          cited_schemes: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceToggle = () => {
    // Voice capture is configuration-ready on the backend (POST /chat/voice
    // currently returns a static notice). Do not fabricate a user query:
    // surface an honest in-chat notice instead of auto-sending canned text.
    if (isRecording) {
      setIsRecording(false);
      return;
    }
    setIsRecording(true);
    setTimeout(() => {
      setIsRecording(false);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Voice input is configuration-ready: microphone capture and speech-to-text are not yet enabled in this build. Please type your question as text — I can evaluate eligibility, compare schemes, explain documents, and guide your application.',
          timestamp: new Date(),
          source: 'rule_based_fallback',
          cited_schemes: []
        }
      ]);
    }, 800);
  };

  // Helper to render structured scheme citation cards
  const renderSchemeCards = (citedSchemes = []) => {
    if (!citedSchemes || citedSchemes.length === 0) return null;

    return (
      <div className="mt-3 pt-3 border-t border-slate-200/80 space-y-2">
        <div className="flex items-center gap-1.5 text-[11px] font-bold text-gov-navy-950 uppercase tracking-wide">
          <Landmark size={13} className="text-gov-saffron-600" />
          <span>Verified Government Scheme Citations ({citedSchemes.length})</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {citedSchemes.map((s, idx) => (
            <div 
              key={idx}
              className="p-3 rounded-2xl bg-white border border-slate-200/90 shadow-sm hover:border-gov-navy-800 transition-all text-left flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-1">
                  <h4 className="font-bold text-xs text-gov-navy-950 leading-tight">
                    {s.name}
                  </h4>
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 flex-shrink-0">
                    {s.subsidy_percentage ? `${s.subsidy_percentage}% Subsidy` : 'Credit Subvention'}
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 mt-0.5 line-clamp-1">
                  {s.ministry || 'Central / State Ministry'}
                </p>

                <div className="mt-2 grid grid-cols-2 gap-1 text-[10px] bg-slate-50 p-1.5 rounded-lg border border-slate-100">
                  <div>
                    <span className="text-slate-400 block text-[9px]">Max Limit</span>
                    <span className="font-bold text-slate-800">
                      {s.max_benefit_inr ? `₹${(s.max_benefit_inr / 100000).toFixed(1)} L` : 'Appraisal'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[9px]">Rate / Terms</span>
                    <span className="font-bold text-slate-800">
                      {s.interest_rate ? `${s.interest_rate}% p.a.` : 'Concessional'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px]">
                {s.official_url && (
                  <a 
                    href={s.official_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-gov-navy-900 font-bold hover:underline"
                  >
                    <span>Official Portal</span>
                    <ExternalLink size={10} />
                  </a>
                )}
                {s.helpline_number && (
                  <span className="inline-flex items-center gap-1 text-slate-500 font-mono text-[9px]">
                    <Phone size={9} />
                    {s.helpline_number}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Action pills for quick routing
  const renderActionPills = (text = '') => {
    const lower = text.toLowerCase();
    const actions = [];
    if (lower.includes('scheme') || lower.includes('pmegp') || lower.includes('mudra') || lower.includes('match') || lower.includes('svanidhi')) {
      actions.push(
        <Link 
          key="matches" 
          to="/matches" 
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-gov-navy-900 text-white text-xs font-bold hover:bg-gov-navy-800 transition-colors shadow-sm"
        >
          <Sparkles size={13} className="text-gov-saffron-400" />
          <span>{t('dash_btn_view_matches', 'View Matched Schemes')}</span>
        </Link>
      );
    }
    if (lower.includes('document') || lower.includes('aadhaar') || lower.includes('pan') || lower.includes('passbook') || lower.includes('checklist')) {
      actions.push(
        <Link 
          key="docs" 
          to="/documents" 
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-100 text-slate-800 text-xs font-bold hover:bg-slate-200 transition-colors border border-slate-300"
        >
          <FileText size={13} />
          <span>{t('nav_documents', 'Document Center')}</span>
        </Link>
      );
    }
    if (lower.includes('partner') || lower.includes('csc') || lower.includes('center') || lower.includes('bank') || lower.includes('sca')) {
      actions.push(
        <Link 
          key="partners" 
          to="/institutions" 
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-gov-emerald-100 text-gov-emerald-900 text-xs font-bold hover:bg-gov-emerald-200 transition-colors border border-gov-emerald-300"
        >
          <MapPin size={13} />
          <span>{t('nav_institutions', 'Find Channel Partners & CSCs')}</span>
        </Link>
      );
    }
    return actions.length > 0 ? (
      <div className="flex flex-wrap gap-2 mt-3 pt-2.5 border-t border-slate-100">
        {actions}
      </div>
    ) : null;
  };

  const getSourceLabel = (source) => {
    switch (source) {
      case 'gemini_ai':
        return 'Google Gemini (Grounded in 63 DB Schemes)';
      case 'openai_ai':
        return 'OpenAI GPT (Grounded in 63 DB Schemes)';
      case 'rule_based_fallback':
        return 'Yojantra Grounded Deterministic RAG';
      case 'offline_fallback':
        return 'Offline Cache Knowledge Base';
      default:
        return 'Grounded Official Gazette Records';
    }
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
                {t('nav_ai_chat', 'Yojantra AI Assistant')}
              </h1>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                providerStatus?.is_ai_live 
                  ? 'bg-gov-emerald-50 text-gov-emerald-700 border-gov-emerald-200' 
                  : 'bg-blue-50 text-blue-700 border-blue-200'
              }`}>
                {providerStatus?.is_ai_live 
                  ? `${providerStatus.provider.toUpperCase()} AI Live (${providerStatus.indexed_schemes_count || 63} Schemes)`
                  : `Grounded Local RAG (${providerStatus?.indexed_schemes_count || 63} Schemes)`}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Zero-PII Grounded Intelligence • Scheme Comparisons • Application Pathways
            </p>
          </div>
        </div>

        {/* Language selector */}
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="text-xs font-semibold border border-slate-200 rounded-xl px-2.5 py-1.5 bg-slate-50 text-slate-700 focus:outline-none"
        >
          {supportedLanguages.map(l => (
            <option key={l.code} value={l.code}>
              {l.label} ({l.englishName})
            </option>
          ))}
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
                  className="text-xs font-semibold px-3 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:border-gov-navy-900 hover:text-gov-navy-950 transition-all shadow-sm text-left flex items-center gap-1.5"
                >
                  <Sparkles size={12} className="text-gov-saffron-500 flex-shrink-0" />
                  <span>{q}</span>
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
              <div className={`max-w-[90%] sm:max-w-[80%] p-4 rounded-3xl text-xs sm:text-sm shadow-gov leading-relaxed ${
                isUser
                  ? 'bg-gov-navy-950 text-white rounded-tr-none'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none'
              }`}>
                <div className="whitespace-pre-line leading-relaxed">
                  {msg.content}
                </div>

                {/* Structured Scheme Citations */}
                {!isUser && renderSchemeCards(msg.cited_schemes)}

                {/* Structured Action Buttons */}
                {!isUser && renderActionPills(msg.content)}

                {/* Statutory Non-Approval Notice Alert */}
                {!isUser && msg.disclaimer && (
                  <div className="mt-2.5 p-2 rounded-xl bg-amber-50/80 border border-amber-200 text-[10px] text-amber-900 leading-snug flex items-start gap-1.5">
                    <AlertCircle size={12} className="text-amber-600 flex-shrink-0 mt-0.5" />
                    <span>{msg.disclaimer}</span>
                  </div>
                )}

                {/* Engine Source & Metadata Footer */}
                {!isUser && (
                  <div className="mt-2.5 pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-1 text-[10px] text-slate-400 font-medium">
                    <span className="flex items-center gap-1">
                      <ShieldCheck size={11} className="text-gov-emerald-600" />
                      {getSourceLabel(msg.source)}
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
              <span className="text-xs text-slate-400 ml-1">Retrieving verified scheme data & calculating guidelines...</span>
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
            className={`p-3 rounded-xl transition-all min-h-[44px] min-w-[44px] flex items-center justify-center ${
              isRecording 
                ? 'bg-red-500 text-white animate-pulse' 
                : 'text-slate-500 hover:text-gov-navy-950 hover:bg-slate-200/60'
            }`}
          >
            {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isRecording ? 'Listening in Hindi/English...' : 'Ask about government schemes, eligibility, comparisons, or EMIs...'}
            className="flex-1 bg-transparent px-2 text-xs sm:text-sm text-slate-900 focus:outline-none"
          />

          <button
            type="submit"
            disabled={!input.trim() || loading}
            aria-label="Send message"
            className="p-3 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white disabled:opacity-40 disabled:cursor-not-allowed shadow-sm transition-all min-h-[44px] min-w-[44px] flex items-center justify-center"
          >
            <Send size={18} />
          </button>
        </form>

        <p className="text-[10px] text-center text-slate-500 mt-2 flex items-center justify-center gap-1.5 font-medium">
          <ShieldCheck size={12} className="text-gov-emerald-600 flex-shrink-0" />
          <span>Statutory Notice: Yojantra guidance is grounded in verified scheme gazettes. It does NOT constitute an official government sanction or loan approval.</span>
        </p>
      </div>

    </div>
  );
}

