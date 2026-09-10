import apiClient from './api';

export const integrationService = {
  getIntegrationStatuses: async () => {
    const response = await apiClient.get('/integrations/status');
    return response.data;
  },

  getDigiLockerAuthUrl: async () => {
    const response = await apiClient.get('/integrations/digilocker/auth-url');
    return response.data;
  },

  verifyAadhaarLastFour: async (aadhaarLastFour, consentGiven = true) => {
    const response = await apiClient.post('/integrations/aadhaar/verify-last-four', {
      aadhaar_last_four: aadhaarLastFour,
      consent_given: consentGiven,
    });
    return response.data;
  },

  verifyPAN: async (panNumber, consentGiven = true) => {
    const response = await apiClient.post('/integrations/pan/verify', {
      pan_number: panNumber,
      consent_given: consentGiven,
    });
    return response.data;
  },

  verifyUdyam: async (udyamNumber, consentGiven = true) => {
    const response = await apiClient.post('/integrations/udyam/verify', {
      udyam_number: udyamNumber,
      consent_given: consentGiven,
    });
    return response.data;
  },

  syncApplicationStatus: async (applicationId) => {
    const response = await apiClient.get(`/integrations/applications/${applicationId}/sync`);
    return response.data;
  },

  syncGovernmentSchemes: async () => {
    const response = await apiClient.post('/integrations/schemes/sync');
    return response.data;
  },

  getCBSPartnerMetrics: async (partnerId, branchCode = null) => {
    const params = branchCode ? { branch_code: branchCode } : {};
    const response = await apiClient.get(`/integrations/banking/partner/${partnerId}/metrics`, { params });
    return response.data;
  },

  getNPAFundUtilization: async (partnerId) => {
    const response = await apiClient.get(`/integrations/banking/partner/${partnerId}/npa-utilization`);
    return response.data;
  },

  getPartnerLendingCapacity: async (partnerId) => {
    const response = await apiClient.get(`/integrations/banking/partner/${partnerId}/lending-capacity`);
    return response.data;
  },

  queryPFMSDisbursementStatus: async (queryPayload) => {
    const response = await apiClient.post('/integrations/pfms/dbt-status', queryPayload);
    return response.data;
  },
};

export default integrationService;
