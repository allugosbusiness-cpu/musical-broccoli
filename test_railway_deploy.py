"""
Minimal test app to verify Railway can run Python at all
"""
def application(environ, start_response):
    """WSGI application for testing"""
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b'Railway is working! This is a minimal WSGI app.']
