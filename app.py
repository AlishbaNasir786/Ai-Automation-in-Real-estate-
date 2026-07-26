import os
import subprocess
from flask import Flask, jsonify, send_from_directory, Response

from routes.properties import properties_bp
from routes.persona import persona_bp

app = Flask(__name__, static_folder='.', static_url_path='')

app.register_blueprint(properties_bp)
app.register_blueprint(persona_bp)
@app.route('/')
def index():
    return send_from_directory('.', 'property.html')
@app.route('/competitor')
def competitor():
    return send_from_directory('.', 'competitor.html')
@app.route('/api/run_competitor_engine', methods=['GET', 'POST'])
def run_engine():
    import queue, threading

    script_path = os.path.abspath(os.path.join('modules', 'competitor_engine.py'))
    cwd_path    = os.path.abspath('modules')

    def generate():
        # Immediate heartbeat so browser knows the connection is open
        yield "data: 0% — Scraper starting…\n\n"

        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'

        process = subprocess.Popen(
            ['python', '-u', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            cwd=cwd_path,
            env=env,
        )

        q = queue.Queue()

        def reader():
            """Background thread: push every raw line into the queue."""
            for raw in iter(process.stdout.readline, b''):
                q.put(raw)
            process.stdout.close()
            q.put(None)   # sentinel

        t = threading.Thread(target=reader, daemon=True)
        t.start()

        while True:
            try:
                raw = q.get(timeout=2.0)   # wait up to 2 s for a line
            except queue.Empty:
                # No output yet but process still running → keepalive
                if process.poll() is not None:
                    break
                yield ": keepalive\n\n"
                continue

            if raw is None:   # sentinel — reader thread is done
                break

            text = raw.decode('utf-8', errors='replace').rstrip('\r\n')
            if text:
                yield f"data: {text}\n\n"

        process.wait()
        if process.returncode == 0:
            yield "data: [DONE]\n\n"
        else:
            yield "data: [ERROR]\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
