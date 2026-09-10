/**
 * Business Classification & Lifecycle Stage Canonical Mappings
 * Maps user-friendly UI labels to backend enum/regex constraints and vice-versa.
 * 
 * Backend constraints:
 * - business_type: manufacturing | service | trading | agriculture | food_processing | technology | handicraft | retail | other
 * - business_stage: idea | pre_revenue | revenue | growth | mature
 */

export const BUSINESS_TYPES = [
  { value: 'manufacturing', label: 'Manufacturing & Processing', desc: 'Production, assembly, factories, machinery' },
  { value: 'service', label: 'Services & Consultancy', desc: 'Professional, commercial, technical services' },
  { value: 'trading', label: 'Trading & Wholesale', desc: 'B2B distribution, wholesale trading' },
  { value: 'retail', label: 'Retail & Store Operations', desc: 'Kirana, retail stores, direct consumer shops' },
  { value: 'agriculture', label: 'Agri-Business & Dairy', desc: 'Farming, dairy, poultry, horticulture, allied' },
  { value: 'food_processing', label: 'Food Processing & Agro', desc: 'Packaged foods, grain milling, food units' },
  { value: 'technology', label: 'IT & Digital Solutions', desc: 'Software, IT services, tech development' },
  { value: 'handicraft', label: 'Handicrafts & Handlooms', desc: 'Artisans, weavers, traditional craft makers' },
  { value: 'other', label: 'Other Enterprise Type', desc: 'General enterprise or emerging sectors' },
];

export const BUSINESS_STAGES = [
  { value: 'idea', label: 'Idea Stage', desc: 'Concept, business planning & prototyping' },
  { value: 'pre_revenue', label: 'Starting Up (Pre-Revenue)', desc: 'Setup in progress, prototype ready (0-12 mos)' },
  { value: 'revenue', label: 'Operating (Generating Revenue)', desc: 'Active sales, stable operational workflow' },
  { value: 'growth', label: 'Growing & Scaling', desc: 'Expanding markets, scaling production & team' },
  { value: 'mature', label: 'Established & Mature', desc: 'Established market leader, sustainable enterprise' },
];

export const REGISTRATION_TYPES = [
  { value: 'individual', label: 'Individual / Sole Proprietor', desc: 'Solo artisan or unregistered enterprise' },
  { value: 'startup', label: 'Startup (DPIIT Recognized)', desc: 'Tech venture or innovation enterprise' },
  { value: 'msme', label: 'MSME (UDYAM Registered)', desc: 'Registered Micro, Small or Medium unit' },
  { value: 'self_employed', label: 'Self Employed / Freelancer', desc: 'Independent consultant or service provider' },
  { value: 'partnership', label: 'Partnership / LLP', desc: 'Registered partnership or limited liability firm' },
  { value: 'pvt_ltd', label: 'Private Limited Company', desc: 'Incorporated private corporate entity' },
];

/**
 * Normalizes any legacy or variant business_type string to a valid canonical backend value.
 */
export function normalizeBusinessType(val) {
  if (!val) return 'manufacturing';
  const clean = String(val).trim().toLowerCase().replace(/[-\s]+/g, '_');
  
  const map = {
    manufacturing: 'manufacturing',
    service: 'service',
    services: 'service',
    trading: 'trading',
    retail: 'retail',
    trade: 'trading',
    agriculture: 'agriculture',
    farming: 'agriculture',
    dairy: 'agriculture',
    agri: 'agriculture',
    food_processing: 'food_processing',
    foodprocessing: 'food_processing',
    food: 'food_processing',
    technology: 'technology',
    tech: 'technology',
    it: 'technology',
    handicraft: 'handicraft',
    handicrafts: 'handicraft',
    handloom: 'handicraft',
    handlooms: 'handicraft',
    other: 'other',
    // Fallbacks for legacy structure values if accidentally saved in business_type
    individual: 'other',
    startup: 'technology',
    msme: 'manufacturing',
    self_employed: 'service',
  };

  return map[clean] || 'other';
}

/**
 * Normalizes any legacy or variant business_stage string to a valid canonical backend value.
 */
export function normalizeBusinessStage(val) {
  if (!val) return 'revenue';
  const clean = String(val).trim().toLowerCase().replace(/[-\s]+/g, '_');

  const map = {
    idea: 'idea',
    concept: 'idea',
    planning: 'idea',
    starting: 'pre_revenue',
    starting_up: 'pre_revenue',
    pre_revenue: 'pre_revenue',
    prerevenue: 'pre_revenue',
    early: 'pre_revenue',
    operating: 'revenue',
    revenue: 'revenue',
    running: 'revenue',
    operational: 'revenue',
    expanding: 'growth',
    growth: 'growth',
    scaling: 'growth',
    mature: 'mature',
    established: 'mature',
  };

  return map[clean] || 'revenue';
}

/**
 * Normalizes registration type.
 */
export function normalizeRegistrationType(val) {
  if (!val) return 'individual';
  const clean = String(val).trim().toLowerCase().replace(/[-\s]+/g, '_');
  const valid = ['individual', 'startup', 'msme', 'self_employed', 'partnership', 'pvt_ltd'];
  return valid.includes(clean) ? clean : 'individual';
}

/**
 * Gets human-friendly display label for business type.
 */
export function getBusinessTypeLabel(val) {
  const norm = normalizeBusinessType(val);
  const found = BUSINESS_TYPES.find(t => t.value === norm);
  return found ? found.label : (norm ? norm.replace('_', ' ').toUpperCase() : '—');
}

/**
 * Gets human-friendly display label for business stage.
 */
export function getBusinessStageLabel(val) {
  const norm = normalizeBusinessStage(val);
  const found = BUSINESS_STAGES.find(s => s.value === norm);
  return found ? found.label : (norm ? norm.replace('_', ' ').toUpperCase() : '—');
}

/**
 * Gets human-friendly display label for registration type.
 */
export function getRegistrationTypeLabel(val) {
  const norm = normalizeRegistrationType(val);
  const found = REGISTRATION_TYPES.find(r => r.value === norm);
  return found ? found.label : (norm ? norm.replace('_', ' ').toUpperCase() : '—');
}
