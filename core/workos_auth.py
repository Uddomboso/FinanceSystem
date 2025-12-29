"""
WorkOS Authentication Module for PennyWise
Handles OAuth flow with browser-based login and token capture
"""

import os
import webbrowser
import threading
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any, Callable
from core.config import Config
from core.logger import logger

try:
    from PyQt5.QtCore import QThread, pyqtSignal
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    QThread = None
    pyqtSignal = None

# Try to import workos, handle gracefully if not installed
try:
    from workos import WorkOSClient
    WORKOS_AVAILABLE = True
except ImportError:
    WORKOS_AVAILABLE = False
    WorkOSClient = None


class WorkOSAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback - lightweight server for token capture"""
    
    def __init__(self, callback_func, *args, **kwargs):
        self.callback_func = callback_func
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET request from OAuth redirect - extract code or token"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # Handle authorization code (most common OAuth flow)
            if 'code' in query_params:
                code = query_params['code'][0]
                logger.info("Received authorization code from WorkOS")
                
                # Send success response FIRST (before callback to avoid blocking HTTP response)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                    <html>
                    <head>
                        <title>Login Successful</title>
                        <meta http-equiv="refresh" content="2;url=about:blank">
                    </head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1 style="color: #28a745;">Login Successful!</h1>
                        <p>You can close this window and return to the application.</p>
                        <p style="color: #6c757d; font-size: 12px;">This window will close automatically...</p>
                    </body>
                    </html>
                """)
                self.wfile.flush()  # Ensure response is sent immediately
                
                # Call the callback function AFTER sending response
                self.callback_func(code)
            
            # Handle direct token (if WorkOS provides it)
            elif 'token' in query_params:
                token = query_params['token'][0]
                logger.info("Received direct token from WorkOS")
                
                # Send response FIRST
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                    <html>
                    <head>
                        <title>Login Successful</title>
                        <meta http-equiv="refresh" content="2;url=about:blank">
                    </head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1 style="color: #28a745;">Login Successful!</h1>
                        <p>You can close this window and return to the application.</p>
                    </body>
                    </html>
                """)
                self.wfile.flush()
                
                # Call callback AFTER sending response
                self.callback_func(token, is_token=True)
            
            # Handle errors
            elif 'error' in query_params:
                error = query_params['error'][0]
                error_description = query_params.get('error_description', ['Unknown error'])[0]
                logger.error(f"WorkOS authentication error: {error} - {error_description}")
                
                # Send response FIRST
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f"""
                    <html>
                    <head><title>Login Failed</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1 style="color: #dc3545;">Login Failed</h1>
                        <p>{error_description}</p>
                        <p style="color: #6c757d; font-size: 12px;">Please try again.</p>
                    </body>
                    </html>
                """.encode())
                self.wfile.flush()
                
                # Call callback AFTER sending response
                self.callback_func(None, error=error, error_description=error_description)
            
            # Invalid request
            else:
                logger.warning(f"Invalid OAuth redirect - missing code/token: {self.path}")
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                    <html>
                    <head><title>Invalid Request</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1 style="color: #dc3545;">Invalid Request</h1>
                        <p>Missing authorization code or token.</p>
                    </body>
                    </html>
                """)
        
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            try:
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f"""
                    <html>
                    <head><title>Server Error</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1 style="color: #dc3545;">Server Error</h1>
                        <p>An error occurred processing your request.</p>
                    </body>
                    </html>
                """.encode())
            except:
                pass  # Connection may be closed
    
    def log_message(self, format, *args):
        """Suppress default logging - use logger instead"""
        pass


