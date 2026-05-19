// ✅ Add CSRF token interceptor to apiV1 (disabled - backend is CSRF-exempt for API endpoints)
apiV1.interceptors.request.use(
  config => {
    // CSRF token disabled for REST API endpoints - backend uses @csrf_exempt
    // If CSRF is re-enabled in future, uncomment code below:
    // if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    //   const csrfToken = getCsrfToken();
    //   if (csrfToken) {
    //     config.headers['X-CSRFToken'] = csrfToken;
    //     console.log('🔐 [API V1] Added CSRF token to request headers');
    //   } else {
    //     console.warn('⚠️ [API V1] No CSRF token found - request may be rejected');
    //   }
    // }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 🚨 ADD THIS RETRY INTERCEPTOR BLOCK HERE 🚨
// Retry interceptor for network resilience (MATCHES regular api instance)
apiV1.interceptors.response.use(
  response => response,
  async error => {
    const config = error.config;

    // Skip retry if not configured
    if (!config || !config.retryCount) {
      config.retryCount = 0;
    }

    // Check if should retry
    const isRetryable = 
      RETRY_CONFIG.retryableStatusCodes.includes(error.response?.status) ||
      error.code === 'ECONNABORTED' ||
      error.code === 'ECONNREFUSED' ||
      error.code === 'ETIMEDOUT' ||
      !error.response; // Network error

    if (isRetryable && config.retryCount < RETRY_CONFIG.maxRetries) {
      config.retryCount += 1;
      
      // Calculate exponential backoff
      const delay = RETRY_CONFIG.retryDelay * Math.pow(RETRY_CONFIG.backoffMultiplier, config.retryCount - 1);
      
      console.warn(
        `⚠️ [API V1] Request failed (attempt ${config.retryCount}/${RETRY_CONFIG.maxRetries}). ` +
        `Retrying in ${delay}ms... [${error.message}]`
      );

      await new Promise(resolve => setTimeout(resolve, delay));
      return apiV1(config); // CRITICAL: Must use apiV1 here
    }

    return Promise.reject(error);
  }
);
// 🚨 END OF RETRY INTERCEPTOR BLOCK 🚨
