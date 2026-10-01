// ====================================================================
// SMART CKD HEALTHCARE PLATFORM - CLIENT ENVIRONMENT CONFIGURATION
// ====================================================================
/**
 * Global Configuration for CKD SmartCare Frontend.
 * 
 * In local development (served by FastAPI):
 *   window.BACKEND_API_URL can remain "" (empty string) so all requests 
 *   use relative path: "/api/..."
 * 
 * In production deployment (e.g., Firebase Hosting frontend + Google Cloud Run backend):
 *   Set window.BACKEND_API_URL to your deployed Cloud Run URL:
 *   window.BACKEND_API_URL = "https://ckd-backend-xxxxx.a.run.app";
 */

window.BACKEND_API_URL = window.BACKEND_API_URL || "";
window.API_BASE = window.BACKEND_API_URL 
  ? `${window.BACKEND_API_URL.replace(/\/$/, '')}/api` 
  : "/api";
