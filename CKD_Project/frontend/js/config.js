// ====================================================================
// SMART CKD HEALTHCARE PLATFORM - CLIENT ENVIRONMENT CONFIGURATION
// ====================================================================
/**
 * Global Configuration for CKD SmartCare Frontend.
 * 
 * Standalone Backend Server (FastAPI + Uvicorn):
 *   All frontend portals (Patient, Doctor, Staff, Admin) are served directly 
 *   by the FastAPI backend application on http://localhost:8000.
 *   window.BACKEND_API_URL defaults to "" so all requests use relative path: "/api/..."
 */

window.BACKEND_API_URL = window.BACKEND_API_URL || "";
window.API_BASE = window.BACKEND_API_URL 
  ? `${window.BACKEND_API_URL.replace(/\/$/, '')}/api` 
  : "/api";
