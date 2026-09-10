"""Localization service for Yojantra (GovTech Scheme Platform).

Supports 12 Scheduled Indian Languages + English:
en, hi, mr, ta, te, bn, gu, kn, ml, pa, or, as.

Strictly adheres to the GovTech Official Data Integrity Principle:
Official statutory scheme names, gazette numbers, ministry designations,
statutory URLs, and banking/DBT reference codes must remain canonical and
never be corrupted or translated incorrectly.
"""

from typing import Dict, Any, Optional, List
import re

SUPPORTED_LANGUAGES: List[Dict[str, str]] = [
    {"code": "hi", "label": "हिन्दी", "english_name": "Hindi", "script": "Devanagari"},
    {"code": "en", "label": "English", "english_name": "English", "script": "Latin"},
    {"code": "mr", "label": "मराठी", "english_name": "Marathi", "script": "Devanagari"},
    {"code": "ta", "label": "தமிழ்", "english_name": "Tamil", "script": "Tamil"},
    {"code": "te", "label": "తెలుగు", "english_name": "Telugu", "script": "Telugu"},
    {"code": "bn", "label": "বাংলা", "english_name": "Bengali", "script": "Bengali"},
    {"code": "gu", "label": "ગુજરાતી", "english_name": "Gujarati", "script": "Gujarati"},
    {"code": "kn", "label": "ಕನ್ನಡ", "english_name": "Kannada", "script": "Kannada"},
    {"code": "ml", "label": "മലയാളം", "english_name": "Malayalam", "script": "Malayalam"},
    {"code": "pa", "label": "ਪੰਜਾਬੀ", "english_name": "Punjabi", "script": "Gurmukhi"},
    {"code": "or", "label": "ଓଡ଼ିଆ", "english_name": "Odia", "script": "Odia"},
    {"code": "as", "label": "অসমীয়া", "english_name": "Assamese", "script": "Bengali-Assamese"},
]

SUPPORTED_CODES = {l["code"] for l in SUPPORTED_LANGUAGES}
DEFAULT_LANGUAGE = "hi"