class WorkOSAuthenticator:
    """Handles WorkOS authentication flow"""
    
    def __init__(self):
        self.api_key = Config.WORKOS_API_KEY
        self.client_id = Config.WORKOS_CLIENT_ID
        self.redirect_url = Config.WORKOS_REDIRECT_URL
        
        if not WORKOS_AVAILABLE:
            logger.warning("WorkOS package not installed. Install with: pip install workos")
            self.workos = None
        elif not self.api_key or not self.client_id:
            logger.warning("WorkOS credentials not configured. WorkOS authentication will be disabled.")
            self.workos = None
        else:
            try:
                self.workos = WorkOSClient(api_key=self.api_key, client_id=self.client_id)
                logger.info("WorkOS client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize WorkOS client: {e}")
                self.workos = None
        
        self.server = None
        self.server_thread = None
        self.auth_code = None
        self.auth_error = None
        self.callback_received = False
        self.code_received_time = None
    
    def _exchange_code_in_thread(self, code):
        """Exchange authorization code for tokens in worker thread"""
        if QT_AVAILABLE and QThread:
            class TokenWorker(QThread):
                finished = pyqtSignal(object)
                error = pyqtSignal(str)
                
                def __init__(self, workos_client, code, redirect_uri):
                    super().__init__()
                    self.workos_client = workos_client
                    self.code = code
                    self.redirect_uri = redirect_uri
                
                def run(self):
                    try:
                        response = self.workos_client.user_management.authenticate_with_code(code=self.code)
                        # Set result directly instead of using signals (signals don't work in nested QThreads)
                        if hasattr(self, 'result_container'):
                            self.result_container['response'] = response
                            self.result_container['done'].set()
                        else:
                            # Fallback to signal if result_container not set
                            self.finished.emit(response)
                    except Exception as e:
                        # Set error directly instead of using signals
                        error_msg = f"{type(e).__name__}: {str(e)}"
                        if hasattr(e, 'status_code'):
                            error_msg += f" (status: {e.status_code})"
                        if hasattr(self, 'result_container'):
                            self.result_container['error'] = error_msg
                            self.result_container['done'].set()
                        else:
                            # Fallback to signal if result_container not set
                            self.error.emit(error_msg)
            
            result_container = {'response': None, 'error': None, 'done': threading.Event()}
            
            # Store result_container in worker so it can set result directly
            worker = TokenWorker(self.workos, code, self.redirect_url)
            worker.result_container = result_container  # Pass result container directly
            worker.start()
            
            # Process Qt events while waiting to ensure signals are delivered
            from PyQt5.QtWidgets import QApplication
            import time as time_module
            wait_start = time_module.time()
            while not result_container['done'].is_set() and (time_module.time() - wait_start) < 30:
                app = QApplication.instance()
                if app:
                    app.processEvents()
                result_container['done'].wait(timeout=0.1)
            wait_result = result_container['done'].is_set()
            
            if result_container['error']:
                raise Exception(result_container['error'])
            if not result_container['response']:
                raise Exception("Token exchange failed")
            
            return result_container['response']
        else:
            return self.workos.user_management.authenticate_with_code(code=code)
    
    def is_configured(self) -> bool:
        """Check if WorkOS is properly configured"""
        return self.workos is not None and bool(self.api_key and self.client_id)
    
    def get_authorization_url(self) -> Optional[str]:
        """Generate WorkOS authorization URL"""
        if not self.is_configured():
            return None
        
        try:
            auth_url = self.workos.user_management.get_authorization_url(
                redirect_uri=self.redirect_url,
                provider="GoogleOAuth"
            )
            return auth_url
        except Exception as e:
            logger.error(f"Error generating WorkOS authorization URL: {e}")
            return None
    
    def _start_callback_server(self, port: int = 8000, timeout: int = 300):
        """Start lightweight local HTTP server to capture OAuth callback"""
        def callback_handler(code: Optional[str] = None, error: Optional[str] = None, 
                           error_description: Optional[str] = None, is_token: bool = False):
            """Handle OAuth callback - extract code or token securely"""
            if code:
                if is_token:
                    # Direct token provided (less common)
                    self.auth_code = code
                    self.is_direct_token = True
                else:
                    # Authorization code (standard OAuth flow)
                    self.auth_code = code
                    self.is_direct_token = False
                    self.code_received_time = time.time()
            else:
                self.auth_error = error or "Unknown error"
                if error_description:
                    self.auth_error += f": {error_description}"
            self.callback_received = True
        
        def handler_factory(*args, **kwargs):
            return WorkOSAuthHandler(callback_handler, *args, **kwargs)
        
        try:
            # Parse port and path from redirect URL
            parsed = urllib.parse.urlparse(self.redirect_url)
            if parsed.port:
                port = parsed.port
            
            # Check if port is already in use
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                raise OSError(f"Port {port} is already in use. Please check if another instance is running.")
            
            self.server = HTTPServer(('localhost', port), handler_factory)
            self.server.timeout = timeout
            self.is_direct_token = False
            
            server_ready = threading.Event()
            server_listening = threading.Event()
            
            def run_server():
                """Run server in thread - handle requests until callback received"""
                try:
                    # Signal that server thread has started
                    server_ready.set()
                    
                    # Start listening immediately - call handle_request() to accept connections
                    # This ensures server is ready before browser opens
                    import socket
                    # Verify server socket is bound and listening
                    if hasattr(self.server, 'socket') and self.server.socket:
                        server_listening.set()
                    
                    max_requests = 10  # Limit requests to prevent infinite loop
                    request_count = 0
                    # Use short timeout so we can check callback_received frequently
                    original_timeout = self.server.timeout
                    self.server.timeout = 1.0  # 1 second timeout for handle_request()
                    while not self.callback_received and request_count < max_requests:
                        self.server.handle_request()
                        request_count += 1
                    # Restore original timeout
                    self.server.timeout = original_timeout
                except OSError as e:
                    if "Address already in use" in str(e):
                        logger.error(f"Port {port} is already in use")
                    else:
                        logger.error(f"Error in callback server: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error in callback server: {e}")
                finally:
                    if self.server:
                        try:
                            self.server.server_close()
                        except:
                            pass
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # Wait for server thread to start
            server_ready.wait(timeout=2.0)
            
            # Verify server is actually listening on the port before opening browser
            import socket
            max_wait = 2.0
            waited = 0
            while waited < max_wait:
                try:
                    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_sock.settimeout(0.1)
                    result = test_sock.connect_ex(('localhost', port))
                    test_sock.close()
                    if result == 0:
                        # Port is open and accepting connections
                        logger.info(f"Started OAuth callback server on http://localhost:{port}/authenticate")
                        break
                except Exception:
                    pass
                time.sleep(0.1)
                waited += 0.1
            else:
                # Server didn't start listening in time
                logger.warning(f"Server may not be listening on port {port}, but proceeding anyway")
            
        except OSError as e:
            logger.error(f"Failed to start callback server on port {port}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to start callback server: {e}")
            raise
    
    def _stop_callback_server(self):
        """Stop the callback server"""
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None
    
    def authenticate(self) -> Optional[Dict[str, Any]]:
        """
        Perform WorkOS authentication flow
        Returns user info dict with 'user_id', 'email', 'username', 'role', 'token' on success
        Returns None on failure
        """
        if not self.is_configured():
            logger.error("WorkOS is not configured")
            return None
        
        # Reset state
        self.auth_code = None
        self.auth_error = None
        self.callback_received = False
        
        # Get authorization URL
        auth_url = self.get_authorization_url()
        if not auth_url:
            logger.error("Failed to generate authorization URL")
            return None
        
        # Start callback server
        try:
            self._start_callback_server()
        except Exception as e:
            logger.error(f"Failed to start callback server: {e}")
            return None
        
        # Open browser
        try:
            logger.info(f"Opening browser for WorkOS authentication: {auth_url}")
            webbrowser.open(auth_url)
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            self._stop_callback_server()
            return None
        
        # Wait for callback (with timeout) - allow Qt events to process
        timeout = 300  # 5 minutes
        start_time = time.time()
        while not self.callback_received:
            if time.time() - start_time > timeout:
                logger.error("Authentication timeout")
                self._stop_callback_server()
                return None
            # Process Qt events if available, otherwise sleep
            try:
                from PyQt5.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    app.processEvents()
            except:
                pass
            time.sleep(0.1)
        
        # Stop server (non-blocking - server thread will exit naturally)
        # Don't block on server shutdown - server thread will exit when callback_received is True
        # Just mark server for cleanup (daemon thread will exit automatically)
        if self.server:
            # Set a flag to stop the server thread loop (already set via callback_received)
            # The server thread will exit naturally, so we don't need to wait
            pass
        
        # Check for errors
        if self.auth_error:
            logger.error(f"Authentication error: {self.auth_error}")
            return None
        
        if not self.auth_code:
            logger.error("No authorization code received")
            return None
        
        # Exchange code for token and user info via WorkOS API
        try:
            if self.is_direct_token:
                # Direct token provided (rare case)
                token = self.auth_code
                logger.warning("Direct token provided - may need to fetch profile separately")
                # Try to get profile with token
                # Note: WorkOS SDK may not support this directly
                # For now, we'll need to use the token to make API calls
                # This is a simplified implementation
                user_info = {
                    'token': token,
                    'email': '',  # Will be filled from database lookup
                    'username': '',
                    'role': 'End User'
                }
            else:
                logger.info("Starting token exchange in worker thread...")
                auth_response = self._exchange_code_in_thread(self.auth_code)
                logger.info("Token exchange completed successfully")
                
                user = getattr(auth_response, 'user', None)
                access_token = getattr(auth_response, 'access_token', None)
                refresh_token = getattr(auth_response, 'refresh_token', None)
                id_token = getattr(auth_response, 'id_token', None)
                
                if user:
                    email = getattr(user, 'email', '') or ''
                    first_name = getattr(user, 'first_name', '') or ''
                    last_name = getattr(user, 'last_name', '') or ''
                    user_id = getattr(user, 'id', '') or ''
                    picture = getattr(user, 'picture', None) or getattr(user, 'profile_picture_url', None) or ''
                else:
                    email = ''
                    first_name = ''
                    last_name = ''
                    user_id = ''
                    picture = ''
                
                username = first_name or email.split('@')[0] if email else 'user'
                
                user_info = {
                    'user_id': user_id,
                    'email': email,
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'picture': picture,
                    'access_token': access_token,
                    'id_token': id_token,
                    'refresh_token': refresh_token,
                    'token': access_token,
                    'raw_profile': {
                        'id': user_id,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'picture': picture,
                    }
                }
                
                user_info['role'] = "End User"
                logger.info(f"WorkOS authentication successful for {email}")
            
            return user_info
            
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from WorkOS token"""
        if not self.is_configured():
            return None
        
        try:
            # WorkOS SDK doesn't have a direct "get user from token" method
            # We'll need to use the token to make API calls
            # For now, return None - user info should be stored during authentication
            logger.warning("get_user_info not fully implemented - use stored session data")
            return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None


# Global authenticator instance
_authenticator = None

def get_workos_authenticator() -> WorkOSAuthenticator:
    """Get the global WorkOS authenticator instance"""
    global _authenticator
    if _authenticator is None:
        _authenticator = WorkOSAuthenticator()
    return _authenticator