# Localized system messages & error alerts
SYSTEM_MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        "ERR_UNAUTHORIZED": "Authentication required. Please log in to continue.",
        "ERR_NOT_FOUND": "The requested government scheme or record was not found.",
        "ERR_VALIDATION_FAILED": "Validation check failed. Please verify required documents and profile details.",
        "ERR_NETWORK_ERROR": "Network communication failed. Please check your internet connection.",
        "ERR_GATEWAY_UNAVAILABLE": "Government/Banking portal gateway is temporarily busy. Please retry shortly.",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ Scheme Deadline Approaching",
        "NOTIF_DEADLINE_7D_BODY": "Your bookmarked scheme '{scheme_name}' deadline is in 7 days. Apply early to complete nodal review.",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 Urgent: Scheme Deadline in 3 Days",
        "NOTIF_DEADLINE_3D_BODY": "Only 3 days left to apply for '{scheme_name}'. Submit your document dossier before window closes.",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 Final Notice: Scheme Closes Today",
        "NOTIF_DEADLINE_1D_BODY": "Today is the final day to submit your application for '{scheme_name}'.",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 Application Dossier Submitted",
        "NOTIF_APP_SUBMITTED_BODY": "Application for '{scheme_name}' registered with reference '{ref_code}'. Under partner review.",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ Document Verified",
        "NOTIF_DOC_VERIFIED_BODY": "Your document '{doc_type}' has been verified by internal scrutiny.",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 Application Status Updated",
        "NOTIF_STATUS_UPDATED_BODY": "Application for '{scheme_name}' moved to status: '{status}'.",
    },
    "hi": {
        "ERR_UNAUTHORIZED": "प्रमाणीकरण आवश्यक है। जारी रखने के लिए कृपया लॉगिन करें।",
        "ERR_NOT_FOUND": "अनुरोधित सरकारी योजना या रिकॉर्ड नहीं मिला।",
        "ERR_VALIDATION_FAILED": "सत्यापन जांच विफल रही। कृपया आवश्यक दस्तावेज़ और प्रोफ़ाइल विवरण जांचें।",
        "ERR_NETWORK_ERROR": "नेटवर्क संचार विफल रहा। कृपया अपना इंटरनेट कनेक्शन जांचें।",
        "ERR_GATEWAY_UNAVAILABLE": "सरकारी/बैंकिंग पोर्टल गेटवे अस्थायी रूप से व्यस्त है। कृपया थोड़ी देर बाद प्रयास करें।",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ योजना की समय सीमा नज़दीक है",
        "NOTIF_DEADLINE_7D_BODY": "आपकी बुकमार्क की गई योजना '{scheme_name}' की अंतिम तिथि में 7 दिन शेष हैं।",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 आवश्यक: योजना की समय सीमा में केवल 3 दिन",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}' के लिए आवेदन करने हेतु केवल 3 दिन शेष हैं। समय रहते आवेदन जमा करें।",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 अंतिम सूचना: योजना आज समाप्त हो रही है",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}' के लिए आवेदन करने का आज अंतिम दिन है। तुरंत आवेदन करें।",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 आवेदन डॉसियर जमा किया गया",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}' के लिए आवेदन संदर्भ संख्या '{ref_code}' के साथ दर्ज हो चुका है।",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ दस्तावेज़ सत्यापित",
        "NOTIF_DOC_VERIFIED_BODY": "आपका दस्तावेज़ '{doc_type}' आंतरिक जांच द्वारा सत्यापित कर दिया गया है।",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 आवेदन स्थिति अपडेट",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' के आवेदन की स्थिति अब '{status}' है।",
    },
    "mr": {
        "ERR_UNAUTHORIZED": "प्रमाणीकरण आवश्यक आहे. सुरू ठेवण्यासाठी कृपया लॉगिन करा.",
        "ERR_NOT_FOUND": "मागितलेली सरकारी योजना किंवा नोंद आढळली नाही.",
        "ERR_VALIDATION_FAILED": "पडताळणी अयशस्वी झाली. कृपया आवश्यक कागदपत्रे आणि तपशील तपासा.",
        "ERR_NETWORK_ERROR": "नेटवर्क संपर्क अयशस्वी झाला. कृपया इंटरनेट तपासा.",
        "ERR_GATEWAY_UNAVAILABLE": "सरकारी/बँकिंग पोर्टल गेटवे व्यस्त आहे. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ योजनेची मुदत जवळ आली आहे",
        "NOTIF_DEADLINE_7D_BODY": "तुमची बुकमार्क केलेली योजना '{scheme_name}' ची अंतिम मुदत ७ दिवसांत संपत आहे.",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 तातडीचे: योजनेची मुदत ३ दिवसांत संपत आहे",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}' साठी अर्ज करण्यासाठी फक्त ३ दिवस शिल्लक आहेत.",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 शेवटची सूचना: योजनेचा आज शेवटचा दिवस",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}' साठी अर्ज करण्याचा आज अखेरचा दिवस आहे.",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 अर्ज डॉसियर सादर केले",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}' साठी अर्ज संदर्भ क्रमांक '{ref_code}' सह नोंदवला गेला आहे.",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ कागदपत्र सत्यापित",
        "NOTIF_DOC_VERIFIED_BODY": "तुमचे कागदपत्र '{doc_type}' अंतर्गत तपासणीद्वारे सत्यापित केले गेले आहे.",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 अर्जाची स्थिती अपडेट",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' अर्जाची स्थिती आता '{status}' आहे.",
    },
    "ta": {
        "ERR_UNAUTHORIZED": "அங்கீகாரம் தேவை. தொடர உள்நுழையவும்.",
        "ERR_NOT_FOUND": "கோரப்பட்ட அரசுத் திட்டம் அல்லது பதிவு காணப்படவில்லை.",
        "ERR_VALIDATION_FAILED": "சரிபார்ப்பு தோல்வியடைந்தது. தேவையான ஆவணங்களைச் சரிபார்க்கவும்.",
        "ERR_NETWORK_ERROR": "நெட்வொர்க் இணைப்பு தோல்வியடைந்தது. இணையத்தைச் சோதிக்கவும்.",
        "ERR_GATEWAY_UNAVAILABLE": "அரசு/வங்கி போர்டல் நுழைவாயில் தற்காலிகமாக பிஸியாக உள்ளது.",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ திட்ட காலக்கெடு நெருங்குகிறது",
        "NOTIF_DEADLINE_7D_BODY": "நீங்கள் சேமித்த திட்டம் '{scheme_name}' காலக்கெடு 7 நாட்களில் முடிகிறது.",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 அவசரம்: திட்ட காலக்கெடு 3 நாட்களில் முடிகிறது",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}' திட்டத்திற்கு விண்ணப்பிக்க இன்னும் 3 நாட்கள் மட்டுமே உள்ளன.",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 இறுதி அறிவிப்பு: இன்று கடைசி நாள்",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}' திட்டத்திற்கு விண்ணப்பிக்க இன்றே கடைசி நாள்.",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 விண்ணப்பம் சமர்ப்பிக்கப்பட்டது",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}' திட்டத்திற்கான விண்ணப்பக் குறிப்பு எண்: '{ref_code}'.",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ ஆவணம் சரிபார்க்கப்பட்டது",
        "NOTIF_DOC_VERIFIED_BODY": "உங்கள் ஆவணம் '{doc_type}' வெற்றிகரமாக சரிபார்க்கப்பட்டது.",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 விண்ணப்ப நிலை புதுப்பிக்கப்பட்டது",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' விண்ணப்பத்தின் தற்போதைய நிலை: '{status}'.",
    },
    "te": {
        "ERR_UNAUTHORIZED": "ప్రామాణీకరణ అవసరం. దయచేసి లాగిన్ అవ్వండి.",
        "ERR_NOT_FOUND": "అభ్యర్థించిన ప్రభుత్వ పథకం లేదా రికార్డు కనుగొనబడలేదు.",
        "ERR_VALIDATION_FAILED": "ధృవీకరణ తనిఖీ విఫలమైంది. అవసరమైన పత్రాలను తనిఖీ చేయండి.",
        "ERR_NETWORK_ERROR": "నెట్‌వర్క్ కనెక్షన్ విఫలమైంది. ఇంటర్నెట్‌ను తనిఖీ చేయండి.",
        "ERR_GATEWAY_UNAVAILABLE": "ప్రభుత్వ పోర్టల్ గేట్‌వే తాత్కాలికంగా బిజీగా ఉంది.",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ పథకం గడువు సమీపిస్తోంది",
        "NOTIF_DEADLINE_7D_BODY": "మీ పథకం '{scheme_name}' గడువు 7 రోజుల్లో ముగుస్తుంది.",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 అత్యవసరం: పథకం గడువు 3 రోజుల్లో ముగుస్తుంది",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}' కోసం దరఖాస్తు చేసుకోవడానికి 3 రోజులు మాత్రమే మిగిలి ఉన్నాయి.",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 తుది నోటీసు: పథకం ఈ రోజే ముగుస్తుంది",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}' కోసం దరఖాస్తు చేయడానికి ఈ రోజే చివరి రోజు.",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 దరఖాస్తు సమర్పించబడింది",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}' కోసం దరఖాస్తు రిఫరెన్స్ కోడ్ '{ref_code}'తో నమోదైంది.",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ పత్రం ధృవీకరించబడింది",
        "NOTIF_DOC_VERIFIED_BODY": "మీ పత్రం '{doc_type}' విజయవంతంగా ధృవీకరించబడింది.",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 దరఖాస్తు స్థితి నవీకరించబడింది",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' దరఖాస్తు స్థితి ఇప్పుడు '{status}'.",
    },
    "bn": {
        "ERR_UNAUTHORIZED": "প্রমাণীকরণ আবশ্যক। এগিয়ে যেতে দয়া করে লগইন করুন।",
        "ERR_NOT_FOUND": "অনুরোধ করা সরকারি প্রকল্প বা নথি পাওয়া যায়নি।",
        "ERR_VALIDATION_FAILED": "যাচাইকরণ ব্যর্থ হয়েছে। অনুগ্রহ করে প্রয়োজনীয় নথি পরীক্ষা করুন।",
        "ERR_NETWORK_ERROR": "নেটওয়ার্ক সংযোগ ব্যর্থ হয়েছে। আপনার ইন্টারনেট পরীক্ষা করুন।",
        "ERR_GATEWAY_UNAVAILABLE": "সরকারি/ব্যাংকিং পোর্টাল গেটওয়ে সাময়িকভাবে ব্যস্ত।",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ প্রকল্পের সময়সীমা ঘনিয়ে আসছে",
        "NOTIF_DEADLINE_7D_BODY": "আপনার সংরক্ষিত প্রকল্প '{scheme_name}'-এর সময়সীমা শেষ হতে ৭ দিন বাকি।",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 জরুরি: প্রকল্পের মেয়াদ ৩ দিনে শেষ হচ্ছে",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}'-এর জন্য আবেদন করতে মাত্র ৩ দিন বাকি রয়েছে।",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 শেষ বিজ্ঞপ্তি: আজই শেষ দিন",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}'-এর জন্য আবেদন জমা দেওয়ার আজই শেষ দিন।",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 আবেদনপত্র জমা হয়েছে",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}'-এর জন্য আবেদন রেফারেন্স কোড '{ref_code}' সহ নথিভুক্ত হয়েছে।",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ নথি যাচাই সম্পন্ন",
        "NOTIF_DOC_VERIFIED_BODY": "আপনার নথি '{doc_type}' সফলভাবে যাচাই করা হয়েছে।",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 আবেদনের স্থিতি আপডেট",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' আবেদনের স্থিতি এখন '{status}'।",
    },
    "gu": {
        "ERR_UNAUTHORIZED": "ઓથેન્ટિકેશન જરૂરી છે. આગળ વધવા માટે કૃપા કરીને લૉગિન કરો.",
        "ERR_NOT_FOUND": "વિનંતી કરેલ સરકારી યોજના અથવા રેકોર્ડ મળ્યો નથી.",
        "ERR_VALIDATION_FAILED": "ચકાસણી નિષ્ફળ રહી. કૃપા કરીને જરૂરી દસ્તાવેજો તપાસો.",
        "ERR_NETWORK_ERROR": "નેટવર્ક કનેક્શન નિષ્ફળ થયું. કૃપા કરીને ઇન્ટરનેટ તપાસો.",
        "ERR_GATEWAY_UNAVAILABLE": "સરકારી પોર્ટલ ગેટવે અસ્થાયી રૂપે વ્યસ્ત છે.",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ યોજનાની અંતિમ તારીખ નજીક છે",
        "NOTIF_DEADLINE_7D_BODY": "તમારી સેવ કરેલી યોજના '{scheme_name}' ની મુદત 7 દિવસમાં પૂર્ણ થાય છે.",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 તાકીદનું: યોજનાની મુદતમાં ફક્ત 3 દિવસ બાકી",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}' માટે અરજી કરવા ફક્ત 3 દિવસ બાકી છે.",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 આખરી સૂચના: યોજના આજે પૂર્ણ થાય છે",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}' માટે અરજી કરવાનો આજે છેલ્લો દિવસ છે.",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 અરજી સબમિટ થઈ ગઈ",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}' માટે અરજી રેફરન્સ કોડ '{ref_code}' સાથે નોંધાઈ ગઈ છે.",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ દસ્તાવેજ ચકાસાયેલ છે",
        "NOTIF_DOC_VERIFIED_BODY": "તમારો દસ્તાવેજ '{doc_type}' ચકાસી લેવામાં આવ્યો છે.",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 અરજી સ્થિતિ અપડેટ",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' અરજીની સ્થિતિ હવે '{status}' છે.",
    },
    "kn": {
        "ERR_UNAUTHORIZED": "ದೃಢೀಕರಣ ಅಗತ್ಯವಿದೆ. ಮುಂದುವರಿಯಲು ದಯವಿಟ್ಟು ಲಾಗಿನ್ ಮಾಡಿ.",
        "ERR_NOT_FOUND": "ವಿನಂತಿಸಿದ ಸರ್ಕಾರಿ ಯೋಜನೆ ಅಥವಾ ದಾಖಲೆ ಕಂಡುಬಂದಿಲ್ಲ.",
        "ERR_VALIDATION_FAILED": "ಪರಿಶೀಲನೆ ವಿಫಲವಾಗಿದೆ. ಅಗತ್ಯ ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.",
        "ERR_NETWORK_ERROR": "ನೆಟ್‌ವರ್ಕ್ ಸಂಪರ್ಕ ವಿಫಲವಾಗಿದೆ. ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವನ್ನು ಪರಿಶೀಲಿಸಿ.",
        "ERR_GATEWAY_UNAVAILABLE": "ಸರ್ಕಾರಿ ಪೋರ್ಟಲ್ ಗೇಟ್‌ವೇ ತಾತ್ಕಾಲಿಕವಾಗಿ ಕಾರ್ಯನಿರತವಾಗಿದೆ.",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ ಯೋಜನೆಯ ಗಡುವು ಸಮೀಪಿಸುತ್ತಿದೆ",
        "NOTIF_DEADLINE_7D_BODY": "ನಿಮ್ಮ ಉಳಿಸಿದ ಯೋಜನೆ '{scheme_name}' ಗಡುವು 7 ದಿನಗಳಲ್ಲಿ ಕೊನೆಗೊಳ್ಳುತ್ತದೆ.",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 ತುರ್ತು: ಯೋಜನೆಗೆ ಕೇವಲ 3 ದಿನಗಳು ಬಾಕಿ",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}' ಯೋಜನೆಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಲು 3 ದಿನಗಳು ಮಾತ್ರ ಉಳಿದಿವೆ.",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 ಕೊನೆಯ ಸೂಚನೆ: ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಇಂದೇ ಕೊನೆ ದಿನ",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}' ಯೋಜನೆಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಇಂದೇ ಕೊನೆಯ ದಿನವಾಗಿದೆ.",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 ಅರ್ಜಿ ಸಲ್ಲಿಸಲಾಗಿದೆ",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}' ಅರ್ಜಿ ಉಲ್ಲೇಖ ಸಂಕೇತ '{ref_code}' ನೊಂದಿಗೆ ದಾಖಲಾಗಿದೆ.",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ ದಾಖಲೆ ಪರಿಶೀಲಿಸಲಾಗಿದೆ",
        "NOTIF_DOC_VERIFIED_BODY": "ನಿಮ್ಮ ದಾಖಲೆ '{doc_type}' ಯಶಸ್ವಿಯಾಗಿ ಪರಿಶೀಲಿಸಲ್ಪಟ್ಟಿದೆ.",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 ಅರ್ಜಿಯ ಸ್ಥಿತಿ ನವೀಕರಿಸಲಾಗಿದೆ",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' ಅರ್ಜಿಯ ಸ್ಥಿತಿ ಈಗ '{status}'.",
    },
    "ml": {
        "ERR_UNAUTHORIZED": "തുടരുന്നതിന് ദയവായി ലോഗിൻ ചെയ്യുക.",
        "ERR_NOT_FOUND": "ആവശ്യപ്പെട്ട സർക്കാർ പദ്ധതി കണ്ടെത്താനായില്ല.",
        "ERR_VALIDATION_FAILED": "പരിശോധന പരാജയപ്പെട്ടു. ആവശ്യമായ രേഖകൾ പരിശോധിക്കുക.",
        "ERR_NETWORK_ERROR": "നെറ്റ്‌വർക്ക് കണക്ഷൻ പരാജയപ്പെട്ടു.",
        "ERR_GATEWAY_UNAVAILABLE": "സർക്കാർ പോർട്ടൽ താൽക്കാലികമായി ലഭ്യമല്ല.",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ പദ്ധതിയുടെ അവസാന തീയതി അടുക്കുന്നു",
        "NOTIF_DEADLINE_7D_BODY": "'{scheme_name}' പദ്ധതിയുടെ അവസാന തീയതിക്ക് 7 ദിവസം ബാക്കിയുണ്ട്.",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 അടിയന്തിരം: 3 ദിവസം മാത്രം ബാക്കി",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}' അപേക്ഷിക്കാൻ 3 ദിവസങ്ങൾ മാത്രം ബാക്കി.",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 അവസാന അറിയിപ്പ്: ഇന്ന് അവസാന തീയതി",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}' അപേക്ഷിക്കാനുള്ള അവസാന ദിവസം ഇന്നാണ്.",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 അപേക്ഷ സമർപ്പിച്ചു",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}' അപേക്ഷ റഫറൻസ് കോഡ് '{ref_code}' രേഖപ്പെടുത്തി.",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ രേഖ പരിശോധിച്ചു",
        "NOTIF_DOC_VERIFIED_BODY": "നിങ്ങളുടെ '{doc_type}' രേഖ വിജയകരമായി പരിശോധിച്ചു.",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 അപേക്ഷാ നില അപ്ഡേറ്റ് ചെയ്തു",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' അപേക്ഷയുടെ ഇപ്പോഴത്തെ നില: '{status}'.",
    },
    "pa": {
        "ERR_UNAUTHORIZED": "ਪ੍ਰਮਾਣਿਕਤਾ ਦੀ ਲੋੜ ਹੈ। ਜਾਰੀ ਰੱਖਣ ਲਈ ਕਿਰਪਾ ਕਰਕੇ ਲੌਗਇਨ ਕਰੋ।",
        "ERR_NOT_FOUND": "ਬੇਨਤੀ ਕੀਤੀ ਸਰਕਾਰੀ ਯੋਜਨਾ ਜਾਂ ਰਿਕਾਰਡ ਨਹੀਂ ਮਿਲਿਆ।",
        "ERR_VALIDATION_FAILED": "ਪੜਤਾਲ ਅਸਫਲ ਰਹੀ। ਕਿਰਪਾ ਕਰਕੇ ਲੋੜੀਂਦੇ ਦਸਤਾਵੇਜ਼ ਚੈੱਕ ਕਰੋ।",
        "ERR_NETWORK_ERROR": "ਨੈੱਟਵਰਕ ਸੰਚਾਰ ਅਸਫਲ ਰਿਹਾ।",
        "ERR_GATEWAY_UNAVAILABLE": "ਸਰਕਾਰੀ ਪੋਰਟਲ ਗੇਟਵੇ ਆਰਜ਼ੀ ਤੌਰ 'ਤੇ ਵਿਅਸਤ ਹੈ।",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ ਯੋਜਨਾ ਦੀ ਆਖਰੀ ਮਿਤੀ ਨੇੜੇ ਹੈ",
        "NOTIF_DEADLINE_7D_BODY": "ਤੁਹਾਡੀ ਚੁਣੀ ਯੋਜਨਾ '{scheme_name}' ਦੀ ਆਖਰੀ ਮਿਤੀ ਵਿੱਚ 7 ਦਿਨ ਬਾਕੀ ਹਨ।",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 ਜ਼ਰੂਰੀ: ਯੋਜਨਾ ਲਈ ਸਿਰਫ਼ 3 ਦਿਨ ਬਾਕੀ",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}' ਲਈ ਅਰਜ਼ੀ ਦੇਣ ਲਈ ਸਿਰਫ਼ 3 ਦਿਨ ਬਾਕੀ ਹਨ।",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 ਆਖਰੀ ਨੋਟਿਸ: ਅੱਜ ਆਖਰੀ ਦਿਨ ਹੈ",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}' ਲਈ ਅਰਜ਼ੀ ਦੇਣ ਦਾ ਅੱਜ ਆਖਰੀ ਦਿਨ ਹੈ।",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 ਅਰਜ਼ੀ ਜਮ੍ਹਾਂ ਹੋ ਗਈ",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}' ਲਈ ਅਰਜ਼ੀ ਰੈਫਰੈਂਸ ਕੋਡ '{ref_code}' ਨਾਲ ਦਰਜ ਹੋ ਗਈ ਹੈ।",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ ਦਸਤਾਵੇਜ਼ ਤਸਦੀਕ ਹੋ ਗਿਆ",
        "NOTIF_DOC_VERIFIED_BODY": "ਤੁਹਾਡਾ ਦਸਤਾਵੇਜ਼ '{doc_type}' ਤਸਦੀਕ ਕਰ ਦਿੱਤਾ ਗਿਆ ਹੈ।",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 ਅਰਜ਼ੀ ਦੀ ਸਥਿਤੀ ਅੱਪਡੇਟ",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' ਅਰਜ਼ੀ ਦੀ ਸਥਿਤੀ ਹੁਣ '{status}' ਹੈ।",
    },
    "or": {
        "ERR_UNAUTHORIZED": "ପ୍ରମାଣୀକରଣ ଆବଶ୍ୟକ। ଦୟାକରି ଲଗଇନ୍ କରନ୍ତୁ।",
        "ERR_NOT_FOUND": "ଅନୁରୋଧିତ ସରକାରୀ ଯୋଜନା ମିଳିଲା ନାହିଁ।",
        "ERR_VALIDATION_FAILED": "ଯାଞ୍ଚ ବିଫଳ ହୋଇଛି। ଆବଶ୍ୟକ ଦସ୍ତାବିଜ ଯାଞ୍ଚ କରନ୍ତୁ।",
        "ERR_NETWORK_ERROR": "ନେଟୱାର୍କ ସଂଯୋଗ ବିଫଳ ହୋଇଛି।",
        "ERR_GATEWAY_UNAVAILABLE": "ସରକାରୀ ପୋର୍ଟାଲ୍ ଗେଟୱେ ବ୍ୟସ୍ତ ଅଛି।",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ ଯୋଜନାର ଅନ୍ତିମ ତାରିଖ ନିକଟତର",
        "NOTIF_DEADLINE_7D_BODY": "ଆପଣଙ୍କ ଯୋଜନା '{scheme_name}'ର ଶେଷ ତାରିଖ ୭ ଦିନରେ ଅଛି।",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 ଜରୁରୀ: ଯୋଜନା ପାଇଁ କେବଳ ୩ ଦିନ ବାକି",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}' ପାଇଁ ଆବେଦନ କରିବାକୁ ମାତ୍ର ୩ ଦିନ ବାକି ଅଛି।",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 ଚୂଡ଼ାନ୍ତ ବିଜ୍ଞପ୍ତି: ଆଜି ଶେଷ ଦିନ",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}' ପାଇଁ ଆବେଦନ କରିବାର ଆଜି ଅନ୍ତିମ ଦିନ।",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 ଆବେଦନ ଦାଖଲ ହୋଇଛି",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}' ପାଇଁ ଆବେଦନ ରେଫରେନ୍ସ କୋଡ୍ '{ref_code}' ସହିତ ପଞ୍ଜୀକୃତ ହୋଇଛି।",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ ଦସ୍ତାବିଜ ଯାଞ୍ଚ ସଫଳ",
        "NOTIF_DOC_VERIFIED_BODY": "ଆପଣଙ୍କ ଦସ୍ତାବିଜ '{doc_type}' ସଫଳତାର ସହିତ ଯାଞ୍ଚ ହୋଇଛି।",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 ଆବେଦନ ସ୍ଥିତି ଅପଡେଟ୍",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' ଆବେଦନର ସ୍ଥିତି ବର୍ତ୍ତମାନ '{status}'।",
    },
    "as": {
        "ERR_UNAUTHORIZED": "প্ৰমাণীকৰণ প্ৰয়োজন। অনুগ্ৰহ কৰি লগইন কৰক।",
        "ERR_NOT_FOUND": "অনুৰোধ কৰা চৰকাৰী আঁচনি পোৱা নগ’ল।",
        "ERR_VALIDATION_FAILED": "পৰীক্ষণ ব্যৰ্থ হ’ল। প্ৰয়োজনীয় নথি পৰীক্ষা কৰক।",
        "ERR_NETWORK_ERROR": "নেটৱৰ্ক সংযোগ ব্যৰ্থ হ’ল।",
        "ERR_GATEWAY_UNAVAILABLE": "চৰকাৰী পৰ্টেল সাময়িকভাৱে ব্যস্ত।",
        "NOTIF_DEADLINE_7D_TITLE": "⏰ আঁচনিৰ সময়সীমা ওচৰ চাপিছে",
        "NOTIF_DEADLINE_7D_BODY": "আপোনাৰ সংৰক্ষিত আঁচনি '{scheme_name}'-ৰ সময়সীমা ৭ দিনত শেষ হ’ব।",
        "NOTIF_DEADLINE_3D_TITLE": "🚨 জৰুৰী: আঁচনিৰ বাবে মাত্ৰ ৩ দিন বাকী",
        "NOTIF_DEADLINE_3D_BODY": "'{scheme_name}'-ৰ বাবে আবেদন কৰিবলৈ মাত্ৰ ৩ দিন বাকী আছে।",
        "NOTIF_DEADLINE_1D_TITLE": "🔴 শেষ জাননী: আজি অন্তিম দিন",
        "NOTIF_DEADLINE_1D_BODY": "'{scheme_name}'-ৰ বাবে আবেদন দাখিল কৰাৰ আজি অন্তিম দিন।",
        "NOTIF_APP_SUBMITTED_TITLE": "📋 আবেদন দাখিল কৰা হ’ল",
        "NOTIF_APP_SUBMITTED_BODY": "'{scheme_name}'-ৰ বাবে আবেদন প্ৰসংগ নম্বৰ '{ref_code}' সহ পঞ্জীয়ন কৰা হ’ল।",
        "NOTIF_DOC_VERIFIED_TITLE": "✅ নথি পৰীক্ষা সম্পূৰ্ণ",
        "NOTIF_DOC_VERIFIED_BODY": "আপোনাৰ নথি '{doc_type}' সফলতাৰে পৰীক্ষা কৰা হৈছে।",
        "NOTIF_STATUS_UPDATED_TITLE": "🔄 আবেদনৰ স্থিতি আপডেট",
        "NOTIF_STATUS_UPDATED_BODY": "'{scheme_name}' আবেদনৰ স্থিতি এতিয়া '{status}'।",
    },
}


class LocalizationService:
    """Provides language negotiation, message localization, and scheme data integrity safeguards."""

    @staticmethod
    def is_supported(code: str) -> bool:
        return code.lower() in SUPPORTED_CODES

    @staticmethod
    def get_supported_languages() -> List[Dict[str, str]]:
        return SUPPORTED_LANGUAGES

    @classmethod
    def resolve_language(
        cls,
        accept_language: Optional[str] = None,
        query_param: Optional[str] = None,
        user_preference: Optional[str] = None
    ) -> str:
        """Resolve highest priority supported language code.
        Priority:
        1. query_param (e.g. ?lang=mr)
        2. user_preference (from profile or session)
        3. accept_language header (RFC 7231 parsing)
        4. DEFAULT_LANGUAGE ('hi')
        """
        if query_param and cls.is_supported(query_param):
            return query_param.lower()

        if user_preference and cls.is_supported(user_preference):
            return user_preference.lower()

        if accept_language:
            # Parse Accept-Language format like 'hi-IN,hi;q=0.9,en-US;q=0.8,en;q=0.7'
            tokens = accept_language.split(",")
            for token in tokens:
                lang_tag = token.split(";")[0].strip().split("-")[0].lower()
                if cls.is_supported(lang_tag):
                    return lang_tag

        return DEFAULT_LANGUAGE

    @classmethod
    def get_message(cls, message_key: str, lang: str = DEFAULT_LANGUAGE, **kwargs) -> str:
        """Fetch localized message with fallback to English then to key."""
        target_lang = lang if cls.is_supported(lang) else DEFAULT_LANGUAGE
        lang_dict = SYSTEM_MESSAGES.get(target_lang) or SYSTEM_MESSAGES.get("en", {})
        
        template = lang_dict.get(message_key)
        if not template:
            template = SYSTEM_MESSAGES.get("en", {}).get(message_key, message_key)

        try:
            return template.format(**kwargs)
        except Exception:
            return template

    @classmethod
    def format_notification(
        cls,
        notif_type: str,
        lang: str = DEFAULT_LANGUAGE,
        **kwargs
    ) -> Dict[str, str]:
        """Generate localized notification title and body.
        Guarantees that official scheme names and reference numbers passed in kwargs
        remain intact and are not translated or corrupted.
        """
        # Map notification type to message keys
        type_key_map = {
            "deadline_7d": ("NOTIF_DEADLINE_7D_TITLE", "NOTIF_DEADLINE_7D_BODY"),
            "deadline_3d": ("NOTIF_DEADLINE_3D_TITLE", "NOTIF_DEADLINE_3D_BODY"),
            "deadline_1d": ("NOTIF_DEADLINE_1D_TITLE", "NOTIF_DEADLINE_1D_BODY"),
            "application_submitted": ("NOTIF_APP_SUBMITTED_TITLE", "NOTIF_APP_SUBMITTED_BODY"),
            "document_verified": ("NOTIF_DOC_VERIFIED_TITLE", "NOTIF_DOC_VERIFIED_BODY"),
            "status_updated": ("NOTIF_STATUS_UPDATED_TITLE", "NOTIF_STATUS_UPDATED_BODY"),
        }

        keys = type_key_map.get(notif_type)
        if not keys:
            title = kwargs.get("title", "Government Scheme Notification")
            body = kwargs.get("body", "")
            return {"title": title, "body": body}

        title_key, body_key = keys
        title = cls.get_message(title_key, lang=lang, **kwargs)
        body = cls.get_message(body_key, lang=lang, **kwargs)
        return {"title": title, "body": body}

    @staticmethod
    def preserve_official_scheme_data(scheme: Any) -> Dict[str, Any]:
        """Ensure canonical statutory scheme data fields remain uncorrupted.
        Official legal names, ministry names, and official .gov.in URLs must never be
        mutated or machine-translated.
        """
        data = scheme if isinstance(scheme, dict) else {
            c.name: getattr(scheme, c.name, None) for c in getattr(scheme, "__table__", []).columns
        } if hasattr(scheme, "__table__") else getattr(scheme, "__dict__", {})

        # Retain canonical official name, ministry, and official_url
        canonical_name = data.get("name")
        canonical_ministry = data.get("ministry")
        canonical_url = data.get("official_url")

        return {
            "id": data.get("id"),
            "name": canonical_name,
            "ministry": canonical_ministry,
            "official_url": canonical_url,
            "scheme_type": data.get("scheme_type"),
            "is_canonical_preserved": True
        }


def get_localization_service() -> LocalizationService:
    return LocalizationService()
